"""
pdf_highlighter.py
Highlights case references found by Claude in the original PDF.
Uses PyMuPDF (fitz) for text search and annotation.
"""

import os
import fitz  # PyMuPDF


# Highlight color: yellow (RGB 1, 1, 0)
HIGHLIGHT_COLOR = (1, 1, 0)


def normalize(text: str) -> str:
    """Normalize whitespace for comparison."""
    return " ".join(text.split()).lower()


def find_and_highlight(pdf_path: str, references: list[str], output_path: str) -> dict:
    """
    Open the PDF, search for each reference, highlight all occurrences,
    and save to output_path.

    Returns a dict: {reference: count_of_highlights}
    """
    doc = fitz.open(pdf_path)
    results = {}

    for ref in references:
        ref_stripped = ref.strip()
        if not ref_stripped:
            continue

        total_hits = 0

        # Strategy 1: exact search (PyMuPDF handles multi-word spans well)
        for page in doc:
            hits = page.search_for(ref_stripped, quads=False)
            for rect in hits:
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=HIGHLIGHT_COLOR)
                annot.update()
                total_hits += 1

        # Strategy 2: if exact search found nothing, try a shorter key phrase
        # (e.g. use the first ~60 chars or up to "," or "(" to find the core name)
        if total_hits == 0:
            # Try progressively shorter versions of the reference
            shortened = _shorten_reference(ref_stripped)
            for short_ref in shortened:
                if not short_ref:
                    continue
                for page in doc:
                    hits = page.search_for(short_ref, quads=False)
                    for rect in hits:
                        annot = page.add_highlight_annot(rect)
                        annot.set_colors(stroke=HIGHLIGHT_COLOR)
                        annot.update()
                        total_hits += 1
                if total_hits > 0:
                    break

        results[ref_stripped] = total_hits

    # Save the annotated PDF
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()

    return results


def _shorten_reference(ref: str) -> list[str]:
    """
    Generate shorter search strings from a full reference.
    Useful when exact match fails due to line breaks or formatting in PDF.
    Examples:
      "Pioneer Corp. v. Godfrey, 2019 SCC 42" -> try "Pioneer Corp. v. Godfrey"
      "Decision No. 280, 1987 CanLII 1996 (ON WSIAT)" -> try "Decision No. 280"
    """
    candidates = []

    # Try splitting on common separators
    for sep in [",", "(", "[", "–", "—"]:
        if sep in ref:
            part = ref.split(sep)[0].strip()
            if len(part) >= 8:
                candidates.append(part)

    # Try citation year patterns: stop before the year
    import re
    year_match = re.search(r"\b(19|20)\d{2}\b", ref)
    if year_match:
        before_year = ref[:year_match.start()].strip().rstrip(",").strip()
        if len(before_year) >= 8:
            candidates.append(before_year)

    # Also try the full reference minus the last word (handles trailing citation IDs)
    words = ref.split()
    if len(words) > 3:
        candidates.append(" ".join(words[:-1]))

    return candidates


def highlight_pdf(pdf_path: str, references: list[str], output_dir: str) -> tuple[str, dict]:
    """
    High-level function: highlight all references in the PDF and save output.

    Returns:
        output_path: path to the saved highlighted PDF
        results: {reference: hit_count}
    """
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_highlighted.pdf")

    print(f"  Highlighting {len(references)} reference(s) in PDF...")
    results = find_and_highlight(pdf_path, references, output_path)

    highlighted = sum(1 for v in results.values() if v > 0)
    not_found = sum(1 for v in results.values() if v == 0)

    print(f"  ✓ Highlighted: {highlighted} reference(s) found in PDF")
    if not_found > 0:
        print(f"  ✗ Not found in PDF text: {not_found} reference(s)")
        for ref, count in results.items():
            if count == 0:
                print(f"      - {ref}")

    print(f"  Saved to: {output_path}")
    return output_path, results