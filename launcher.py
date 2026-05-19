"""
launcher.py
Standalone launcher for Case Reference Extractor.
Bundled by PyInstaller into a single .exe
"""

import sys
import os
import threading
import webbrowser
import time

# When running as a PyInstaller bundle, find the app directory
if getattr(sys, 'frozen', False):
    APP_DIR = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

APP_FILE = os.path.join(APP_DIR, "app.py")
PORT = 8501


def open_browser():
    """Wait for Streamlit to start, then open the browser."""
    time.sleep(5)
    webbrowser.open(f"http://localhost:{PORT}")


def main():
    # Must set these BEFORE importing streamlit to override defaults
    os.environ["STREAMLIT_SERVER_PORT"] = str(PORT)
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    # This is the critical one - disable dev mode before streamlit loads
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()

    # Use streamlit bootstrap directly (bypasses CLI/click entirely)
    from streamlit.web import bootstrap
    bootstrap.run(APP_FILE, False, [], {})


if __name__ == "__main__":
    main()