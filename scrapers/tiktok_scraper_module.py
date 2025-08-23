"""
TikTok Comment Scraper Module
Adapted from tiktok_scraper.py for Flask integration
"""

import jmespath
import json
from typing import Any, Dict, Iterator, List, Optional
from requests import Session, Response
from loguru import logger
from dataclasses import dataclass, asdict

@dataclass
class Comment:
    """Data class for individual comment"""
    comment_id: str
    username: str
    nickname: str
    comment: str
    create_time: int
    avatar: str
    total_reply: int
    replies: List['Comment'] = None
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []

@dataclass
class Comments:
    """Data class for collection of comments"""
    caption: str
    video_url: str
    comments: List[Comment]
    has_more: bool
    
    @property
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for compatibility"""
        return {
            'caption': self.caption,
            'video_url': self.video_url,
            'comments': [asdict(comment) for comment in self.comments],
            'has_more': self.has_more
        }

class TikTokScraper:
    """TikTok comment scraper for Flask integration"""
    
    BASE_URL: str = 'https://www.tiktok.com'
    API_URL: str = f'{BASE_URL}/api'

    def __init__(self) -> None:
        """Initialize the TikTok scraper"""
        self.__session: Session = Session()
        self.aweme_id: str = ""
    
    def __parse_comment(self, data: Dict[str, Any]) -> Comment:
        """Parse comment data from API response"""
        parsed_data: Dict[str, Any] = jmespath.search(
            """
            {
                comment_id: cid,
                username: user.unique_id,
                nickname: user.nickname,
                comment: text,
                create_time: create_time,
                avatar: user.avatar_thumb.url_list[0],
                total_reply: reply_comment_total
            }
            """,
            data
        )
    
        comment: Comment = Comment(
            **parsed_data,
            replies=list(
                self.get_all_replies(parsed_data.get('comment_id'))
            ) if parsed_data.get('total_reply') else []
        )

        # Simple log format: username - comment (truncated)
        comment_preview = comment.comment[:100] + "..." if len(comment.comment) > 100 else comment.comment
        logger.info(f'{comment.username} - {comment_preview}')
        return comment

    def get_all_replies(self, comment_id: str) -> Iterator[Comment]:
        """Get all replies for a comment"""
        page: int = 1
        while True:
            replies = self.get_replies(comment_id=comment_id, page=page)
            if not replies:
                break
            for reply in replies:
                yield reply
            page += 1

    def get_replies(self, comment_id: str, size: Optional[int] = 50, page: Optional[int] = 1):
        """Get replies for a specific comment"""
        try:
            response: Response = self.__session.get(
                f'{self.API_URL}/comment/list/reply/',
                params={
                    'aid': 1988,
                    'comment_id': comment_id,
                    'item_id': self.aweme_id,
                    'count': size,
                    'cursor': (page - 1) * size
                },
                timeout=30
            )

            return [
                self.__parse_comment(comment) 
                for comment in response.json().get('comments', [])
            ]
        except Exception as e:
            logger.error(f"Error fetching replies: {e}")
            return []
    
    def get_all_comments(self, aweme_id: str) -> Comments:
        """Get all comments for a video"""
        page: int = 1
        data: Comments = self.get_comments(aweme_id=aweme_id, page=page)
        
        while True:
            page += 1
            comments: Comments = self.get_comments(aweme_id=aweme_id, page=page)
            if not comments.has_more:
                break
            data.comments.extend(comments.comments)

        return data

    def get_comments(self, aweme_id: str, size: Optional[int] = 50, page: Optional[int] = 1) -> Comments:
        """Get comments for a specific page"""
        self.aweme_id: str = aweme_id

        try:
            response: Response = self.__session.get(
                f'{self.API_URL}/comment/list/',
                params={
                    'aid': 1988,
                    'aweme_id': aweme_id,
                    'count': size,
                    'cursor': (page - 1) * size
                },
                timeout=30
            )

            data: Dict[str, Any] = jmespath.search(    
                """
                {
                    caption: comments[0].share_info.title,
                    video_url: comments[0].share_info.url,
                    comments: comments,
                    has_more: has_more
                }
                """,
                response.json()
            )

            return Comments(
                comments=[
                    self.__parse_comment(comment) 
                    for comment in data.get('comments', [])
                ],
                caption=data.get('caption', ''),
                video_url=data.get('video_url', ''),
                has_more=data.get('has_more', False)
            )
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            return Comments(comments=[], caption='', video_url='', has_more=False)
    
    def __call__(self, aweme_id: str) -> Comments:
        """Make the class callable"""
        return self.get_all_comments(aweme_id=aweme_id)
    
    def scrape_comments(self, aweme_id: str) -> List[Dict]:
        """
        Main method to scrape comments for a TikTok video
        
        Args:
            aweme_id (str): TikTok video ID
            
        Returns:
            List[Dict]: List of standardized comment dictionaries
        """
        try:
            logger.info(f'Starting to scrape TikTok video {aweme_id}...')
            
            comments: Comments = self(aweme_id=aweme_id)
            comment_list = comments.dict['comments']
            
            # Standardize format to match Instagram scraper output
            standardized_comments = []
            for comment in comment_list:
                standardized_comment = {
                    'post_id': aweme_id,
                    'username': comment.get('username', ''),
                    'created_at': comment.get('create_time', ''),
                    'comment_text': comment.get('comment', '')
                }
                standardized_comments.append(standardized_comment)
            
            logger.info(f"✓ Scraped {len(standardized_comments)} comments from TikTok video {aweme_id}")
            return standardized_comments
            
        except Exception as e:
            logger.error(f"Error scraping TikTok video {aweme_id}: {e}")
            return []
