"""
Starts and verifies all 3 platform services as detached persistent processes.
"""
import sys
import os
import time
import socket
import urllib.request
import subprocess
from pathlib import Path

PLATFORM_ROOT = Path(r"C:\Users\panka\.gemini\antigravity\scratch\universal_multiagent_platform")
SCRATCH_DIR = PLATFORM_ROOT.parent
PYTHON_EXE = str(SCRATCH_DIR / "ocr_multiagent_system" / "venv_ocr" / "Scripts" / "python.exe")

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def check_endpoint(url: str, timeout: float = 3.0) -> bool:
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        return resp.getcode() == 200
    except Exception:
        return False

def start_services():
    print(f"Using Python: {PYTHON_EXE}")

    # 1. Face Detection Server on Port 8050
    if not is_port_in_use(8050) or not check_endpoint("http://localhost:8050"):
        fd_script = str(SCRATCH_DIR / "multi_agent_face_detection" / "server.py")
        print("Launching Face Detection Server (8050)...")
        subprocess.Popen(
            [PYTHON_EXE, fd_script],
            cwd=str(SCRATCH_DIR / "multi_agent_face_detection"),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        print("Face Detection Server already running on 8050.")

    # 2. Industrial Vision RAG Server on Port 8080
    if not is_port_in_use(8080) or not check_endpoint("http://localhost:8080"):
        ind_script = str(SCRATCH_DIR / "industrial_multiagent_rag" / "dashboard.py")
        print("Launching Industrial Vision RAG Server (8080)...")
        subprocess.Popen(
            [PYTHON_EXE, ind_script],
            cwd=str(SCRATCH_DIR / "industrial_multiagent_rag"),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        print("Industrial Vision RAG Server already running on 8080.")

    # 3. Master Streamlit Platform on Port 8550
    if not is_port_in_use(8550) or not check_endpoint("http://localhost:8550"):
        app_path = str(PLATFORM_ROOT / "app.py")
        print("Launching Master Streamlit Platform (8550)...")
        subprocess.Popen(
            [PYTHON_EXE, "-m", "streamlit", "run", app_path, "--server.port", "8550", "--server.headless", "true"],
            cwd=str(PLATFORM_ROOT),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        print("Master Streamlit Platform already running on 8550.")

    # Wait for services to be ready
    print("\nWaiting for services to become responsive...")
    for i in range(15):
        time.sleep(1.0)
        fd_ok = check_endpoint("http://localhost:8050")
        ind_ok = check_endpoint("http://localhost:8080")
        st_ok = check_endpoint("http://localhost:8550")
        print(f"[{i+1}/15] Port 8050: {fd_ok} | Port 8080: {ind_ok} | Port 8550: {st_ok}")
        if fd_ok and ind_ok and st_ok:
            print("\nALL 3 PLATFORMS ONLINE AND HEALTHY!")
            return True

    print("\nServices started, checking status...")
    return False

if __name__ == "__main__":
    start_services()
