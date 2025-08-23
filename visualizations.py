"""
Visualization module for sentiment analysis results
Creates interactive Plotly charts
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime
import numpy as np

def create_visualizations(df, analysis_type='csv_upload'):
    """
    Create all visualizations for sentiment analysis results
    
    Args:
        df (pandas.DataFrame): DataFrame with sentiment analysis results
        analysis_type (str): Type of analysis performed
        
    Returns:
        dict: Dictionary containing all chart JSON data
    """
    charts = {}
    
    if df.empty:
        return charts
    
    # 1. Sentiment Distribution Chart
    charts['sentiment_distribution'] = create_sentiment_distribution_chart(df)
    
    # 2. Confidence Score Distribution
    charts['confidence_distribution'] = create_confidence_distribution_chart(df)
    
    # 3. Sentiment vs Confidence Scatter Plot
    charts['sentiment_confidence_scatter'] = create_sentiment_confidence_scatter(df)
    
    # 4. Platform Comparison (if platform data exists)
    if 'platform' in df.columns or analysis_type == 'url_scraping':
        charts['platform_comparison'] = create_platform_comparison_chart(df)
    
    # 5. Time-based analysis (if timestamp data exists)
    if 'created_at' in df.columns:
        charts['time_trends'] = create_time_trends_chart(df)
    
    # 6. Top Words by Sentiment (basic version)
    charts['word_frequency'] = create_word_frequency_chart(df)
    
    return charts

def create_sentiment_distribution_chart(df):
    """Create sentiment distribution bar chart"""
    sentiment_counts = df['sentiment_label'].value_counts()
    
    # Define colors for sentiments
    colors = {
        'positive': '#2E8B57',  # Sea Green
        'negative': '#DC143C',  # Crimson
        'neutral': '#4682B4'    # Steel Blue
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=sentiment_counts.index,
            y=sentiment_counts.values,
            marker_color=[colors.get(sentiment, '#808080') for sentiment in sentiment_counts.index],
            text=sentiment_counts.values,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title='Sentiment Distribution',
        xaxis_title='Sentiment',
        yaxis_title='Number of Comments',
        template='plotly_white',
        height=400
    )
    
    return json.loads(fig.to_json())

def create_confidence_distribution_chart(df):
    """Create confidence score distribution box plot"""
    fig = go.Figure()
    
    colors = {
        'positive': '#2E8B57',
        'negative': '#DC143C', 
        'neutral': '#4682B4'
    }
    
    for sentiment in df['sentiment_label'].unique():
        sentiment_data = df[df['sentiment_label'] == sentiment]['sentiment_score']
        
        fig.add_trace(go.Box(
            y=sentiment_data,
            name=sentiment.title(),
            marker_color=colors.get(sentiment, '#808080'),
            boxpoints='outliers'
        ))
    
    fig.update_layout(
        title='Confidence Score Distribution by Sentiment',
        xaxis_title='Sentiment',
        yaxis_title='Confidence Score',
        template='plotly_white',
        height=400
    )
    
    return json.loads(fig.to_json())

def create_sentiment_confidence_scatter(df):
    """Create scatter plot of comment length vs confidence score"""
    # Calculate comment length
    df_copy = df.copy()
    df_copy['comment_length'] = df_copy['comment_text'].str.len()
    
    colors = {
        'positive': '#2E8B57',
        'negative': '#DC143C',
        'neutral': '#4682B4'
    }
    
    fig = go.Figure()
    
    for sentiment in df_copy['sentiment_label'].unique():
        sentiment_data = df_copy[df_copy['sentiment_label'] == sentiment]
        
        fig.add_trace(go.Scatter(
            x=sentiment_data['comment_length'],
            y=sentiment_data['sentiment_score'],
            mode='markers',
            name=sentiment.title(),
            marker=dict(
                color=colors.get(sentiment, '#808080'),
                size=8,
                opacity=0.6
            ),
            text=sentiment_data['comment_text'].str[:100] + '...',
            hovertemplate='<b>%{text}</b><br>Length: %{x}<br>Confidence: %{y:.3f}<extra></extra>'
        ))
    
    fig.update_layout(
        title='Comment Length vs Confidence Score',
        xaxis_title='Comment Length (characters)',
        yaxis_title='Confidence Score',
        template='plotly_white',
        height=400
    )
    
    return json.loads(fig.to_json())

def create_platform_comparison_chart(df):
    """Create platform comparison chart if platform data exists"""
    if 'platform' not in df.columns:
        # If no platform column, create one based on post_id patterns
        df_copy = df.copy()
        df_copy['platform'] = 'Unknown'
        return json.loads(go.Figure().to_json())
    
    platform_sentiment = df.groupby(['platform', 'sentiment_label']).size().unstack(fill_value=0)
    
    fig = go.Figure()
    
    colors = {
        'positive': '#2E8B57',
        'negative': '#DC143C',
        'neutral': '#4682B4'
    }
    
    for sentiment in platform_sentiment.columns:
        fig.add_trace(go.Bar(
            name=sentiment.title(),
            x=platform_sentiment.index,
            y=platform_sentiment[sentiment],
            marker_color=colors.get(sentiment, '#808080')
        ))
    
    fig.update_layout(
        title='Sentiment Distribution by Platform',
        xaxis_title='Platform',
        yaxis_title='Number of Comments',
        barmode='group',
        template='plotly_white',
        height=400
    )
    
    return json.loads(fig.to_json())

def create_time_trends_chart(df):
    """Create time-based sentiment trends"""
    if 'created_at' not in df.columns:
        return json.loads(go.Figure().to_json())
    
    df_copy = df.copy()
    
    # Convert timestamps to datetime
    try:
        # Handle different timestamp formats
        df_copy['datetime'] = pd.to_datetime(df_copy['created_at'], unit='s', errors='coerce')
        if df_copy['datetime'].isna().all():
            df_copy['datetime'] = pd.to_datetime(df_copy['created_at'], errors='coerce')
    except:
        return json.loads(go.Figure().to_json())
    
    # Remove rows with invalid dates
    df_copy = df_copy.dropna(subset=['datetime'])
    
    if df_copy.empty:
        return json.loads(go.Figure().to_json())
    
    # Group by hour and sentiment
    df_copy['hour'] = df_copy['datetime'].dt.floor('H')
    hourly_sentiment = df_copy.groupby(['hour', 'sentiment_label']).size().unstack(fill_value=0)
    
    fig = go.Figure()
    
    colors = {
        'positive': '#2E8B57',
        'negative': '#DC143C',
        'neutral': '#4682B4'
    }
    
    for sentiment in hourly_sentiment.columns:
        fig.add_trace(go.Scatter(
            x=hourly_sentiment.index,
            y=hourly_sentiment[sentiment],
            mode='lines+markers',
            name=sentiment.title(),
            line=dict(color=colors.get(sentiment, '#808080'))
        ))
    
    fig.update_layout(
        title='Sentiment Trends Over Time',
        xaxis_title='Time',
        yaxis_title='Number of Comments',
        template='plotly_white',
        height=400
    )
    
    return json.loads(fig.to_json())

def create_word_frequency_chart(df):
    """Create simple word frequency chart"""
    from collections import Counter
    import re
    
    # Combine all comments
    all_text = ' '.join(df['comment_text'].fillna('').astype(str))
    
    # Simple word extraction (basic tokenization)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
    
    # Remove common stop words
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
    words = [word for word in words if word not in stop_words]
    
    # Get top 20 words
    word_counts = Counter(words).most_common(20)
    
    if not word_counts:
        return json.loads(go.Figure().to_json())
    
    words, counts = zip(*word_counts)
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(counts),
            y=list(words),
            orientation='h',
            marker_color='#4682B4'
        )
    ])
    
    fig.update_layout(
        title='Top 20 Most Frequent Words',
        xaxis_title='Frequency',
        yaxis_title='Words',
        template='plotly_white',
        height=500,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return json.loads(fig.to_json())
