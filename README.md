# Simple Social Media Sentiment Analysis Tool

A Flask-based web application for analyzing sentiment from text, CSV files, and social media URLs (Instagram & TikTok).

## Features

### 🎯 Three Analysis Methods
- **Single Text Analysis**: Analyze individual text snippets instantly
- **CSV Upload Analysis**: Batch process comments from CSV files
- **URL Scraping Analysis**: Extract and analyze comments from Instagram and TikTok posts

### 📊 Interactive Visualizations
- Sentiment distribution charts
- Confidence score analysis
- Time-based sentiment trends
- Platform comparison charts
- Word frequency analysis
- Word clouds (overall and per-sentiment)

### 🚀 Key Capabilities
- **AI-Powered**: Uses Hugging Face's `cardiffnlp/twitter-roberta-base-sentiment-latest` model
- **Real-time Processing**: Instant sentiment analysis with confidence scores
- **Export Functionality**: Download results as CSV files
- **Responsive Design**: Modern, mobile-friendly interface
- **Interactive Charts**: Powered by Plotly.js

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sentiment-analysis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python run.py
   ```

4. **Access the application**
   Open your browser and go to `http://localhost:5002`

## Usage

### Single Text Analysis
1. Navigate to the home page
2. Enter your text in the "Single Text Analysis" section
3. Click "Analyze Sentiment"
4. View results with confidence scores

### CSV Upload Analysis
1. Prepare a CSV file with a `comment_text` column
2. Upload the file using the "CSV Upload Analysis" section
3. View comprehensive analysis and visualizations
4. Export results or generate word clouds

### URL Scraping Analysis
1. Copy an Instagram or TikTok post URL
2. Select the platform and paste the URL
3. Click "Scrape & Analyze"
4. Explore interactive visualizations and insights

#### Supported URL Formats
- **Instagram**: `https://www.instagram.com/p/POST_ID/`
- **TikTok**: `https://www.tiktok.com/@username/video/VIDEO_ID`

## Project Structure

```
sentiment-analysis/
├── app.py                          # Main Flask application
├── run.py                          # Application runner
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── sentiment_analyzer.py           # Sentiment analysis module
├── visualizations.py               # Chart generation
├── wordcloud_generator.py          # Word cloud creation
├── utils.py                        # Utility functions
├── scrapers/                       # Social media scrapers
│   ├── __init__.py
│   ├── instagram_scraper_module.py
│   └── tiktok_scraper_module.py
├── templates/                      # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── results.html
│   ├── visualizations.html
│   ├── single_result.html
│   ├── 404.html
│   └── 500.html
├── static/                         # Static assets
│   └── css/
│       └── style.css
├── uploads/                        # Temporary file uploads
├── data/                          # Data storage
└── static/exports/                # Export files
```

## Configuration

### Environment Variables
For production deployment, set these environment variables:

```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
HOST=0.0.0.0
PORT=5000

# Instagram scraper credentials (optional)
INSTAGRAM_SESSIONID=your-session-id
INSTAGRAM_DS_USER_ID=your-user-id
INSTAGRAM_CSRFTOKEN=your-csrf-token
INSTAGRAM_MID=your-mid
```

### Model Configuration
The application uses Hugging Face models:
- Primary: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- Fallback: `cardiffnlp/twitter-roberta-base-sentiment`

## API Endpoints

- `GET /` - Home page
- `POST /analyze_text` - Single text analysis
- `POST /analyze_csv` - CSV file analysis
- `POST /analyze_url` - URL scraping analysis
- `GET /results` - Analysis results page
- `GET /visualizations` - Interactive charts
- `GET /export` - Download CSV results
- `GET /api/wordcloud` - Word cloud data API

## Dependencies

### Core Dependencies
- **Flask**: Web framework
- **transformers**: Hugging Face model integration
- **torch**: PyTorch for model inference
- **pandas**: Data manipulation
- **plotly**: Interactive visualizations
- **wordcloud**: Word cloud generation

### Scraping Dependencies
- **requests**: HTTP requests
- **loguru**: Logging
- **jmespath**: JSON parsing
- **click**: CLI interface

## Troubleshooting

### Common Issues

1. **Model Loading Errors**
   - Ensure stable internet connection for first-time model download
   - Models are cached locally after first use

2. **Scraping Issues**
   - Instagram scraping requires valid session cookies
   - TikTok API may have rate limits
   - Some posts may be private or restricted

3. **Memory Issues**
   - Large CSV files may require more RAM
   - Consider processing in smaller batches

### Performance Tips
- Use CPU-only mode for better compatibility
- Process large datasets in smaller chunks
- Clear browser cache if visualizations don't load

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Hugging Face for the sentiment analysis models
- Plotly for interactive visualizations
- Bootstrap for responsive UI components
- Font Awesome for icons

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information

---

**Note**: This tool is for educational and research purposes. Ensure compliance with platform terms of service when scraping social media content.
