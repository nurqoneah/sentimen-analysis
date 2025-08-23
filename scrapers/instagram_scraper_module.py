"""
Instagram Comment Scraper Module
Adapted from instagram_scraper.py for Flask integration
"""

import json
import requests
import re
from time import sleep
from loguru import logger
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os

# Load environment variables from the .env file at the start of the script
load_dotenv()

class InstagramScraper:
    """Instagram comment scraper for Flask integration"""
    
    def __init__(self):
        """Initialize the Instagram scraper"""
        self.parent_query_hash = "97b41c52301f77ce508f55e66d17620e"
        self.reply_query_hash = "863813fb3a4d6501723f11d1e44a42b1"
        self.comments_per_page = 50
        
        # Default cookies - should be updated with valid session
        self.cookies_str = self._get_default_cookies()
    
    def _get_default_cookies(self) -> str:
        """Get default cookies - in production, these should be configurable"""
        # These are example cookies - replace with valid ones
        sessionid = os.getenv("INSTAGRAM_SESSION_ID")
        ds_user_id = os.getenv("INSTAGRAM_DS_USER_ID")
        csrftoken = os.getenv("INSTAGRAM_CSRF_TOKEN")
        mid = os.getenv("INSTAGRAM_MID")
        
        
        return f"sessionid={sessionid}; ds_user_id={ds_user_id}; csrftoken={csrftoken}; mid={mid};"
    
    def build_headers(self, shortcode: str) -> Dict[str, str]:
        """Build HTTP headers for API requests"""
        return {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-A125F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "X-IG-App-ID": "936619743392459",
            "Referer": f"https://www.instagram.com/p/{shortcode}/",
            "Cookie": self.cookies_str
        }
    
    def graphql_request(self, query_hash: str, variables: Dict, headers: Dict) -> Dict:
        """Make GraphQL request to Instagram API"""
        var_str = json.dumps(variables, separators=(",", ":"))
        url = (
            f"https://www.instagram.com/graphql/query/"
            f"?query_hash={query_hash}"
            f"&variables={requests.utils.quote(var_str)}"
        )
        
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error for {query_hash}: {e}")
            return {}
    
    def fetch_replies(self, shortcode: str, comment_id: str, headers: Dict) -> List[Dict]:
        """Fetch replies for a parent comment"""
        all_replies = []
        has_next = True
        cursor = ""
        
        while has_next:
            vars = {
                "comment_id": comment_id, 
                "first": self.comments_per_page
            }
            if cursor:
                vars["after"] = cursor
            
            data = self.graphql_request(self.reply_query_hash, vars, headers)
            
            try:
                edge_info = data.get("data", {}).get("comment", {}).get("edge_threaded_comments", {})
                if not edge_info:
                    break
                    
                edges = edge_info.get("edges", [])
                for edge in edges:
                    node = edge.get("node", {})
                    if node:
                        all_replies.append({
                            "post_id": shortcode,
                            "username": node.get("owner", {}).get("username", ""),
                            "created_at": node.get("created_at", ""),
                            "comment_text": node.get("text", "")
                        })
                
                page_info = edge_info.get("page_info", {})
                has_next = page_info.get("has_next_page", False)
                cursor = page_info.get("end_cursor", "")
            except KeyError as e:
                logger.error(f"Error parsing reply data: {e}")
                break
                
            if has_next:
                sleep(2)  # Rate limiting
                
        return all_replies
    
    def fetch_comments(self, shortcode: str, headers: Dict) -> List[Dict]:
        """Fetch main comments and replies for a post"""
        all_comments = []
        has_next = True
        cursor = ""
        
        logger.info(f"Fetching comments for post {shortcode}...")
        
        while has_next:
            vars = {"shortcode": shortcode, "first": self.comments_per_page}
            if cursor:
                vars["after"] = cursor
                
            data = self.graphql_request(self.parent_query_hash, vars, headers)

            if not data or not data.get("data", {}).get("shortcode_media", {}):
                logger.error(f"Invalid data for post {shortcode}")
                break

            try:
                edge_info = data.get("data", {}).get("shortcode_media", {}).get("edge_media_to_parent_comment", {})
                if not edge_info:
                    logger.warning(f"No comments found for post {shortcode}")
                    break
                
                edges = edge_info.get("edges", [])
                for edge in edges:
                    node = edge.get("node", {})
                    if node:
                        parent_comment_id = node.get("id")
                        
                        # Add parent comment
                        all_comments.append({
                            "post_id": shortcode,
                            "username": node.get("owner", {}).get("username", ""),
                            "created_at": node.get("created_at", ""),
                            "comment_text": node.get("text", "")
                        })
                        
                        # Fetch replies if any
                        child_comment_count = node.get("edge_threaded_comments", {}).get("count", 0)
                        if child_comment_count > 0:
                            logger.info(f"Fetching {child_comment_count} replies for comment {parent_comment_id}")
                            replies = self.fetch_replies(shortcode, parent_comment_id, headers)
                            all_comments.extend(replies)
                
                page_info = edge_info.get("page_info", {})
                has_next = page_info.get("has_next_page", False)
                cursor = page_info.get("end_cursor", "")
                
            except (KeyError, TypeError) as e:
                logger.error(f"Error parsing data for {shortcode}: {e}")
                break

            if has_next:
                logger.info("Fetching next page of comments...")
                sleep(2)  # Rate limiting
                
        return all_comments
    
    def scrape_comments(self, post_id: str) -> List[Dict]:
        """
        Main method to scrape comments for a post
        
        Args:
            post_id (str): Instagram post ID (shortcode)
            
        Returns:
            List[Dict]: List of comment dictionaries
        """
        try:
            headers = self.build_headers(post_id)
            comments = self.fetch_comments(post_id, headers)
            
            logger.info(f"Successfully scraped {len(comments)} comments from Instagram post {post_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Error scraping Instagram post {post_id}: {e}")
            return []
    
    def update_cookies(self, cookies_str: str):
        """
        Update cookies for authentication
        
        Args:
            cookies_str (str): Cookie string for Instagram session
        """
        self.cookies_str = cookies_str
        logger.info("Instagram cookies updated")
