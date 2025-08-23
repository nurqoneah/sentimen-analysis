"""
Word Cloud Generator for Sentiment Analysis
"""

import pandas as pd
import numpy as np
from wordcloud import WordCloud
import base64
from io import BytesIO
import re
from collections import Counter
import matplotlib.pyplot as plt

def generate_wordcloud_data(df):
    """
    Generate word cloud data for overall and per-sentiment analysis
    
    Args:
        df (pandas.DataFrame): DataFrame with sentiment analysis results
        
    Returns:
        dict: Dictionary containing word cloud data
    """
    wordcloud_data = {}
    
    # Overall word cloud
    wordcloud_data['overall'] = create_wordcloud_image(df, 'Overall Comments')
    
    # Per-sentiment word clouds
    for sentiment in df['sentiment_label'].unique():
        sentiment_df = df[df['sentiment_label'] == sentiment]
        wordcloud_data[sentiment] = create_wordcloud_image(
            sentiment_df, 
            f'{sentiment.title()} Comments'
        )
    
    return wordcloud_data

def create_wordcloud_image(df, title):
    """
    Create word cloud image from DataFrame
    
    Args:
        df (pandas.DataFrame): DataFrame containing comment text
        title (str): Title for the word cloud
        
    Returns:
        dict: Dictionary with image data and statistics
    """
    if df.empty:
        return {
            'image': None,
            'word_count': 0,
            'top_words': []
        }
    
    # Combine all text
    text = ' '.join(df['comment_text'].fillna('').astype(str))
    
    # Clean and process text
    cleaned_text = clean_text_for_wordcloud(text)
    
    if not cleaned_text.strip():
        return {
            'image': None,
            'word_count': 0,
            'top_words': []
        }
    
    # Create word cloud
    try:
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            max_words=100,
            colormap='viridis',
            relative_scaling=0.5,
            min_font_size=10
        ).generate(cleaned_text)
        
        # Convert to base64 image
        img_buffer = BytesIO()
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(title, fontsize=16, fontweight='bold')
        plt.tight_layout(pad=0)
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        plt.close()
        
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Get word frequencies
        word_freq = wordcloud.words_
        top_words = list(word_freq.items())[:10]
        
        return {
            'image': f'data:image/png;base64,{img_base64}',
            'word_count': len(word_freq),
            'top_words': top_words
        }
        
    except Exception as e:
        print(f"Error creating word cloud: {e}")
        return {
            'image': None,
            'word_count': 0,
            'top_words': [],
            'error': str(e)
        }

def clean_text_for_wordcloud(text):
    """
    Clean text for word cloud generation
    
    Args:
        text (str): Raw text to clean
        
    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove mentions and hashtags (optional - you might want to keep hashtags)
    text = re.sub(r'@\w+', '', text)
    # text = re.sub(r'#\w+', '', text)  # Uncomment to remove hashtags
    
    # Remove special characters but keep letters, numbers, and spaces
    text = re.sub(r'[^a-zA-Z0-9\s#]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
        'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 
        'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'this', 'that',
        'with', 'have', 'will', 'your', 'from', 'they', 'know', 'want', 'been',
        'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just',
        'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them',
        'well', 'were', 'what', 'would', 'there', 'could', 'other', 'after',
        'first', 'never', 'these', 'think', 'where', 'being', 'every', 'great',
        'might', 'shall', 'still', 'those', 'under', 'while', 'about', 'before',
        'should', 'through', 'during', 'follow', 'around', 'really', 'something'
    }
    
    # Filter out stop words
    words = text.split()
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    return ' '.join(filtered_words)

def get_word_frequencies(df, sentiment=None):
    """
    Get word frequencies for a DataFrame
    
    Args:
        df (pandas.DataFrame): DataFrame with comment text
        sentiment (str, optional): Filter by sentiment
        
    Returns:
        list: List of (word, frequency) tuples
    """
    if sentiment:
        df = df[df['sentiment_label'] == sentiment]
    
    if df.empty:
        return []
    
    # Combine all text
    text = ' '.join(df['comment_text'].fillna('').astype(str))
    
    # Clean text
    cleaned_text = clean_text_for_wordcloud(text)
    
    # Get word frequencies
    words = cleaned_text.split()
    word_freq = Counter(words)
    
    return word_freq.most_common(50)

def create_simple_wordcloud_data(df):
    """
    Create simple word cloud data without images (for API responses)
    
    Args:
        df (pandas.DataFrame): DataFrame with sentiment analysis results
        
    Returns:
        dict: Dictionary containing word frequency data
    """
    wordcloud_data = {}
    
    # Overall word frequencies
    wordcloud_data['overall'] = get_word_frequencies(df)
    
    # Per-sentiment word frequencies
    for sentiment in df['sentiment_label'].unique():
        wordcloud_data[sentiment] = get_word_frequencies(df, sentiment)
    
    return wordcloud_data
