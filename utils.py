"""
Utility functions for the sentiment analysis application
"""

import re
import os
from urllib.parse import urlparse

def extract_post_id(url, platform):
    """
    Extract post ID from social media URLs
    
    Args:
        url (str): The social media URL
        platform (str): Platform type ('instagram' or 'tiktok')
    
    Returns:
        str: Extracted post ID or None if invalid
    """
    if platform == 'instagram':
        # Instagram URL patterns:
        # https://www.instagram.com/p/DNcgnWvRJ9-/
        # https://instagram.com/p/DNcgnWvRJ9-/
        pattern = r'instagram\.com/p/([A-Za-z0-9_-]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    elif platform == 'tiktok':
        # TikTok URL patterns:
        # https://www.tiktok.com/@username/video/7539605848159489286
        # https://tiktok.com/@username/video/7539605848159489286
        pattern = r'tiktok\.com/@[^/]+/video/(\d+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    return None

def allowed_file(filename):
    """
    Check if uploaded file has allowed extension
    
    Args:
        filename (str): Name of the uploaded file
    
    Returns:
        bool: True if file extension is allowed
    """
    ALLOWED_EXTENSIONS = {'csv'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_csv_structure(df):
    """
    Validate that CSV has required columns
    
    Args:
        df (pandas.DataFrame): The uploaded CSV data
    
    Returns:
        tuple: (is_valid, error_message)
    """
    required_columns = ['comment_text']
    
    if df.empty:
        return False, "CSV file is empty"
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Check if comment_text column has any non-empty values
    if df['comment_text'].dropna().empty:
        return False, "No valid comments found in 'comment_text' column"
    
    return True, None

def clean_text(text):
    """
    Clean text for sentiment analysis
    
    Args:
        text (str): Raw text to clean
    
    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove mentions and hashtags for cleaner analysis (optional)
    # text = re.sub(r'@\w+|#\w+', '', text)
    
    return text.strip()

def format_timestamp(timestamp):
    """
    Format timestamp for display
    
    Args:
        timestamp: Unix timestamp or datetime string
    
    Returns:
        str: Formatted timestamp
    """
    from datetime import datetime
    
    if isinstance(timestamp, (int, float)):
        # Unix timestamp
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(timestamp, str):
        try:
            # Try to parse ISO format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
    else:
        return str(timestamp)

def get_platform_from_url(url):
    """
    Detect platform from URL
    
    Args:
        url (str): Social media URL
    
    Returns:
        str: Platform name ('instagram', 'tiktok', or None)
    """
    if 'instagram.com' in url.lower():
        return 'instagram'
    elif 'tiktok.com' in url.lower():
        return 'tiktok'
    return None

def safe_filename(filename):
    """
    Create a safe filename for exports
    
    Args:
        filename (str): Original filename
    
    Returns:
        str: Safe filename
    """
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    return filename

def calculate_sentiment_stats(df):
    """
    Calculate sentiment statistics from DataFrame
    
    Args:
        df (pandas.DataFrame): DataFrame with sentiment analysis results
    
    Returns:
        dict: Statistics dictionary
    """
    if df.empty:
        return {}
    
    stats = {
        'total_comments': len(df),
        'sentiment_distribution': df['sentiment_label'].value_counts().to_dict(),
        'average_confidence': df['sentiment_score'].mean(),
        'confidence_by_sentiment': df.groupby('sentiment_label')['sentiment_score'].mean().to_dict()
    }
    
    # Calculate percentages
    total = stats['total_comments']
    stats['sentiment_percentages'] = {
        sentiment: (count / total) * 100 
        for sentiment, count in stats['sentiment_distribution'].items()
    }
    
    return stats
