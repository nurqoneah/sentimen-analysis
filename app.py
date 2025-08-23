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
import logging
import threading
from collections import defaultdict
import re

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

# Global storage for scraping logs per session
scraping_logs = defaultdict(list)
scraping_logs_lock = threading.Lock()

class ScrapingLogHandler(logging.Handler):
    """Custom log handler to capture scraping logs"""
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id

    def emit(self, record):
        try:
            # Check if this is a scraper log
            if 'scrapers.' in record.name:
                message = record.getMessage()

                # Only capture comment logs (username - comment format)
                if ' - ' in message and not any(x in message for x in ['Starting', '✓', 'Successfully', 'Error']):
                    with scraping_logs_lock:
                        scraping_logs[self.session_id].append(message)
                        # Keep only last 100 logs to prevent memory issues
                        if len(scraping_logs[self.session_id]) > 100:
                            scraping_logs[self.session_id] = scraping_logs[self.session_id][-100:]
        except Exception as e:
            # Don't let log handler errors break the scraping
            pass

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

        # Save analysis results to CSV file
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_filename = f'analysis_results_csv_{timestamp}.csv'
        results_filepath = os.path.join('data', results_filename)

        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)

        # Save results to CSV
        results.to_csv(results_filepath, index=False, encoding='utf-8')

        # Store only essential info in session
        session['analysis_id'] = session_id
        session['analysis_type'] = 'csv_upload'
        session['csv_filepath'] = results_filepath  # Path to results file
        session['original_filename'] = filename
        session['total_comments'] = len(results)
        session['timestamp'] = timestamp

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

        # Generate session ID and redirect to progress page
        session_id = str(uuid.uuid4())

        # Redirect to progress page (scraping will be done via AJAX)
        return redirect(url_for('scraping_progress', session_id=session_id, platform=platform, post_id=post_id) + f'?url={url}')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scraping_progress/<session_id>/<platform>/<post_id>')
def scraping_progress(session_id, platform, post_id):
    """Progress page for URL scraping"""
    return render_template('scraping_progress.html',
                         session_id=session_id,
                         platform=platform,
                         post_id=post_id)

