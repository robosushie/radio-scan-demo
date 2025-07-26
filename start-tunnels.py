#!/usr/bin/env python3
import subprocess
import time
import signal
import sys
import os
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the process"""
    print(f"Running: {command}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    process = subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def main():
    print("Starting Radio Scan Demo with Localtunnel...")
    print()
    
    processes = []
    
    try:
        # Get the project root directory
        project_root = Path(__file__).parent
        
        # 1. Start Python backend
        print("1. Starting Python backend...")
        backend_process = run_command("python main.py", cwd=project_root / "src")
        processes.append(("Backend", backend_process))
        
        # Wait a bit for backend to start
        time.sleep(2)
        
        # 2. Start Next.js frontend
        print()
        print("2. Starting Next.js frontend...")
        frontend_process = run_command("npm run dev", cwd=project_root / "frontend")
        processes.append(("Frontend", frontend_process))
        
        # Wait a bit for frontend to start
        time.sleep(3)
        
        # 3. Start Localtunnel for frontend
        print()
        print("3. Starting Localtunnel for frontend (port 3000)...")
        frontend_tunnel_process = run_command("lt --port 3000 --subdomain radio-scan")
        processes.append(("Frontend Tunnel", frontend_tunnel_process))
        
        # 4. Start Localtunnel for backend
        print()
        print("4. Starting Localtunnel for backend (port 8000)...")
        backend_tunnel_process = run_command("lt --port 8000 --subdomain radio-scan-api")
        processes.append(("Backend Tunnel", backend_tunnel_process))
        
        print()
        print("All services starting...")
        print()
        print("URLs:")
        print("- Frontend: https://radio-scan.loca.lt")
        print("- Backend API: https://radio-scan-api.loca.lt")
        print("- WebSocket: wss://radio-scan-api.loca.lt/ws/stream")
        print()
        print("Access your app on mobile at: https://radio-scan.loca.lt")
        print()
        print("Press Ctrl+C to stop all services")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print()
        print("Stopping all services...")
        
        # Terminate all processes
        for name, process in processes:
            try:
                print(f"Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"Error stopping {name}: {e}")
        
        print("All services stopped.")
        sys.exit(0)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 