"""
Web scraping and feed parsing utilities for competitor monitoring
"""

import requests
import feedparser
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class WebScraper:
    """Web scraper for competitor websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_website(self, url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Scrape website content using CSS selectors"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            updates = []
            
            # Default selectors if none provided
            if not selectors:
                selectors = {
                    'container': 'article, .post, .update, .changelog-entry',
                    'title': 'h1, h2, h3, .title',
                    'content': 'p, .content, .description',
                    'date': 'time, .date, .timestamp'
                }
            
            # Find all update containers
            containers = soup.select(selectors.get('container', 'article'))
            
            for container in containers[:10]:  # Limit to recent 10 updates
                update = self._extract_update_data(container, selectors)
                if update:
                    updates.append(update)
            
            logger.info(f"Scraped {len(updates)} updates from {url}")
            return updates
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return []
    
    def _extract_update_data(self, container, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data from a single update container"""
        try:
            # Extract title
            title_elem = container.select_one(selectors.get('title', 'h1, h2, h3'))
            title = title_elem.get_text().strip() if title_elem else 'No title'
            
            # Extract content
            content_elems = container.select(selectors.get('content', 'p'))
            content = ' '.join([elem.get_text().strip() for elem in content_elems[:3]])
            
            # Extract date
            date_elem = container.select_one(selectors.get('date', 'time, .date'))
            date_str = self._extract_date(date_elem) if date_elem else datetime.now().isoformat()
            
            return {
                'title': title[:200],  # Truncate long titles
                'content': content[:500],  # Truncate long content
                'date': date_str,
                'type': 'website_update'
            }
            
        except Exception as e:
            logger.error(f"Failed to extract update data: {e}")
            return None
    
    def _extract_date(self, date_elem) -> str:
        """Extract and normalize date from element"""
        try:
            # Try datetime attribute first
            if date_elem.get('datetime'):
                return datetime.fromisoformat(date_elem['datetime']).isoformat()
            
            # Try parsing text content
            date_text = date_elem.get_text().strip()
            
            # Common date patterns
            patterns = [
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\w+ \d{1,2}, \d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    return match.group(1)
            
            return datetime.now().isoformat()
            
        except Exception:
            return datetime.now().isoformat()


class RSSParser:
    """RSS/Atom feed parser for changelogs and blogs"""
    
    def parse_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Parse RSS/Atom feed and extract entries"""
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            updates = []
            
            for entry in feed.entries[:15]:  # Limit to recent 15 entries
                update = {
                    'title': entry.get('title', 'No title')[:200],
                    'content': self._extract_content(entry)[:500],
                    'date': self._parse_entry_date(entry),
                    'link': entry.get('link', ''),
                    'type': 'rss_entry'
                }
                updates.append(update)
            
            logger.info(f"Parsed {len(updates)} entries from RSS feed {feed_url}")
            return updates
            
        except Exception as e:
            logger.error(f"Failed to parse RSS feed {feed_url}: {e}")
            return []
    
    def _extract_content(self, entry) -> str:
        """Extract content from RSS entry"""
        # Try different content fields
        for field in ['content', 'summary', 'description']:
            if hasattr(entry, field):
                content = getattr(entry, field)
                if isinstance(content, list) and content:
                    content = content[0].get('value', '')
                elif isinstance(content, str):
                    pass
                else:
                    continue
                
                # Clean HTML tags
                soup = BeautifulSoup(content, 'html.parser')
                return soup.get_text().strip()
        
        return 'No content'
    
    def _parse_entry_date(self, entry) -> str:
        """Parse entry date to ISO format"""
        try:
            # Try different date fields
            for date_field in ['published_parsed', 'updated_parsed']:
                if hasattr(entry, date_field):
                    date_tuple = getattr(entry, date_field)
                    if date_tuple:
                        return datetime(*date_tuple[:6]).isoformat()
            
            # Fallback to string parsing
            for date_field in ['published', 'updated']:
                if hasattr(entry, date_field):
                    date_str = getattr(entry, date_field)
                    # Basic date parsing - feedparser should handle this
                    return datetime.now().isoformat()
            
            return datetime.now().isoformat()
            
        except Exception:
            return datetime.now().isoformat()


class SocialMediaParser:
    """Social media parser for Twitter/LinkedIn updates"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def parse_social(self, url: str, platform: str) -> List[Dict[str, Any]]:
        """Parse social media updates (limited without API)"""
        try:
            if platform == 'twitter':
                return self._parse_twitter_fallback(url)
            elif platform == 'linkedin':
                return self._parse_linkedin_fallback(url)
            else:
                logger.warning(f"Unsupported social platform: {platform}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to parse {platform} updates from {url}: {e}")
            return []
    
    def _parse_twitter_fallback(self, url: str) -> List[Dict[str, Any]]:
        """Basic Twitter parsing (limited without API)"""
        # Note: This is a fallback method. For production, use Twitter API v2
        try:
            # Try to get basic profile info or recent posts
            # This is very limited due to Twitter's restrictions
            
            # For now, return empty list and log warning
            logger.warning("Twitter parsing requires API access. Consider upgrading to Twitter API v2.")
            return []
            
        except Exception as e:
            logger.error(f"Twitter parsing failed: {e}")
            return []
    
    def _parse_linkedin_fallback(self, url: str) -> List[Dict[str, Any]]:
        """Basic LinkedIn parsing (limited without API)"""
        # Note: LinkedIn also requires API access for reliable parsing
        try:
            logger.warning("LinkedIn parsing requires API access. Consider using LinkedIn API.")
            return []
            
        except Exception as e:
            logger.error(f"LinkedIn parsing failed: {e}")
            return []
