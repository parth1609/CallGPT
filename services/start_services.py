import subprocess
import time
import sys
import os
from pathlib import Path
SERVICES = [
    "document_service",
    "embedding_service",
    "vectorstore_service",
    "retrieval_service",
    "llm_service",
    "conversation_service",
    "api_gateway"
]

def start_services():
    processes = []
    
    # Start each service in a separate process
    for service in SERVICES:
        print(f"\n🚀 Starting {service}...")
        try:
            cmd = [sys.executable, "main.py"]
            proc = subprocess.Popen(
                cmd,
                cwd=os.path.join("services", service) if os.path.exists("services") else service,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append((service, proc))
            print(f"✅ {service} started (PID: {proc.pid})")
            time.sleep(2)  # Give each service time to initialize
        except Exception as e:
            print(f"❌ Failed to start {service}: {str(e)}")
    
    print("\n🔍 Services running (Press Ctrl+C to stop):")
    for i, (service, _) in enumerate(processes, 1):
        port = 8000 + i if i < 7 else 8000  # API Gateway is last
        print(f"  • {service}: http://localhost:{port}/docs")
    
    print("\n🛑 Press Ctrl+C to stop all services...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for service, proc in processes:
            proc.terminate()
            print(f"  • Stopped {service}")
        print("\n👋 All services stopped.")

if __name__ == "__main__":
    print("🌟 Starting CallGPT Microservices...")
    start_services()
