"""
Sentiment Analysis Module
Uses Hugging Face w11wo/indonesian-roberta-base-sentiment-classifier-latest model
"""

import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from utils import clean_text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Sentiment analyzer using Hugging Face transformers
    """
    
    def __init__(self, model_name="w11wo/indonesian-roberta-base-sentiment-classifier-latest"):
        """
        Initialize the sentiment analyzer
        
        Args:
            model_name (str): Hugging Face model name
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.classifier = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentiment analysis model"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Create pipeline for easier inference
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                return_all_scores=True
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            # Fallback to a simpler model if the main one fails
            try:
                logger.info("Trying fallback model...")
                self.model_name = "w11wo/indonesian-roberta-base-sentiment-classifier"
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.classifier = pipeline(
                    "sentiment-analysis",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=-1,  # Use CPU for fallback
                    return_all_scores=True
                )
                logger.info("Fallback model loaded successfully")
            except Exception as e2:
                logger.error(f"Error loading fallback model: {e2}")
                raise e2
    
    def _map_label(self, label):
        """
        Map model labels to standard format
        
        Args:
            label (str): Original model label
            
        Returns:
            str: Standardized label (positive, negative, neutral)
        """
        label_mapping = {
            'LABEL_0': 'negative',
            'LABEL_1': 'neutral', 
            'LABEL_2': 'positive',
            'NEGATIVE': 'negative',
            'NEUTRAL': 'neutral',
            'POSITIVE': 'positive'
        }
        return label_mapping.get(label.upper(), label.lower())
    
    def analyze_single_text(self, text):
        """
        Analyze sentiment of a single text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Analysis result with sentiment_label and sentiment_score
        """
        if not text or not isinstance(text, str):
            return {
                'sentiment_label': 'neutral',
                'sentiment_score': 0.0,
                'error': 'Invalid text input'
            }
        
        # Clean the text
        cleaned_text = clean_text(text)
        if not cleaned_text:
            return {
                'sentiment_label': 'neutral',
                'sentiment_score': 0.0,
                'error': 'Empty text after cleaning'
            }
        
        try:
            # Get predictions
            results = self.classifier(cleaned_text)
            
            # Find the highest scoring sentiment
            best_result = max(results[0], key=lambda x: x['score'])
            
            return {
                'sentiment_label': self._map_label(best_result['label']),
                'sentiment_score': round(best_result['score'], 4),
                'all_scores': {
                    self._map_label(r['label']): round(r['score'], 4) 
                    for r in results[0]
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {
                'sentiment_label': 'neutral',
                'sentiment_score': 0.0,
                'error': str(e)
            }
    
    def analyze_batch(self, texts, batch_size=32):
        """
        Analyze sentiment of multiple texts in batches
        
        Args:
            texts (list): List of texts to analyze
            batch_size (int): Batch size for processing
            
        Returns:
            list: List of analysis results
        """
        if not texts:
            return []
        
        results = []
        
        # Process in batches to avoid memory issues
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Clean texts
            cleaned_batch = [clean_text(text) for text in batch]
            
            try:
                # Get predictions for batch
                batch_results = self.classifier(cleaned_batch)
                
                for j, text_results in enumerate(batch_results):
                    if text_results:  # Check if results exist
                        best_result = max(text_results, key=lambda x: x['score'])
                        results.append({
                            'sentiment_label': self._map_label(best_result['label']),
                            'sentiment_score': round(best_result['score'], 4),
                            'all_scores': {
                                self._map_label(r['label']): round(r['score'], 4) 
                                for r in text_results
                            }
                        })
                    else:
                        results.append({
                            'sentiment_label': 'neutral',
                            'sentiment_score': 0.0,
                            'error': 'No results from model'
                        })
                        
            except Exception as e:
                logger.error(f"Error analyzing batch: {e}")
                # Add error results for this batch
                for _ in batch:
                    results.append({
                        'sentiment_label': 'neutral',
                        'sentiment_score': 0.0,
                        'error': str(e)
                    })
        
        return results
    
    def analyze_dataframe(self, df, text_column='comment_text'):
        """
        Analyze sentiment for a pandas DataFrame
        
        Args:
            df (pandas.DataFrame): DataFrame containing text data
            text_column (str): Name of the column containing text
            
        Returns:
            pandas.DataFrame: DataFrame with added sentiment columns
        """
        if df.empty or text_column not in df.columns:
            logger.error(f"DataFrame is empty or missing column: {text_column}")
            return df
        
        # Get texts and handle NaN values
        texts = df[text_column].fillna('').astype(str).tolist()
        
        logger.info(f"Analyzing sentiment for {len(texts)} texts...")
        
        # Analyze in batches
        results = self.analyze_batch(texts)
        
        # Add results to DataFrame
        df_copy = df.copy()
        df_copy['sentiment_label'] = [r['sentiment_label'] for r in results]
        df_copy['sentiment_score'] = [r['sentiment_score'] for r in results]
        
        # Add individual sentiment scores as separate columns (optional)
        for sentiment in ['positive', 'negative', 'neutral']:
            df_copy[f'{sentiment}_score'] = [
                r.get('all_scores', {}).get(sentiment, 0.0) for r in results
            ]
        
        logger.info("Sentiment analysis completed")
        return df_copy
    
    def get_model_info(self):
        """
        Get information about the loaded model
        
        Returns:
            dict: Model information
        """
        return {
            'model_name': self.model_name,
            'device': 'cuda' if torch.cuda.is_available() and self.classifier.device.type == 'cuda' else 'cpu',
            'tokenizer_vocab_size': len(self.tokenizer) if self.tokenizer else None,
            'model_config': str(self.model.config) if self.model else None
        }
