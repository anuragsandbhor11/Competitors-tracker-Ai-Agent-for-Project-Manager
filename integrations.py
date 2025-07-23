"""
Slack and Notion integration modules for competitor monitoring
"""

import json
import requests
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SlackNotifier:
    """Slack webhook notifier for competitor updates"""
    
    def __init__(self, webhook_url: str):
        if not webhook_url:
            raise ValueError("Slack webhook URL is required")
        
        self.webhook_url = webhook_url
        self.session = requests.Session()
        logger.info("Slack notifier initialized")
    
    def send_message(self, message: str, retry_count: int = 3) -> bool:
        """Send message to Slack via webhook"""
        payload = {
            "text": message,
            "username": "Competitor Bot",
            "icon_emoji": ":mag:",
            "blocks": self._format_blocks(message)
        }
        
        for attempt in range(retry_count):
            try:
                response = self.session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info("Successfully sent message to Slack")
                    return True
                else:
                    logger.warning(f"Slack webhook returned {response.status_code}: {response.text}")
                    
            except Exception as e:
                logger.error(f"Slack notification attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)
        
        logger.error("All Slack notification attempts failed")
        return False
    
    def _format_blocks(self, message: str) -> List[Dict]:
        """Format message into Slack blocks for better display"""
        # Split message into sections
        sections = message.split('\n\n')
        blocks = []
        
        for section in sections:
            if section.strip():
                # Header section
                if section.startswith('🔍 **'):
                    blocks.append({
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": section.replace('🔍 **', '').replace('**', '').strip()
                        }
                    })
                else:
                    # Regular text section
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": section
                        }
                    })
        
        # Add divider at the end
        blocks.append({"type": "divider"})
        
        return blocks
    
    def send_error_alert(self, error_message: str) -> bool:
        """Send error alert to Slack"""
        alert_message = f"""🚨 *Competitor Monitoring Alert*
        
*Error*: {error_message}
*Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Action Required*: Check logs and system status"""
        
        return self.send_message(alert_message)


class NotionUpdater:
    """Notion API integration for competitor intelligence reports"""
    
    def __init__(self, token: str, page_id: str):
        if not token or not page_id:
            raise ValueError("Notion token and page ID are required")
        
        self.token = token
        self.page_id = page_id
        self.base_url = "https://api.notion.com/v1"
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        })
        logger.info("Notion updater initialized")
    
    def update_page(self, content: Dict[str, Any], retry_count: int = 3) -> bool:
        """Update Notion page with competitor intelligence report"""
        for attempt in range(retry_count):
            try:
                # Create new page as child of the specified page
                page_data = self._build_page_content(content)
                
                response = self.session.post(
                    f"{self.base_url}/pages",
                    json=page_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info("Successfully created Notion page")
                    return True
                else:
                    logger.warning(f"Notion API returned {response.status_code}: {response.text}")
                    
            except Exception as e:
                logger.error(f"Notion update attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)
        
        logger.error("All Notion update attempts failed")
        return False
    
    def _build_page_content(self, content: Dict[str, Any]) -> Dict:
        """Build Notion page content structure"""
        title = content.get('title', 'Competitor Intelligence Report')
        summary = content.get('summary', '')
        categories = content.get('categories', {})
        total_updates = content.get('total_updates', 0)
        
        # Build page properties and content
        page_data = {
            "parent": {"page_id": self.page_id},
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            },
            "children": [
                # Summary section
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "Executive Summary"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"Total Updates: {total_updates}\n\n{summary}"
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        # Add category sections
        if categories.get('new_features'):
            page_data["children"].extend(self._build_category_blocks("🆕 New Features", categories['new_features']))
        
        if categories.get('pricing_changes'):
            page_data["children"].extend(self._build_category_blocks("💰 Pricing Changes", categories['pricing_changes']))
        
        if categories.get('messaging_updates'):
            page_data["children"].extend(self._build_category_blocks("📢 Messaging Updates", categories['messaging_updates']))
        
        # Add metadata
        page_data["children"].append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })
        
        page_data["children"].append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "text": {
                            "content": f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        }
                    }
                ]
            }
        })
        
        return page_data
    
    def _build_category_blocks(self, category_title: str, items: list) -> list:
        """Build Notion blocks for a category section"""
        blocks = [
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "text": {
                                "content": category_title
                            }
                        }
                    ]
                }
            }
        ]
        
        if items:
            # Create bulleted list
            for item in items[:10]:  # Limit items
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": str(item)[:2000]  # Notion has character limits
                                }
                            }
                        ]
                    }
                })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "No updates in this category this week."
                            }
                        }
                    ]
                }
            })
        
        return blocks
    
    def test_connection(self) -> bool:
        """Test Notion API connection"""
        try:
            response = self.session.get(f"{self.base_url}/pages/{self.page_id}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Notion connection test failed: {e}")
            return False
