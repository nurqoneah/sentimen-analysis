#!/usr/bin/env python3
"""
Simple startup script for the sentiment analysis application
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    
    print("=" * 60)
    print("Simple Social Media Sentiment Analysis Tool")
    print("=" * 60)
    print("Starting server on http://localhost:5002")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5002, debug=True)
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install flask transformers torch pandas plotly wordcloud requests loguru jmespath")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    sys.exit(1)
