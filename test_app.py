#!/usr/bin/env python3
"""
Simple test script to verify the application components
"""

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import flask
        print("✓ Flask imported successfully")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ Pandas imported successfully")
    except ImportError as e:
        print(f"✗ Pandas import failed: {e}")
        return False
    
    try:
        import requests
        print("✓ Requests imported successfully")
    except ImportError as e:
        print(f"✗ Requests import failed: {e}")
        return False
    
    try:
        from utils import extract_post_id, allowed_file
        print("✓ Utils module imported successfully")
    except ImportError as e:
        print(f"✗ Utils import failed: {e}")
        return False
    
    try:
        from sentiment_analyzer import SentimentAnalyzer
        print("✓ SentimentAnalyzer imported successfully")
    except ImportError as e:
        print(f"✗ SentimentAnalyzer import failed: {e}")
        return False
    
    try:
        from visualizations import create_visualizations
        print("✓ Visualizations module imported successfully")
    except ImportError as e:
        print(f"✗ Visualizations import failed: {e}")
        return False
    
    return True

def test_sentiment_analyzer():
    """Test the sentiment analyzer with a simple text"""
    print("\nTesting sentiment analyzer...")
    
    try:
        from sentiment_analyzer import SentimentAnalyzer
        
        # This might take a while on first run as it downloads the model
        print("Initializing sentiment analyzer (this may take a while on first run)...")
        analyzer = SentimentAnalyzer()
        
        # Test with a simple positive text
        test_text = "I love this product! It's amazing!"
        result = analyzer.analyze_single_text(test_text)
        
        print(f"Test text: {test_text}")
        print(f"Result: {result}")
        
        if 'sentiment_label' in result and 'sentiment_score' in result:
            print("✓ Sentiment analyzer working correctly")
            return True
        else:
            print("✗ Sentiment analyzer returned unexpected format")
            return False
            
    except Exception as e:
        print(f"✗ Sentiment analyzer test failed: {e}")
        return False

def test_utils():
    """Test utility functions"""
    print("\nTesting utility functions...")
    
    try:
        from utils import extract_post_id, allowed_file
        
        # Test Instagram URL extraction
        instagram_url = "https://www.instagram.com/p/DNcgnWvRJ9-/"
        post_id = extract_post_id(instagram_url, 'instagram')
        if post_id == "DNcgnWvRJ9-":
            print("✓ Instagram URL extraction working")
        else:
            print(f"✗ Instagram URL extraction failed: got {post_id}")
            return False
        
        # Test TikTok URL extraction
        tiktok_url = "https://www.tiktok.com/@putra11__/video/7539605848159489286"
        post_id = extract_post_id(tiktok_url, 'tiktok')
        if post_id == "7539605848159489286":
            print("✓ TikTok URL extraction working")
        else:
            print(f"✗ TikTok URL extraction failed: got {post_id}")
            return False
        
        # Test file validation
        if allowed_file("test.csv"):
            print("✓ CSV file validation working")
        else:
            print("✗ CSV file validation failed")
            return False
        
        if not allowed_file("test.txt"):
            print("✓ Non-CSV file rejection working")
        else:
            print("✗ Non-CSV file rejection failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Utils test failed: {e}")
        return False

def test_flask_app():
    """Test Flask app creation"""
    print("\nTesting Flask app creation...")
    
    try:
        from app import app
        
        if app:
            print("✓ Flask app created successfully")
            print(f"App name: {app.name}")
            print(f"Debug mode: {app.debug}")
            return True
        else:
            print("✗ Flask app creation failed")
            return False
            
    except Exception as e:
        print(f"✗ Flask app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Simple Sentiment Analysis Tool - Component Tests")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Utils Test", test_utils),
        ("Flask App Test", test_flask_app),
        ("Sentiment Analyzer Test", test_sentiment_analyzer),  # This one last as it's slow
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"Running {test_name}...")
        print(f"{'-' * 40}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        print(f"{icon} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The application should work correctly.")
        print("\nTo start the application, run:")
        print("python run.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
    
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