@app.route('/api/scrape_and_analyze', methods=['POST'])
def api_scrape_and_analyze():
    """API endpoint to perform scraping and analysis with progress updates"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        platform = data.get('platform')
        post_id = data.get('post_id')
        url = data.get('url')

        if not all([session_id, platform, post_id, url]):
            return jsonify({'error': 'Missing required parameters'}), 400

        # Setup log handler to capture scraping logs
        log_handler = ScrapingLogHandler(session_id)
        log_handler.setLevel(logging.INFO)

        # Add handler to scrapers logger and root logger to catch all logs
        scrapers_logger = logging.getLogger('scrapers')
        scrapers_logger.addHandler(log_handler)

        # Also add to specific scraper loggers
        tiktok_logger = logging.getLogger('scrapers.tiktok_scraper_module')
        instagram_logger = logging.getLogger('scrapers.instagram_scraper_module')
        tiktok_logger.addHandler(log_handler)
        instagram_logger.addHandler(log_handler)

        try:
            # Scrape comments based on platform
            if platform == 'instagram':
                scraper = InstagramScraper()
                comments_data = scraper.scrape_comments(post_id)
            elif platform == 'tiktok':
                scraper = TikTokScraper()
                comments_data = scraper.scrape_comments(post_id)
            else:
                return jsonify({'error': 'Unsupported platform'}), 400
        finally:
            # Remove handler after scraping
            scrapers_logger.removeHandler(log_handler)
            tiktok_logger.removeHandler(log_handler)
            instagram_logger.removeHandler(log_handler)

        if not comments_data:
            return jsonify({'error': 'No comments found or scraping failed'}), 400

        # Save scraped data to CSV file first
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'scraped_data_{platform}_{post_id}_{timestamp}.csv'
        csv_filepath = os.path.join('data', csv_filename)

        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)

        # Save to CSV
        df_scraped = pd.DataFrame(comments_data)
        df_scraped.to_csv(csv_filepath, index=False, encoding='utf-8')

        # Analyze sentiment from the saved CSV
        results = sentiment_analyzer.analyze_dataframe(df_scraped)

        # Save analysis results to another CSV
        results_filename = f'analysis_results_{platform}_{post_id}_{timestamp}.csv'
        results_filepath = os.path.join('data', results_filename)
        results.to_csv(results_filepath, index=False, encoding='utf-8')

        # Store results in session
        session['analysis_id'] = session_id
        session['analysis_type'] = 'url_scraping'
        session['csv_filepath'] = results_filepath
        session['scraped_csv_filepath'] = csv_filepath
        session['platform'] = platform
        session['post_id'] = post_id
        session['original_url'] = url
        session['total_comments'] = len(results)
        session['timestamp'] = timestamp

        # Get captured logs
        with scraping_logs_lock:
            captured_logs = scraping_logs.get(session_id, [])
            # Clear logs after sending
            if session_id in scraping_logs:
                del scraping_logs[session_id]

        return jsonify({
            'success': True,
            'total_comments': len(results),
            'results_preview': results.head(5).to_dict('records'),
            'scraped_comments': captured_logs  # Send captured logs
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scraping_logs/<session_id>')
def api_scraping_logs(session_id):
    """API endpoint to get scraping logs for a session"""
    with scraping_logs_lock:
        logs = scraping_logs.get(session_id, [])
        # Return logs without clearing them (for real-time updates)
        return jsonify({'logs': logs})

@app.route('/results')
def results():
    """Results page showing analysis summary and action buttons"""
    if 'analysis_id' not in session:
        return redirect(url_for('index'))

    analysis_type = session.get('analysis_type')

    # Handle different analysis types
    if analysis_type == 'single_text':
        analysis_data = session.get('analysis_data')
        if not analysis_data:
            return redirect(url_for('index'))

        summary = {
            'total_items': 1,
            'sentiment_distribution': {
                analysis_data['sentiment_label']: 1
            }
        }
    elif analysis_type in ['csv_upload', 'url_scraping']:
        # For CSV and URL scraping, read data from file
        csv_filepath = session.get('csv_filepath')
        if not csv_filepath or not os.path.exists(csv_filepath):
            return redirect(url_for('index'))

        try:
            df = pd.read_csv(csv_filepath)
            summary = {
                'total_items': len(df),
                'sentiment_distribution': df['sentiment_label'].value_counts().to_dict()
            }
        except Exception as e:
            return jsonify({'error': f'Error reading analysis results: {str(e)}'}), 500
    else:
        return redirect(url_for('index'))
    
    return render_template('results.html', 
                         analysis_type=analysis_type,
                         summary=summary,
                         session_data=session)

@app.route('/visualizations')
def visualizations():
    """Interactive visualizations page"""
    if 'analysis_id' not in session:
        return redirect(url_for('index'))

    analysis_type = session.get('analysis_type')

    if analysis_type == 'single_text':
        # For single text, show simple result
        analysis_data = session.get('analysis_data')
        if not analysis_data:
            return redirect(url_for('index'))
        return render_template('single_result.html', data=analysis_data)

    # For CSV and URL scraping, read data from file
    csv_filepath = session.get('csv_filepath')
    if not csv_filepath or not os.path.exists(csv_filepath):
        return redirect(url_for('index'))

    try:
        # Read data from CSV file
        df = pd.read_csv(csv_filepath)
        charts = create_visualizations(df, analysis_type)

        return render_template('visualizations.html',
                             charts=charts,
                             analysis_type=analysis_type)
    except Exception as e:
        return jsonify({'error': f'Error reading analysis data: {str(e)}'}), 500
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
    if 'analysis_id' not in session:
        return redirect(url_for('index'))

    analysis_type = session.get('analysis_type')

    if analysis_type == 'single_text':
        # For single text, create DataFrame from session data
        analysis_data = session.get('analysis_data')
        if not analysis_data:
            return redirect(url_for('index'))
        df = pd.DataFrame([analysis_data])
    else:
        # For CSV and URL scraping, read from existing file
        csv_filepath = session.get('csv_filepath')
        if not csv_filepath or not os.path.exists(csv_filepath):
            return redirect(url_for('index'))

        try:
            df = pd.read_csv(csv_filepath)
        except Exception as e:
            return jsonify({'error': f'Error reading analysis data: {str(e)}'}), 500

    # Generate filename for export
    timestamp = session.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S'))
    filename = f'sentiment_analysis_{analysis_type}_{timestamp}.csv'
    filepath = os.path.join('static/exports', filename)

    # Ensure exports directory exists
    os.makedirs('static/exports', exist_ok=True)

    # Save CSV for download
    df.to_csv(filepath, index=False, encoding='utf-8')

    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/api/wordcloud')
def api_wordcloud():
    """API endpoint for word cloud data"""
    if 'analysis_id' not in session:
        return jsonify({'error': 'No analysis data found'}), 400

    analysis_type = session.get('analysis_type')

    if analysis_type == 'single_text':
        return jsonify({'error': 'Word cloud not available for single text analysis'}), 400

    # Read data from CSV file
    csv_filepath = session.get('csv_filepath')
    if not csv_filepath or not os.path.exists(csv_filepath):
        return jsonify({'error': 'Analysis data file not found'}), 400

    try:
        from wordcloud_generator import generate_wordcloud_data

        df = pd.read_csv(csv_filepath)
        wordcloud_data = generate_wordcloud_data(df)

        return jsonify(wordcloud_data)
    except Exception as e:
        return jsonify({'error': f'Error generating word cloud: {str(e)}'}), 500

@app.route('/api/results_preview')
def api_results_preview():
    """API endpoint for results preview data"""
    if 'analysis_id' not in session:
        return jsonify({'error': 'No analysis data found'}), 400

    analysis_type = session.get('analysis_type')

    if analysis_type == 'single_text':
        return jsonify({'error': 'Preview not available for single text analysis'}), 400

    # Read data from CSV file
    csv_filepath = session.get('csv_filepath')
    if not csv_filepath or not os.path.exists(csv_filepath):
        return jsonify({'error': 'Analysis data file not found'}), 400

    try:
        df = pd.read_csv(csv_filepath)
        preview_data = df.head(5).to_dict('records')

        return jsonify({
            'preview': preview_data,
            'total': len(df)
        })
    except Exception as e:
        return jsonify({'error': f'Error loading preview: {str(e)}'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
