#!/usr/bin/env python3
"""
Simple health check endpoint for Docker containers.
"""
import json
import sys
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_info = {
                'status': 'healthy',
                'timestamp': int(time.time()),
                'service': 'scrapper-llm',
                'version': '1.0.0',
                'checks': {
                    'filesystem': self.check_filesystem(),
                    'python': self.check_python(),
                    'dependencies': self.check_dependencies()
                }
            }
            
            self.wfile.write(json.dumps(health_info).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def check_filesystem(self):
        """Check filesystem access."""
        try:
            test_file = Path('/app/data/.health_check')
            test_file.touch()
            test_file.unlink()
            return {'status': 'ok', 'message': 'Filesystem accessible'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_python(self):
        """Check Python environment."""
        try:
            import sys
            return {
                'status': 'ok', 
                'message': f'Python {sys.version.split()[0]} running',
                'version': sys.version.split()[0]
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_dependencies(self):
        """Check critical dependencies."""
        try:
            import selenium
            import requests
            import numpy
            return {
                'status': 'ok',
                'message': 'Core dependencies available',
                'selenium': selenium.__version__,
                'requests': requests.__version__,
                'numpy': numpy.__version__
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def log_message(self, format, *args):
        """Override to suppress access logs."""
        pass

def start_health_server(port=8000):
    """Start health check server."""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()

if __name__ == '__main__':
    start_health_server()