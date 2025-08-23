"""
Simple Social Media Sentiment Analysis Tool
Flask application for analyzing sentiment from text, CSV files, and social media URLs
"""

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import os
import pandas as pd
import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import tempfile

# Import custom modules (will be created)
from sentiment_analyzer import SentimentAnalyzer
from scrapers.instagram_scraper_module import InstagramScraper
from scrapers.tiktok_scraper_module import TikTokScraper
from visualizations import create_visualizations
from utils import extract_post_id, allowed_file

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('static/exports', exist_ok=True)

# Initialize sentiment analyzer
sentiment_analyzer = SentimentAnalyzer()

@app.route('/')
def index():
    """Home page with three analysis options"""
    return render_template('index.html')

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    """Analyze single text input"""
    try:
        text = request.form.get('text', '').strip()
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Analyze sentiment
        result = sentiment_analyzer.analyze_single_text(text)
        
        # Store result in session for results page
        session_id = str(uuid.uuid4())
        session['analysis_id'] = session_id
        session['analysis_type'] = 'single_text'
        session['analysis_data'] = {
            'text': text,
            'sentiment_label': result['sentiment_label'],
            'sentiment_score': result['sentiment_score'],
            'timestamp': datetime.now().isoformat()
        }
        
        return redirect(url_for('results'))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_csv', methods=['POST'])
def analyze_csv():
    """Analyze CSV file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a CSV file.'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read and validate CSV
        df = pd.read_csv(filepath)
        if 'comment_text' not in df.columns:
            return jsonify({'error': 'CSV must contain a "comment_text" column'}), 400
        
        # Analyze sentiment for all comments
        results = sentiment_analyzer.analyze_dataframe(df)
        
        # Store results in session
        session_id = str(uuid.uuid4())
        session['analysis_id'] = session_id
        session['analysis_type'] = 'csv_upload'
        session['analysis_data'] = results.to_dict('records')
        session['original_filename'] = filename
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return redirect(url_for('results'))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_url', methods=['POST'])
def analyze_url():
    """Analyze social media URL"""
    try:
        url = request.form.get('url', '').strip()
        platform = request.form.get('platform', '').lower()
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Extract post ID from URL
        post_id = extract_post_id(url, platform)
        if not post_id:
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Scrape comments based on platform
        if platform == 'instagram':
            scraper = InstagramScraper()
            comments_data = scraper.scrape_comments(post_id)
        elif platform == 'tiktok':
            scraper = TikTokScraper()
            comments_data = scraper.scrape_comments(post_id)
        else:
            return jsonify({'error': 'Unsupported platform'}), 400
        
        if not comments_data:
            return jsonify({'error': 'No comments found or scraping failed'}), 400
        
        # Convert to DataFrame and analyze sentiment
        df = pd.DataFrame(comments_data)
        results = sentiment_analyzer.analyze_dataframe(df)
        
        # Store results in session
        session_id = str(uuid.uuid4())
        session['analysis_id'] = session_id
        session['analysis_type'] = 'url_scraping'
        session['analysis_data'] = results.to_dict('records')
        session['platform'] = platform
        session['post_id'] = post_id
        session['original_url'] = url
        
        return redirect(url_for('results'))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results():
    """Results page showing analysis summary and action buttons"""
    if 'analysis_id' not in session:
        return redirect(url_for('index'))
    
    analysis_type = session.get('analysis_type')
    analysis_data = session.get('analysis_data')
    
    if not analysis_data:
        return redirect(url_for('index'))
    
    # Calculate summary statistics
    if analysis_type == 'single_text':
        summary = {
            'total_items': 1,
            'sentiment_distribution': {
                analysis_data['sentiment_label']: 1
            }
        }
    else:
        df = pd.DataFrame(analysis_data)
        summary = {
            'total_items': len(df),
            'sentiment_distribution': df['sentiment_label'].value_counts().to_dict()
        }
    
    return render_template('results.html', 
                         analysis_type=analysis_type,
                         summary=summary,
                         session_data=session)

@app.route('/visualizations')
def visualizations():
    """Interactive visualizations page"""
    if 'analysis_id' not in session or 'analysis_data' not in session:
        return redirect(url_for('index'))
    
    analysis_data = session.get('analysis_data')
    analysis_type = session.get('analysis_type')
    
    if analysis_type == 'single_text':
        # For single text, show simple result
        return render_template('single_result.html', data=analysis_data)
    
    # Create visualizations for multi-item data
    df = pd.DataFrame(analysis_data)
    charts = create_visualizations(df, analysis_type)
    
    return render_template('visualizations.html', 
                         charts=charts,
                         analysis_type=analysis_type)
@app.route('/download_template')
def download_template():
    """Download CSV template for upload"""
    import io
    import csv
    from flask import make_response
    
    # Create sample CSV data
    template_data = [
        ['comment_text', 'username', 'created_at', 'post_id'],
        ['Saya sangat senang dengan produk ini! Mantap banget!', 'user_1', '1/1/2024 10:00', 'post_1'],
        ['Produk ini tidak sesuai ekspektasi. Kecewa sekali.', 'user_2', '1/1/2024 11:30', 'post_2'],
        ['Biasa saja, tidak ada yang istimewa tapi masih bisa dipakai.', 'user_3', '1/1/2024 12:15', 'post_3'],
        ['Luar biasa! Sangat merekomendasikan produk ini.', 'user_4', '1/1/2024 13:45', 'post_4'],
        ['Harga terlalu mahal untuk kualitas seperti ini.', 'user_5', '1/1/2024 14:20', 'post_5']
    ]
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(template_data)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=template_sentiment_analysis.csv'
    
    return response

@app.route('/export')
def export_results():
    """Export analysis results as CSV"""
    if 'analysis_id' not in session or 'analysis_data' not in session:
        return redirect(url_for('index'))
    
    analysis_data = session.get('analysis_data')
    analysis_type = session.get('analysis_type')
    
    # Create DataFrame
    if analysis_type == 'single_text':
        df = pd.DataFrame([analysis_data])
    else:
        df = pd.DataFrame(analysis_data)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'sentiment_analysis_{analysis_type}_{timestamp}.csv'
    filepath = os.path.join('static/exports', filename)
    
    # Save CSV
    df.to_csv(filepath, index=False)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/api/wordcloud')
def api_wordcloud():
    """API endpoint for word cloud data"""
    if 'analysis_data' not in session:
        return jsonify({'error': 'No analysis data found'}), 400
    
    analysis_data = session.get('analysis_data')
    analysis_type = session.get('analysis_type')
    
    if analysis_type == 'single_text':
        return jsonify({'error': 'Word cloud not available for single text analysis'}), 400
    
    from wordcloud_generator import generate_wordcloud_data
    
    df = pd.DataFrame(analysis_data)
    wordcloud_data = generate_wordcloud_data(df)
    
    return jsonify(wordcloud_data)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
