"""
Universal Multi-Agent LangGraph Platform — Unified Launcher
============================================================
Coordinates and launches all three multi-agent platform components:
  1. Multi-Agent Face Detection Server & Dashboard (Port 8050)
  2. Industrial Vision RAG Control Room (Port 8080)
  3. Universal Streamlit Platform Dashboard (Port 8550)

Usage:
    python run_platform.py [port]
"""
import os
import sys
import time
import socket
import webbrowser
import threading
import subprocess
from pathlib import Path

PLATFORM_ROOT = Path(__file__).parent.resolve()
SCRATCH_DIR = PLATFORM_ROOT.parent.resolve()


def find_python():
    """Find the best Python interpreter with installed dependencies."""
    candidates = [
        SCRATCH_DIR / "ocr_multiagent_system" / "venv_ocr" / "Scripts" / "python.exe",
        PLATFORM_ROOT / ".venv" / "Scripts" / "python.exe",
        SCRATCH_DIR / "industrial_multiagent_rag" / ".venv" / "Scripts" / "python.exe",
        SCRATCH_DIR / "multi_agent_face_detection" / ".venv" / "Scripts" / "python.exe",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return sys.executable


def is_port_in_use(port: int) -> bool:
    """Check if a local port is already listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    python = find_python()
    
    # If invoked with system Python (e.g. 3.8), re-exec using project venv Python (3.11)
    try:
        if Path(sys.executable).resolve() != Path(python).resolve():
            print(f"  Switching to configured platform Python: {python}")
            sys.exit(subprocess.call([python, str(Path(__file__).resolve())] + sys.argv[1:]))
    except Exception as e:
        print(f"  Warning during python check: {e}")

    app_path = str(PLATFORM_ROOT / "app.py")
    port = sys.argv[1] if len(sys.argv) > 1 else "8550"
    background_procs = []

    print("=" * 68)
    print("  [Universal Multi-Agent LangGraph Platform Master Launcher]")
    print("=" * 68)
    print(f"  Python:     {python}")
    print(f"  Dashboard:  {app_path}")
    print(f"  Master URL: http://localhost:{port}")
    print("=" * 68)

    # 1. Ensure Face Detection Server is running on port 8050
    if not is_port_in_use(8050):
        fd_server = SCRATCH_DIR / "multi_agent_face_detection" / "server.py"
        if fd_server.exists():
            print("  Starting Face Detection Server on Port 8050...")
            proc = subprocess.Popen(
                [python, str(fd_server)],
                cwd=str(fd_server.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            background_procs.append(proc)
            time.sleep(1.0)
    else:
        print("  Face Detection Server already active on Port 8050.")

    # 2. Ensure Industrial Vision RAG Server is running on port 8080
    if not is_port_in_use(8080):
        ind_server = SCRATCH_DIR / "industrial_multiagent_rag" / "dashboard.py"
        if ind_server.exists():
            print("  Starting Industrial Vision RAG Server on Port 8080...")
            proc = subprocess.Popen(
                [python, str(ind_server)],
                cwd=str(ind_server.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            background_procs.append(proc)
            time.sleep(1.0)
    else:
        print("  Industrial Vision RAG Server already active on Port 8080.")

    print(f"  Launching Master Universal Streamlit Dashboard on Port {port}...")
    print("=" * 68)

    # Auto open browser after 2 seconds
    def open_browser():
        time.sleep(2.0)
        webbrowser.open(f"http://localhost:{port}")

    threading.Thread(target=open_browser, daemon=True).start()

    cmd = [
        python, "-m", "streamlit", "run", app_path,
        "--server.port", port,
        "--server.headless", "true"
    ]

    try:
        subprocess.run(cmd, cwd=str(PLATFORM_ROOT))
    except KeyboardInterrupt:
        print("\n[Platform] Shutting down.")
    finally:
        for p in background_procs:
            try:
                p.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    main()
