import subprocess
import sys
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
VERIFY_DIR = os.path.join(PROJECT_ROOT, "verify")

def run_both():
    print("=" * 50)
    print("🚀 1. Starting FastAPI (main.py) on http://localhost:8000 ...")
    print("=" * 50)
    
    fastapi_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd=VERIFY_DIR
    )

    # Wait a moment for Keycloak init & FastAPI to boot
    time.sleep(3)

    print("\n" + "=" * 50)
    print("🎙️ 2. Starting Streamlit (app.py) on http://localhost:8501 ...")
    print("=" * 50)
    
    streamlit_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py"],
        cwd=PROJECT_ROOT
    )

    try:
        fastapi_proc.wait()
        streamlit_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping both servers...")
        fastapi_proc.terminate()
        streamlit_proc.terminate()
        print("✅ Servers stopped.")

if __name__ == "__main__":
    run_both()
