#!/usr/bin/env python3
"""
Run Flask backend for FlipInsight
"""
import os
import sys

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Import and run Flask app
from backend.app import app

if __name__ == '__main__':
    print("Starting FlipInsight Flask backend...")
    print("Frontend will be available at: http://localhost:5000")
    print("API endpoints available at: http://localhost:5000/api/*")
    print("\nPress Ctrl+C to stop the server")
    app.run(debug=True, port=5000)