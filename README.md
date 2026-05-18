# ⚖️ Case Reference Extractor & Highlighter

Extracts case references from legal judgment PDFs using Claude AI (via Thomson Reuters AI Open Arena), then highlights those references in the original PDF.

---

## Project Structure

```
cases-reflist/
├── app.py                # Streamlit web UI
├── llm_extractor.py      # TR AI Open Arena API integration
├── pdf_highlighter.py    # PDF highlighting logic (PyMuPDF)
├── main.py               # CLI version (batch processing)
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── .dockerignore         # Files excluded from Docker image
└── .env                  # API token (not committed to git)
```

---

## Option A — Run Locally (Python)

### Prerequisites
- Python 3.11+

### Setup
```bash
pip install -r requirements.txt
```

### Run the web app
```bash
streamlit run app.py
```
Open http://localhost:8501 in your browser.

### Run the CLI (batch mode)
```bash
python main.py
```

---

## Option B — Run with Docker (Recommended for sharing)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

### Step 1 — Build the Docker image
```bash
docker build -t case-reflist-app .
```

### Step 2 — Run the container

**Windows (PowerShell):**
```powershell
docker run -p 8501:8501 `
  -v "C:\path\to\your\input:/app/input" `
  -v "C:\path\to\your\output:/app/output" `
  case-reflist-app
```

**Mac / Linux:**
```bash
docker run -p 8501:8501 \
  -v "/path/to/your/input:/app/input" \
  -v "/path/to/your/output:/app/output" \
  case-reflist-app
```

Open http://localhost:8501 in your browser.

### Step 3 — Set your ESSO token
In the app sidebar, paste your ESSO Bearer token and click **Save Token**.

---

## Option C — Docker Compose (easiest for teams)

### Step 1 — Edit `docker-compose.yml`
Update the volume paths to point to your PDF input/output folders:
```yaml
volumes:
  - "C:/Users/YourName/Documents/Cases/Input:/app/input"
  - "C:/Users/YourName/Documents/Cases/Output:/app/output"
```

### Step 2 — Start the app
```bash
docker compose up -d
```

### Step 3 — Open the app
http://localhost:8501

### Stop the app
```bash
docker compose down
```

---

## Sharing with Teammates

### Method 1 — Save & share the Docker image
```bash
# Save to a file
docker save case-reflist-app -o case-reflist-app.tar

# Share the .tar file, then teammates load it:
docker load -i case-reflist-app.tar
docker run -p 8501:8501 case-reflist-app
```

### Method 2 — Push to internal Docker registry
```bash
docker tag case-reflist-app your-internal-registry.company.com/case-reflist-app:latest
docker push your-internal-registry.company.com/case-reflist-app:latest
```

### Method 3 — Run on a shared server
Deploy on any internal VM/server — all teammates access it via the server's IP or hostname:
```
http://<server-ip>:8501
```

---

## Input Requirements

Your **Input Directory** must contain:
- `Reflist_Prompt.txt` — the instruction file for Claude
- One or more `.pdf` files (legal judgment documents)

The **Output Directory** will be created automatically and will contain:
- `<filename>_highlighted.pdf` — the highlighted PDF for each input
- `processing_summary.json` — summary of results

---

## Authorization

Each user needs their own **ESSO Bearer Token** from Thomson Reuters SSO.

- Paste the token in the app sidebar → **Save Token**
- Tokens expire daily — update via the sidebar UI whenever needed
- The token is stored in `.env` locally (never included in the Docker image)

---

## Notes

- The app uses **Claude Opus** via the TR AI Open Arena endpoint
- Processing time: ~30–90 seconds per PDF depending on length
- Very long PDFs (>400K characters) are automatically truncated