# 🚀 Quick Setup Guide for Teammates

## Prerequisites
- Python 3.11+ installed → https://www.python.org/downloads/
  - ✅ During install, check **"Add Python to PATH"**
- Connected to the **TR corporate network or VPN**

---

## Step 1 — Get the files

**Option A — Download from GitHub:**
1. Go to https://github.com/Rad0286/Training
2. Click the green **Code** button → **Download ZIP**
3. Extract the ZIP to a folder on your computer (e.g. `C:\Tools\cases-reflist\`)

**Option B — Clone with Git (if you have Git installed):**
```
git clone https://github.com/Rad0286/Training.git
```

---

## Step 2 — Launch the app

1. Open the folder you extracted
2. Double-click **`launch.bat`**
3. A browser window will open at **http://localhost:8501**

> First launch may take 1–2 minutes to install dependencies.

---

## Step 3 — Set your ESSO token

1. In the app sidebar, paste your **ESSO Bearer Token**
2. Click **💾 Save Token**
3. Tokens expire daily — repeat this step each day

---

## Step 4 — Use the app

1. Click **Browse files** and upload your PDF judgment(s)
2. Click **🚀 Run Extraction & Highlighting**
3. Wait ~30–90 seconds per PDF
4. Click **⬇️ Download** to save the highlighted PDF

---

## Stopping the app

Close the black command window (or press `Ctrl+C` inside it).

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Python is not installed" | Install from python.org, check "Add to PATH" |
| "No token set" | Paste your ESSO token in the sidebar |
| Network/connection error | Make sure you are on TR network or VPN |
| Port already in use | Close other Streamlit windows, or edit `launch.bat` to use a different port |