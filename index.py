import os
import sys
import subprocess
import time
import requests
from http.server import BaseHTTPRequestHandler

# ----------------- WARNING & DISCLAIMER -----------------
# Streamlit is stateful and relies on WebSockets, which are unsupported by Vercel serverless functions.
# The serverless runtime will spin down execution container nodes, causing disconnected sessions.
# For production, we strongly recommend deploying directly to Streamlit Community Cloud or Render.
# --------------------------------------------------------

# Define port and start Streamlit process if not already running
PORT = 8501
process = None

def start_streamlit():
    global process
    if process is None:
        print("Starting Streamlit subprocess...")
        # Start streamlit in headless mode
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port",
                str(PORT),
                "--server.headless",
                "true",
                "--server.enableCORS",
                "false",
                "--server.enableXsrfProtection",
                "false"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Wait a moment for it to boot up
        time.sleep(3)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        start_streamlit()
        
        # Proxy standard request to local Streamlit server
        url = f"http://localhost:{PORT}{self.path}"
        try:
            headers = {key: val for key, val in self.headers.items()}
            # Remove host header to avoid conflict
            headers.pop('Host', None)
            
            res = requests.get(url, headers=headers, stream=True, timeout=10)
            
            self.send_response(res.status_code)
            for key, val in res.headers.items():
                self.send_header(key, val)
            self.end_headers()
            
            self.wfile.write(res.content)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"Error proxying request to Streamlit: {e}<br><em>Note: Running Streamlit on serverless Vercel is highly unstable. Consider using Streamlit Community Cloud instead.</em>".encode())

    def do_POST(self):
        start_streamlit()
        
        url = f"http://localhost:{PORT}{self.path}"
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else None
        
        try:
            headers = {key: val for key, val in self.headers.items()}
            headers.pop('Host', None)
            
            res = requests.post(url, headers=headers, data=post_data, stream=True, timeout=10)
            
            self.send_response(res.status_code)
            for key, val in res.headers.items():
                self.send_header(key, val)
            self.end_headers()
            
            self.wfile.write(res.content)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"Error proxying request to Streamlit: {e}".encode())
