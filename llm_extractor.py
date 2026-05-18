"""
llm_extractor.py
Sends PDF text + instructions to the TR AI Open Arena endpoint
and returns a list of case references.
"""

import os
import json
import requests
import pdfplumber
from dotenv import load_dotenv

load_dotenv()

# ── TR AI Open Arena configuration ────────────────────────────────────────────
ENDPOINT_URL = "https://aiopenarena.gcs.int.thomsonreuters.com/v3/inference"
WORKFLOW_ID  = "4de98216-8278-49cc-a549-dcbf269588ab"

# Max characters to send (safety measure for very large PDFs)
MAX_CHARS = 400_000

# ── Hardcoded system prompt ────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a legal research assistant specializing in identifying case references in legal judgments.

Your task is to extract ALL case references cited in the judgment provided. A case reference is any citation to a legal case, decision, or judgment.

Instructions:
1. Read through the entire judgment carefully.
2. Identify every case reference cited, including:
   - Named cases (e.g., "Smith v. Jones, 2020 ONCA 123")
   - Neutral citations (e.g., "2019 SCC 42")
   - Law report citations (e.g., "[2018] 2 SCR 456")
   - Decision numbers (e.g., "Decision No. 280/87")
3. Extract the full reference as it appears in the text.
4. Do NOT include references to legislation, statutes, or regulations.
5. Do NOT include the judge's own case name (the case being decided).

Output format:
- List ONLY the case references, one per line.
- Do not include any explanation, preamble, or commentary.
- Start your output with the exact heading: Final References
- If no case references are found, write: Final References\nNo References

Example output:
Final References
Smith v. Jones, 2020 ONCA 123
R. v. Brown, [2019] 2 SCR 100
Decision No. 280/87 (WSIAT)"""


def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def call_tr_endpoint(pdf_text: str, pdf_name: str) -> str:
    """
    POST to the TR AI Open Arena endpoint.
    Returns the raw text response from the model.
    """
    esso_token = os.getenv("TR_ESSO_TOKEN", "").strip()
    if not esso_token:
        raise ValueError(
            "TR_ESSO_TOKEN is not set in .env — please add your current ESSO bearer token."
        )

    # Truncate PDF text if needed
    if len(pdf_text) > MAX_CHARS:
        print(f"  [Warning] PDF text truncated from {len(pdf_text):,} to {MAX_CHARS:,} chars")
        pdf_text = pdf_text[:MAX_CHARS]

    # Build the query: instruct the model to extract references from the PDF text
    query = (
        f"Please review the following legal judgment ({pdf_name}) and extract all case references "
        f"following your instructions.\n\n"
        f"--- JUDGMENT TEXT ---\n{pdf_text}"
    )

    payload = {
        "workflow_id": WORKFLOW_ID,
        "query": query,
        "is_persistence_allowed": False,
        "modelparams": {
            "system_prompt_LLM_task": {
                "system_prompt": SYSTEM_PROMPT
            },
            "llm_LLM_task": {
                "effort": "high",
                "output_schema": {},
                "max_tokens": "128000",
                "enable_websearch": "True",
                "enable_reasoning": "True"
            }
        },
        "input_variables": {},
        "conversation_id": None
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"bearer {esso_token}"
    }

    print(f"  Calling TR AI Open Arena endpoint...")
    response = requests.post(ENDPOINT_URL, headers=headers, data=json.dumps(payload), timeout=300)

    if response.status_code != 200:
        raise RuntimeError(
            f"Endpoint returned HTTP {response.status_code}: {response.text[:500]}"
        )

    return response.text


def parse_references(raw_response: str) -> list[str]:
    """
    Parse the model's response to extract the reference list.
    The model is instructed to mark the output with 'Final References'.
    TR AI Open Arena returns: {"result": {"answer": {"llm_LLM_task": "<text>"}}}
    """
    # Parse the TR AI Open Arena JSON response structure
    try:
        data = json.loads(raw_response)
        if isinstance(data, dict):
            # TR AI Open Arena format: result.answer.llm_LLM_task
            try:
                raw_response = data["result"]["answer"]["llm_LLM_task"]
            except (KeyError, TypeError):
                # Fallback: search common keys at any level
                for key in ("output", "response", "answer", "text", "content"):
                    if key in data and isinstance(data[key], str):
                        raw_response = data[key]
                        break
                else:
                    raw_response = json.dumps(data)
    except (json.JSONDecodeError, ValueError):
        pass  # Not JSON, treat as plain text

    # Look for the "Final References" section marker
    marker = "Final References"
    idx = raw_response.find(marker)
    if idx != -1:
        ref_section = raw_response[idx + len(marker):].strip()
    else:
        # Fallback: if marker not found, use the full response
        ref_section = raw_response.strip()

    # Check for explicit "No References"
    if ref_section.lower().startswith("no references"):
        return []

    # Parse line by line
    references = []

    # Patterns that indicate a non-reference line (intro text, headers)
    skip_patterns = [
        "final references",
        "based on my review",
        "based on the judgment",
        "based on a review",
        "the following case references",
        "here are the case references",
        "here is the reference list",
        "reference list",
        "case references",
        "no case references",
        "extracted from",
        "judge's own reasons",
        "judge's own text",
        "in the judge's",
    ]

    for line in ref_section.splitlines():
        line = line.strip()
        if not line:
            continue

        # Strip markdown bold/italic markers
        line = line.replace("**", "").replace("__", "").strip()

        # Skip separator lines
        if set(line) <= set("-=_*#"):
            continue

        # Skip lines that are clearly introductory/header text
        line_lower = line.lower()
        if any(pat in line_lower for pat in skip_patterns):
            continue

        # Skip lines that are clearly sentences (contain verbs/conjunctions typical of prose)
        if line_lower.startswith("the following") or line_lower.startswith("below is"):
            continue

        # Remove leading bullets, dashes, numbers
        line = line.lstrip("•·-–—*#0123456789.) ").strip()

        # A valid reference should be at least 4 chars and not a full sentence
        if line and len(line) >= 4 and not line.endswith(":"):
            references.append(line)

    return references


def extract_references(pdf_path: str) -> list[str]:
    """
    Main entry point: given a PDF path,
    return a list of case references extracted by the TR LLM endpoint.
    """
    pdf_name = os.path.basename(pdf_path)
    print(f"  Extracting text from {pdf_name}...")
    pdf_text = extract_pdf_text(pdf_path)
    print(f"  Extracted {len(pdf_text):,} characters from PDF.")

    raw_response = call_tr_endpoint(pdf_text, pdf_name)

    references = parse_references(raw_response)
    print(f"  Model returned {len(references)} reference(s).")

    return references
