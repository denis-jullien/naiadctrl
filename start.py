import subprocess
import sys
import os
import time
import signal
import threading

def run_backend():
    """Run the backend server"""
    print("Starting backend server...")
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
    backend_process = subprocess.Popen([sys.executable, 'main.py'])
    return backend_process

def run_frontend():
    """Run the frontend server in production mode"""
    print("Starting frontend server...")
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend'))
    frontend_process = subprocess.Popen(['npx', 'vite', 'preview', '--port', '5173'])
    return frontend_process

def main():
    """Main entry point"""
    # Start backend
    backend_process = run_backend()
    
    # Wait for backend to start
    print("Waiting for backend to start...")
    time.sleep(5)
    
    # Start frontend
    frontend_process = run_frontend()
    
    # Print access information
    print("\n" + "="*50)
    print("Hydroponic Control System is running!")
    print("Access the dashboard at: http://localhost:5173")
    print("API server is running at: http://localhost:8000")
    print("="*50 + "\n")
    print("Press Ctrl+C to stop all servers")
    
    # Handle graceful shutdown
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        
        # Terminate processes
        backend_process.terminate()
        frontend_process.terminate()
        
        # Wait for processes to terminate
        backend_process.wait()
        frontend_process.wait()
        
        print("Servers stopped")

if __name__ == "__main__":
    main()