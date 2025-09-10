#!/usr/bin/env python3
"""
Unified Launcher: Runs FastAPI backend and React frontend (Vite dev server) for Agentic SF Dev
"""
import subprocess
import sys
import time
import signal
import os
from pathlib import Path

import argparse
import socket
try:
    import psutil
except ImportError:
    psutil = None

def ensure_required_files():
    data_dir = Path("data")
    db_path = data_dir / "app.db"
    if not data_dir.exists():
        print("[init] Creating data/ directory...")
        data_dir.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        print("[init] Creating empty SQLite DB at data/app.db...")
        import sqlite3
        cxn = sqlite3.connect(str(db_path))
        cxn.close()

def free_port(port):
    if not psutil:
        print("[force] psutil not installed, cannot free ports automatically.")
        return
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.info.get('connections', []):
                if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
                    print(f"[force] Killing process {proc.info['pid']} ({proc.info['name']}) on port {port}")
                    proc.kill()
        except Exception:
            continue

def free_ports_if_needed(force=False):
    ports = [8000, 1420]
    if force:
        for port in ports:
            free_port(port)
    else:
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("localhost", port))
                except OSError:
                    print(f"[error] Port {port} is already in use. Use --force to free it.")
                    exit(1)

class UnifiedLauncher:
    def __init__(self):
        self.processes = []
        self.api_port = 8000
        self.react_port = 1420

    def start_api_server(self):
        print("🚀 Starting FastAPI server on http://localhost:8000...")
        process = subprocess.Popen([
            sys.executable, "app/api/server.py"
        ], cwd=Path(__file__).parent)
        self.processes.append(("FastAPI", process))
        return process

    def start_react_dev(self):
        print("⚛️  Starting React dev server on http://localhost:1420...")
        desktop_ui_path = Path(__file__).parent / "desktop-ui"
        process = subprocess.Popen([
            "npm", "run", "dev"
        ], cwd=desktop_ui_path)
        self.processes.append(("React", process))
        return process

    def check_ports(self):
        import socket
        def is_port_free(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("localhost", port))
                    return True
                except:
                    return False
        if not is_port_free(self.api_port):
            print(f"⚠️  Port {self.api_port} is already in use (FastAPI)")
        if not is_port_free(self.react_port):
            print(f"⚠️  Port {self.react_port} is already in use (React)")

    def cleanup(self, signal_num=None, frame=None):
        print("\n🛑 Shutting down all services...")
        for name, process in self.processes:
            try:
                print(f"   Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"   Error stopping {name}: {e}")
        print("✅ All services stopped.")
        sys.exit(0)

    def run(self):
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        print("🚀 Starting Agentic SF Dev (Unified Mode)")
        print("=" * 60)
        self.check_ports()
        try:
            api_proc = self.start_api_server()
            time.sleep(2)
            react_proc = self.start_react_dev()
            print("\n✅ All services started!")
            print("=" * 60)
            print(f"🚀 FastAPI:       http://localhost:{self.api_port}")
            print(f"⚛️  React Dev:     http://localhost:{self.react_port}")
            print(f"📊 API Docs:      http://localhost:{self.api_port}/docs")
            print("=" * 60)
            print("\n🛑 Press Ctrl+C to stop all services")
            while True:
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"\n❌ {name} server stopped unexpectedly!")
                        self.cleanup()
                        return
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified launcher for Agentic SF Dev")
    parser.add_argument('--force', action='store_true', help='Force kill processes on occupied ports before starting')
    args = parser.parse_args()

    ensure_required_files()
    free_ports_if_needed(force=args.force)
    launcher = UnifiedLauncher()
    launcher.run()
