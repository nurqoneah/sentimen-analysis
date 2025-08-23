#!/usr/bin/env python3
"""
Run script for the Simple Social Media Sentiment Analysis Tool
"""

import os
import sys
from app import app
from config import config

def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        'uploads',
        'data',
        'static/exports',
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directory '{directory}' ready")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask',
        'transformers',
        'torch',
        'pandas',
        'plotly',
        'wordcloud',
        'requests',
        'loguru',
        'jmespath'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is missing")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
        return False
    
    return True

def main():
    """Main function to run the application"""
    print("=" * 60)
    print("Simple Social Media Sentiment Analysis Tool")
    print("=" * 60)
    
    # Get environment
    env = os.environ.get('FLASK_ENV', 'development')
    print(f"Environment: {env}")
    
    # Create directories
    print("\nCreating directories...")
    create_directories()
    
    # Check dependencies
    print("\nChecking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Configure app
    app.config.from_object(config[env])
    
    # Get host and port
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5002))
    debug = env == 'development'
    
    print(f"\nStarting server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"\nAccess the application at: http://localhost:{port}")
    print("=" * 60)
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
    except Exception as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
