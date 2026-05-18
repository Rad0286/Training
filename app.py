"""
app.py
Streamlit UI for the Case Reference Extractor & Highlighter.
"""

import os
import json
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load existing .env
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

# ── Defaults (can be overridden in UI) ────────────────────────────────────────
DEFAULT_INPUT_DIR  = r"C:\Users\0119944\Downloads\Cases Reflist\Input"
DEFAULT_OUTPUT_DIR = r"C:\Users\0119944\Downloads\Cases Reflist\Output"

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
    current_token = os.getenv("TR_ESSO_TOKEN", "")
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
            set_key(ENV_PATH, "TR_ESSO_TOKEN", token_val)
            os.environ["TR_ESSO_TOKEN"] = token_val
            st.success(f"✅ Token saved! ({len(token_val)} chars)")
            st.rerun()
        else:
            st.warning("Please paste a token first.")

    st.divider()

    # ── Directory Settings ─────────────────────────────────────────────────────
    st.header("📁 Directory Settings")

    input_dir = st.text_input(
        "Input Directory",
        value=st.session_state.get("input_dir", DEFAULT_INPUT_DIR),
        help="Folder containing your PDF files and Reflist_Prompt.txt"
    )
    st.session_state["input_dir"] = input_dir

    output_dir = st.text_input(
        "Output Directory",
        value=st.session_state.get("output_dir", DEFAULT_OUTPUT_DIR),
        help="Folder where highlighted PDFs will be saved"
    )
    st.session_state["output_dir"] = output_dir

    # Validate directories
    input_valid = os.path.isdir(input_dir)
    output_valid = True  # Will be created if it doesn't exist

    if input_dir and not input_valid:
        st.error(f"⚠️ Input directory not found")
    else:
        st.success(f"✅ Input path OK")

    instructions_file = os.path.join(input_dir, "Reflist_Prompt.txt")
    if input_valid and not os.path.isfile(instructions_file):
        st.warning("⚠️ `Reflist_Prompt.txt` not found in input folder")

    st.caption(f"Output will be created at:\n`{output_dir}`")

# ── Main area ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 PDF Files in Input Folder")

    pdf_files = []
    if os.path.isdir(input_dir):
        pdf_files = sorted(Path(input_dir).glob("*.pdf"))

    if not pdf_files:
        st.warning(f"No PDF files found in:\n`{input_dir}`")
        selected_pdfs = []
    else:
        selected_pdfs = []
        st.markdown(f"Found **{len(pdf_files)}** PDF(s):")
        select_all = st.checkbox("☑️ Select All", value=True)

        for pdf in pdf_files:
            checked = st.checkbox(pdf.name, value=select_all, key=f"chk_{pdf.name}")
            if checked:
                selected_pdfs.append(pdf)

with col2:
    st.subheader("⚙️ Run")

    token_ok = bool(os.environ.get("TR_ESSO_TOKEN", "").strip())
    instructions_ok = os.path.isfile(instructions_file) if os.path.isdir(input_dir) else False

    if not token_ok:
        st.error("⚠️ No authorization token — set it in the sidebar.")
    if not instructions_ok and os.path.isdir(input_dir):
        st.warning("⚠️ `Reflist_Prompt.txt` missing from input folder.")
    if selected_pdfs:
        st.info(f"**{len(selected_pdfs)}** PDF(s) selected for processing.")

    run_button = st.button(
        "🚀 Run Extraction & Highlighting",
        disabled=(not token_ok or not pdf_files or not selected_pdfs or not instructions_ok),
        use_container_width=True,
        type="primary"
    )

# ── Run processing ─────────────────────────────────────────────────────────────
if run_button and selected_pdfs:
    os.makedirs(output_dir, exist_ok=True)

    from llm_extractor import extract_references
    from pdf_highlighter import highlight_pdf

    st.divider()
    st.subheader("📊 Processing Results")

    summary = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, pdf_path in enumerate(selected_pdfs):
        progress_bar.progress(i / len(selected_pdfs))
        status_text.info(f"Processing {i+1}/{len(selected_pdfs)}: **{pdf_path.name}**")

        with st.expander(f"📄 {pdf_path.name}", expanded=True):
            try:
                st.write("🔍 Extracting text and calling Claude AI...")
                references = extract_references(str(pdf_path), instructions_file)

                if not references:
                    st.warning("No case references found.")
                    summary.append({"file": pdf_path.name, "status": "no references", "refs": 0})
                    continue

                st.success(f"✅ Claude found **{len(references)}** reference(s):")
                for ref in references:
                    st.markdown(f"- {ref}")

                st.write("🖊️ Highlighting references in PDF...")
                output_path, results = highlight_pdf(str(pdf_path), references, output_dir)

                highlighted = sum(1 for v in results.values() if v > 0)
                not_found = sum(1 for v in results.values() if v == 0)

                st.success(f"✅ Highlighted **{highlighted}** / {len(references)} references")
                if not_found > 0:
                    st.info(f"ℹ️ {not_found} reference(s) not found in PDF text (may span lines)")

                with open(output_path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Download {os.path.basename(output_path)}",
                        data=f.read(),
                        file_name=os.path.basename(output_path),
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"run_dl_{pdf_path.name}"
                    )

                summary.append({
                    "file": pdf_path.name,
                    "status": "success",
                    "refs": len(references),
                    "highlighted": highlighted,
                    "output": os.path.basename(output_path)
                })

            except Exception as e:
                st.error(f"❌ Error: {e}")
                summary.append({"file": pdf_path.name, "status": f"error: {e}", "refs": 0})

    progress_bar.progress(1.0)
    status_text.success("✅ All files processed!")

    summary_path = os.path.join(output_dir, "processing_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    st.divider()
    st.subheader("📋 Summary")
    for item in summary:
        if item["status"] == "success":
            st.markdown(f"✅ **{item['file']}** — {item['refs']} refs found, {item['highlighted']} highlighted → `{item['output']}`")
        elif item["status"] == "no references":
            st.markdown(f"➖ **{item['file']}** — No references found")
        else:
            st.markdown(f"❌ **{item['file']}** — {item['status']}")

# ── Output folder viewer ───────────────────────────────────────────────────────
st.divider()
st.subheader("📂 Output Folder")

if st.button("🔄 Refresh Output List"):
    st.rerun()

output_files = sorted(Path(output_dir).glob("*.pdf")) if os.path.isdir(output_dir) else []
if not output_files:
    st.info(f"No highlighted PDFs yet in `{output_dir}`.")
else:
    st.markdown(f"**{len(output_files)}** highlighted PDF(s) available:")
    for out_file in output_files:
        size_kb = out_file.stat().st_size // 1024
        with open(out_file, "rb") as f:
            st.download_button(
                label=f"⬇️ {out_file.name} ({size_kb} KB)",
                data=f.read(),
                file_name=out_file.name,
                mime="application/pdf",
                key=f"dl_{out_file.name}"
            )