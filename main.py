"""
main.py
Orchestrator: processes all PDFs in the input folder.
- Reads instructions from Reflist_Prompt.txt
- Sends each PDF to Claude for reference extraction
- Highlights the references in each PDF
- Saves highlighted PDFs to the output folder
"""

import os
import sys
import json
import io
from pathlib import Path
from llm_extractor import extract_references
from pdf_highlighter import highlight_pdf

# Force unbuffered output so log files capture in real time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

# ── Path configuration ─────────────────────────────────────────────────────────
INPUT_DIR  = r"C:\Users\0119944\Downloads\Cases Reflist\Input"
OUTPUT_DIR = r"C:\Users\0119944\Downloads\Cases Reflist\Output"
INSTRUCTIONS_FILE = os.path.join(INPUT_DIR, "Reflist_Prompt.txt")


def run():
    print("=" * 65)
    print("  Case Reference Extractor & Highlighter")
    print("=" * 65)

    # Validate paths
    if not os.path.isdir(INPUT_DIR):
        print(f"[ERROR] Input directory not found: {INPUT_DIR}")
        sys.exit(1)

    if not os.path.isfile(INSTRUCTIONS_FILE):
        print(f"[ERROR] Instructions file not found: {INSTRUCTIONS_FILE}")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Collect all PDF files in input directory
    pdf_files = sorted(Path(INPUT_DIR).glob("*.pdf"))

    if not pdf_files:
        print(f"[WARNING] No PDF files found in: {INPUT_DIR}")
        sys.exit(0)

    print(f"\nFound {len(pdf_files)} PDF(s) to process.")
    print(f"Instructions: {INSTRUCTIONS_FILE}")
    print(f"Output dir  : {OUTPUT_DIR}\n")

    summary = []

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
        print("-" * 55)

        try:
            # Step 1: Extract references via Claude
            references = extract_references(str(pdf_path), INSTRUCTIONS_FILE)

            if not references:
                print("  No case references found by Claude. Skipping highlight step.")
                summary.append({
                    "file": pdf_path.name,
                    "references_found": 0,
                    "output": None,
                    "status": "no references"
                })
                print()
                continue

            # Print the reference list
            print(f"\n  Reference list extracted by Claude:")
            for ref in references:
                print(f"    • {ref}")
            print()

            # Step 2: Highlight in PDF
            output_path, results = highlight_pdf(str(pdf_path), references, OUTPUT_DIR)

            highlighted_count = sum(1 for v in results.values() if v > 0)
            summary.append({
                "file": pdf_path.name,
                "references_found": len(references),
                "highlighted_in_pdf": highlighted_count,
                "output": os.path.basename(output_path),
                "status": "success"
            })

        except Exception as e:
            print(f"  [ERROR] Failed to process {pdf_path.name}: {e}")
            summary.append({
                "file": pdf_path.name,
                "status": f"error: {e}"
            })

        print()

    # ── Final summary ───────────────────────────────────────────────────────────
    print("=" * 65)
    print("  SUMMARY")
    print("=" * 65)
    for item in summary:
        status = item.get("status", "unknown")
        if status == "success":
            print(f"  ✓ {item['file']}")
            print(f"      References found  : {item['references_found']}")
            print(f"      Highlighted in PDF: {item['highlighted_in_pdf']}")
            print(f"      Output file       : {item['output']}")
        elif status == "no references":
            print(f"  – {item['file']}  (no references found)")
        else:
            print(f"  ✗ {item['file']}  ({status})")

    # Save summary JSON next to outputs
    summary_path = os.path.join(OUTPUT_DIR, "processing_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n  Full summary saved to: {summary_path}")
    print("=" * 65)


if __name__ == "__main__":
    run()