"""
Configuration file for the sentiment analysis application
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Model settings
    SENTIMENT_MODEL = 'cardiffnlp/twitter-roberta-base-sentiment-latest'
    FALLBACK_MODEL = 'cardiffnlp/twitter-roberta-base-sentiment'
    
    # Scraper settings
    SCRAPER_TIMEOUT = 30
    SCRAPER_DELAY = 2  # seconds between requests
    MAX_COMMENTS_PER_REQUEST = 50
    
    # Export settings
    EXPORT_FOLDER = 'static/exports'
    
    # Visualization settings
    CHART_HEIGHT = 400
    CHART_WIDTH = 800
    
    # Word cloud settings
    WORDCLOUD_WIDTH = 800
    WORDCLOUD_HEIGHT = 400
    WORDCLOUD_MAX_WORDS = 100
    
    # Instagram scraper settings (should be moved to environment variables in production)
    INSTAGRAM_COOKIES = {
        'sessionid': '8900711295%3ACOeDeSGecWNZLK%3A9%3AAYf0g_IpxxhTmgjuUWX7Ne8gVjqUAi3KJJRehaD04Q',
        'ds_user_id': '8900711295',
        'csrftoken': 'E5VPI5indmbps5COiHI7DI2LeH7vLA40',
        'mid': 'aHSP6wALAAEGbmMHO65q6keKTGUT'
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Override with environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Use environment variables for sensitive data
    INSTAGRAM_COOKIES = {
        'sessionid': os.environ.get('INSTAGRAM_SESSIONID'),
        'ds_user_id': os.environ.get('INSTAGRAM_DS_USER_ID'),
        'csrftoken': os.environ.get('INSTAGRAM_CSRFTOKEN'),
        'mid': os.environ.get('INSTAGRAM_MID')
    }

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
