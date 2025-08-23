# Installation Guide

## Quick Start

### Option 1: Using start.py (Recommended)
```bash
python start.py
```

### Option 2: Using run.py
```bash
python run.py
```

### Option 3: Direct Flask run
```bash
python app.py
```

## Detailed Installation Steps

### 1. Prerequisites
- Python 3.8 or higher
- pip package manager
- At least 4GB RAM (for model loading)
- Internet connection (for first-time model download)

### 2. Install Dependencies

#### Core Dependencies
```bash
pip install flask
pip install transformers
pip install torch
pip install pandas
pip install plotly
pip install wordcloud
pip install requests
pip install loguru
pip install jmespath
pip install click
```

#### Or install all at once
```bash
pip install flask transformers torch pandas plotly wordcloud requests loguru jmespath click
```

### 3. Verify Installation
Run the test script to check if everything is working:
```bash
python test_app.py
```

### 4. Start the Application
```bash
python start.py
```

The application will be available at: http://localhost:5002

## Troubleshooting

### Common Issues

#### 1. PowerShell Execution Policy (Windows)
If you see execution policy errors, run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. Model Download Issues
On first run, the application downloads the sentiment analysis model (~500MB). This requires:
- Stable internet connection
- Sufficient disk space
- Patience (may take 5-10 minutes)

#### 3. Memory Issues
If you encounter memory errors:
- Close other applications
- Use smaller batch sizes for CSV files
- Consider using CPU-only mode

#### 4. Port Already in Use
If port 5002 is busy, modify the port in `start.py`:
```python
app.run(host='0.0.0.0', port=5003, debug=True)  # Change to 5003 or any available port
```

#### 5. Import Errors
If you see import errors, ensure all dependencies are installed:
```bash
python -c "import flask, transformers, torch, pandas, plotly, wordcloud, requests, loguru, jmespath"
```

### Testing with Sample Data

1. Use the provided `sample_data.csv` file to test CSV upload functionality
2. Try single text analysis with: "I love this product!"
3. Test URL scraping with valid Instagram/TikTok URLs

### Performance Tips

1. **First Run**: The first analysis will be slow due to model download and initialization
2. **Subsequent Runs**: Much faster as models are cached locally
3. **Large Files**: Process CSV files with <1000 rows for optimal performance
4. **Memory**: Close browser tabs and other applications if running low on memory

### Development Mode

To run in development mode with auto-reload:
```bash
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows
python app.py
```

### Production Deployment

For production deployment:
1. Set environment variables:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secret-key-here
   ```
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

## File Structure After Installation

```
sentiment-analysis/
├── app.py                    # Main application
├── start.py                  # Simple startup script
├── run.py                    # Advanced startup script
├── test_app.py              # Test script
├── sample_data.csv          # Sample data for testing
├── requirements.txt         # Dependencies
├── README.md               # Main documentation
├── INSTALL.md              # This file
├── config.py               # Configuration
├── sentiment_analyzer.py   # AI model handler
├── visualizations.py       # Chart generation
├── wordcloud_generator.py  # Word cloud creation
├── utils.py                # Utility functions
├── scrapers/               # Social media scrapers
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── uploads/                # Temporary uploads (created automatically)
├── data/                   # Data storage (created automatically)
└── static/exports/         # Export files (created automatically)
```

## Next Steps

After successful installation:
1. Open http://localhost:5002 in your browser
2. Try the three analysis methods
3. Explore the interactive visualizations
4. Export your results

## Support

If you encounter issues:
1. Run `python test_app.py` to diagnose problems
2. Check the console output for error messages
3. Ensure all dependencies are properly installed
4. Verify you have sufficient system resources
