"""
app.py
Streamlit UI for the Case Reference Extractor & Highlighter.
Cloud-compatible: uses file upload instead of local directory paths.
"""

import os
import io
import json
import tempfile
import streamlit as st
from dotenv import load_dotenv, set_key

# Load existing .env (works locally; on Streamlit Cloud use st.secrets)
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Case Reference Extractor",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Case Reference Extractor & Highlighter")
st.markdown("Extracts case references from legal PDFs using Claude AI and highlights them in the output PDF.")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Authorization ──────────────────────────────────────────────────────────
    st.header("🔑 Authorization")

    # Support both .env (local) and st.secrets (Streamlit Cloud)
    try:
        current_token = st.secrets.get("TR_ESSO_TOKEN", "") if "TR_ESSO_TOKEN" in st.secrets else os.getenv("TR_ESSO_TOKEN", "")
    except (FileNotFoundError, Exception):
        current_token = os.getenv("TR_ESSO_TOKEN", "")
    current_token = current_token.strip()

    token_display = current_token[:40] + "..." if len(current_token) > 40 else current_token
    if current_token:
        st.success(f"Token set ({len(current_token)} chars): `{token_display}`")
    else:
        st.error("No token set")

    new_token = st.text_area(
        "Paste new ESSO Bearer Token",
        placeholder="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpX...",
        height=120,
        help="Paste your full ESSO JWT token here. It starts with 'eyJ...'"
    )

    if st.button("💾 Save Token", use_container_width=True):
        token_val = new_token.strip()
        if token_val:
            os.environ["TR_ESSO_TOKEN"] = token_val
            # Save to .env if running locally
            try:
                set_key(ENV_PATH, "TR_ESSO_TOKEN", token_val)
            except Exception:
                pass
            current_token = token_val
            st.success(f"✅ Token saved for this session! ({len(token_val)} chars)")
            st.rerun()
        else:
            st.warning("Please paste a token first.")

    st.divider()
    st.markdown("""
    **How to use:**
    1. Paste your ESSO token above and click Save
    2. Upload one or more PDF files
    3. Click **Run** to extract and highlight references
    4. Download the highlighted PDFs
    """)

# ── Resolve token (session state takes priority) ───────────────────────────────
token_ok = bool(os.environ.get("TR_ESSO_TOKEN", current_token).strip())
if current_token and not os.environ.get("TR_ESSO_TOKEN"):
    os.environ["TR_ESSO_TOKEN"] = current_token

# ── Main area ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 PDF Files")
    uploaded_pdfs = st.file_uploader(
        "Upload PDF file(s)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more legal judgment PDFs to process"
    )
    if uploaded_pdfs:
        st.success(f"✅ **{len(uploaded_pdfs)}** PDF(s) ready:")
        for f in uploaded_pdfs:
            st.markdown(f"- `{f.name}` ({f.size // 1024} KB)")

with col2:
    st.subheader("⚙️ Run")

    if not token_ok:
        st.error("⚠️ No authorization token — set it in the sidebar.")
    if not uploaded_pdfs:
        st.warning("⚠️ Please upload at least one PDF.")

    can_run = token_ok and uploaded_pdfs
    if can_run:
        st.info(f"Ready to process **{len(uploaded_pdfs)}** PDF(s).")

    run_button = st.button(
        "🚀 Run Extraction & Highlighting",
        disabled=not can_run,
        use_container_width=True,
        type="primary"
    )

# ── Run processing ─────────────────────────────────────────────────────────────
if run_button and can_run:
    from llm_extractor import extract_references
    from pdf_highlighter import highlight_pdf

    st.divider()
    st.subheader("📊 Processing Results")

    summary = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, pdf_file in enumerate(uploaded_pdfs):
        progress_bar.progress(i / len(uploaded_pdfs))
        status_text.info(f"Processing {i+1}/{len(uploaded_pdfs)}: **{pdf_file.name}**")

        with st.expander(f"📄 {pdf_file.name}", expanded=True):
            try:
                # Write uploaded files to a temp directory for processing
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Save PDF to temp
                    pdf_path = os.path.join(tmp_dir, pdf_file.name)
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_file.read())

                    output_dir = os.path.join(tmp_dir, "output")
                    os.makedirs(output_dir, exist_ok=True)

                    st.write("🔍 Extracting text and calling Claude AI...")
                    references = extract_references(pdf_path)

                    if not references:
                        st.warning("No case references found.")
                        summary.append({"file": pdf_file.name, "status": "no references", "refs": 0})
                        continue

                    st.success(f"✅ Claude found **{len(references)}** reference(s):")
                    for ref in references:
                        st.markdown(f"- {ref}")

                    st.write("🖊️ Highlighting references in PDF...")
                    output_path, results = highlight_pdf(pdf_path, references, output_dir)

                    highlighted = sum(1 for v in results.values() if v > 0)
                    not_found = sum(1 for v in results.values() if v == 0)

                    st.success(f"✅ Highlighted **{highlighted}** / {len(references)} references")
                    if not_found > 0:
                        st.info(f"ℹ️ {not_found} reference(s) not found in PDF text (may span lines)")

                    # Read the output file into memory before temp dir is deleted
                    with open(output_path, "rb") as f:
                        output_bytes = f.read()

                out_filename = os.path.splitext(pdf_file.name)[0] + "_highlighted.pdf"
                st.download_button(
                    label=f"⬇️ Download {out_filename}",
                    data=output_bytes,
                    file_name=out_filename,
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"dl_{pdf_file.name}"
                )

                summary.append({
                    "file": pdf_file.name,
                    "status": "success",
                    "refs": len(references),
                    "highlighted": highlighted,
                    "output": out_filename
                })

            except Exception as e:
                st.error(f"❌ Error: {e}")
                summary.append({"file": pdf_file.name, "status": f"error: {e}", "refs": 0})

    progress_bar.progress(1.0)
    status_text.success("✅ All files processed!")

    st.divider()
    st.subheader("📋 Summary")
    for item in summary:
        if item["status"] == "success":
            st.markdown(f"✅ **{item['file']}** — {item['refs']} refs found, {item['highlighted']} highlighted → `{item['output']}`")
        elif item["status"] == "no references":
            st.markdown(f"➖ **{item['file']}** — No references found")
        else:
            st.markdown(f"❌ **{item['file']}** — {item['status']}")

    # Offer summary JSON download
    summary_json = json.dumps(summary, indent=2, ensure_ascii=False)
    st.download_button(
        label="⬇️ Download Processing Summary (JSON)",
        data=summary_json,
        file_name="processing_summary.json",
        mime="application/json"
    )