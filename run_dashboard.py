"""
Launcher script for the Adaptive Variable-Resolution 2.5D LiDAR Mapping Dashboard.

Usage:
    # Run full system (FastAPI backend + Streamlit dashboard):
    python run_dashboard.py

    # Run FastAPI backend only:
    python run_dashboard.py --backend-only

    # Run Streamlit frontend only:
    python run_dashboard.py --frontend-only
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
import httpx

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_URL = "http://127.0.0.1:8000"


def is_backend_running() -> bool:
    """Check if FastAPI backend is responding on port 8000."""
    try:
        resp = httpx.get(f"{BACKEND_URL}/api/v1/health", timeout=1.5)
        return resp.status_code == 200
    except Exception:
        return False


def start_backend() -> subprocess.Popen:
    """Launch FastAPI uvicorn server in a subprocess."""
    print("[Launcher] Starting FastAPI backend on http://127.0.0.1:8000 ...")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.backend.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=str(PROJECT_ROOT),
    )
    # Wait for backend to become ready
    for _ in range(25):
        if is_backend_running():
            print("[Launcher] FastAPI backend is online and ready!")
            return proc
        time.sleep(0.4)
    print("[Launcher] Warning: Backend startup timed out or is taking longer than expected.")
    return proc


def start_react_frontend() -> int:
    """Launch React + Three.js engineering simulator."""
    print("[Launcher] Starting React + Three.js LiDAR simulator on http://localhost:3000 ...")
    cmd = ["npm", "run", "dev"]
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT / "frontend"), shell=True)


def start_frontend() -> int:
    """Launch Streamlit frontend."""
    print("[Launcher] Starting Streamlit engineering dashboard on http://localhost:8501 ...")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(PROJECT_ROOT / "src" / "frontend" / "app.py"),
        "--server.port",
        "8501",
        "--server.headless",
        "true",
    ]
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="LiDAR Mapping Dashboard Launcher")
    parser.add_argument("--backend-only", action="store_true", help="Launch FastAPI backend only")
    parser.add_argument("--frontend-only", action="store_true", help="Launch frontend only")
    parser.add_argument("--react", action="store_true", help="Launch React + Three.js simulator")
    parser.add_argument("--streamlit", action="store_true", help="Launch Streamlit dashboard")
    args = parser.parse_args()

    if args.backend_only:
        backend_proc = start_backend()
        try:
            backend_proc.wait()
        except KeyboardInterrupt:
            print("\n[Launcher] Stopping backend...")
            backend_proc.terminate()
        return

    if args.frontend_only:
        if args.streamlit:
            sys.exit(start_frontend())
        sys.exit(start_react_frontend())

    if args.react:
        backend_proc = None
        if not is_backend_running():
            backend_proc = start_backend()
        else:
            print("[Launcher] Backend is already running on port 8000.")
        try:
            start_react_frontend()
        finally:
            if backend_proc is not None:
                print("[Launcher] Terminating backend subprocess...")
                backend_proc.terminate()
        return

    # Default: Start backend if not already running, then launch frontend
    backend_proc = None
    if not is_backend_running():
        backend_proc = start_backend()
    else:
        print("[Launcher] Backend is already running on port 8000.")

    try:
        start_frontend()
    finally:
        if backend_proc is not None:
            print("[Launcher] Terminating backend subprocess...")
            backend_proc.terminate()


if __name__ == "__main__":
    main()
