#!/usr/bin/env python3
"""
Unified startup script for the complete application stack:
- MCP Server
- FastAPI Backend
- React Frontend (Vite dev server)
"""

import subprocess
import threading
import sys
import signal
import os
import time
from pathlib import Path

# Color codes for output
RED = "\033[0;31m"
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[0;33m"
NC = "\033[0m"  # No Color

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.threads = []
        self.shutdown_requested = False

    def add_process(self, name, color, cmd, cwd=None):
        """Add a process to be managed."""
        proc_info = {
            'name': name,
            'color': color,
            'cmd': cmd,
            'cwd': cwd,
            'process': None,
            'thread': None
        }
        return proc_info

    def stream_output(self, proc_info):
        """Stream output from a process with colored prefix."""
        process = proc_info['process']
        name = proc_info['name']
        color = proc_info['color']
        
        try:
            for line in iter(process.stdout.readline, b''):
                if self.shutdown_requested:
                    break
                output = line.decode('utf-8', errors='replace').rstrip()
                if output:  # Only print non-empty lines
                    print(f"{color}[{name}] {output}{NC}", flush=True)
        except Exception as e:
            if not self.shutdown_requested:
                print(f"{RED}[{name}] Error reading output: {e}{NC}", flush=True)

    def start_process(self, proc_info):
        """Start a single process."""
        try:
            print(f"{proc_info['color']}[{proc_info['name']}] Starting: {' '.join(proc_info['cmd'])}{NC}")
            
            process = subprocess.Popen(
                proc_info['cmd'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=proc_info['cwd'],
                bufsize=1,
                universal_newlines=False
            )
            
            proc_info['process'] = process
            self.processes.append(process)
            
            # Start output streaming thread
            thread = threading.Thread(
                target=self.stream_output,
                args=(proc_info,),
                daemon=True
            )
            thread.start()
            proc_info['thread'] = thread
            self.threads.append(thread)
            
            return True
            
        except Exception as e:
            print(f"{RED}[{proc_info['name']}] Failed to start: {e}{NC}")
            return False

    def shutdown_all(self):
        """Gracefully shutdown all processes."""
        if self.shutdown_requested:
            return
            
        self.shutdown_requested = True
        print(f"\n{YELLOW}Shutting down all services...{NC}")
        
        # Terminate all processes
        for process in self.processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                except Exception as e:
                    print(f"{RED}Error terminating process: {e}{NC}")
        
        # Wait for processes to terminate gracefully
        for process in self.processes:
            if process:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"{RED}Force killing process...{NC}")
                    process.kill()
                except Exception:
                    pass
        
        print(f"{GREEN}All services stopped.{NC}")

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print(f"\n{YELLOW}Received interrupt signal...{NC}")
    manager.shutdown_all()
    sys.exit(0)

def check_dependencies():
    """Check if required dependencies are available."""
    # Check if npm is available for frontend
    try:
        subprocess.run(['npm', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{RED}Error: npm is not installed or not in PATH{NC}")
        print("Please install Node.js and npm to run the frontend")
        return False
    
    # Check if frontend directory exists
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print(f"{RED}Error: frontend directory not found{NC}")
        return False
    
    # Check if package.json exists
    if not (frontend_dir / "package.json").exists():
        print(f"{RED}Error: frontend/package.json not found{NC}")
        return False
    
    return True

def install_frontend_deps():
    """Install frontend dependencies if needed."""
    frontend_dir = Path("frontend")
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print(f"{BLUE}Installing frontend dependencies...{NC}")
        try:
            subprocess.run(
                ['npm', 'install'],
                cwd=frontend_dir,
                check=True,
                capture_output=True
            )
            print(f"{GREEN}Frontend dependencies installed successfully{NC}")
        except subprocess.CalledProcessError as e:
            print(f"{RED}Failed to install frontend dependencies: {e}{NC}")
            return False
    
    return True

def main():
    global manager
    
    print(f"{BLUE}🚀 Starting Finn - Financial Assistant Stack{NC}")
    print(f"{BLUE}{'='*50}{NC}")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Install frontend dependencies if needed
    if not install_frontend_deps():
        sys.exit(1)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    manager = ProcessManager()
    
    # Define all processes
    processes = [
        manager.add_process(
            "mcp-server",
            RED,
            [sys.executable, "-u", "mcp_server.py"]
        ),
        manager.add_process(
            "email-mcp-server",
            YELLOW,
            [sys.executable, "-u", "email_mcp_server.py"]
        ),
        manager.add_process(
            "backend",
            GREEN,
            [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"]
        ),
        manager.add_process(
            "frontend",
            BLUE,
            ["npm", "run", "dev"],
            cwd="frontend"
        )
    ]
    
    # Start all processes
    started_count = 0
    for proc_info in processes:
        if manager.start_process(proc_info):
            started_count += 1
            time.sleep(1)  # Small delay between starts
        else:
            print(f"{RED}Failed to start {proc_info['name']}, aborting...{NC}")
            manager.shutdown_all()
            sys.exit(1)
    
    print(f"\n{GREEN}✅ All {started_count} services started successfully!{NC}")
    print(f"{BLUE}📱 Frontend: http://localhost:5173{NC}")
    print(f"{GREEN}🔧 Backend API: http://localhost:8000{NC}")
    print(f"{RED}🔌 MCP Server: Running{NC}")
    print(f"{YELLOW}📧 Email MCP Server: Running{NC}")
    print(f"\n{YELLOW}Press Ctrl+C to stop all services{NC}")
    
    try:
        # Wait for all processes to complete
        for process in manager.processes:
            if process:
                process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        manager.shutdown_all()

if __name__ == "__main__":
    main() 