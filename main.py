


import os
import json
import time
import logging
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass

from scrapers import WebScraper, RSSParser, SocialMediaParser
from ai_analyzer import GeminiAnalyzer
from integrations import SlackNotifier, NotionUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('competitor_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Source:
    """Data class for monitoring sources"""
    name: str
    url: str
    type: str  # 'website', 'rss', 'twitter', 'linkedin'
    selectors: Dict[str, str] = None  # CSS selectors for web scraping

class CompetitorAgent:
    """Main agent class for monitoring competitors"""
    
    def __init__(self):
        self.scraper = WebScraper()
        self.rss_parser = RSSParser()
        self.social_parser = SocialMediaParser()
        self.analyzer = GeminiAnalyzer(os.getenv('GEMINI_API_KEY'))
        self.slack_notifier = SlackNotifier(os.getenv('SLACK_WEBHOOK_URL'))
        self.notion_updater = NotionUpdater(
            os.getenv('NOTION_TOKEN'), 
            os.getenv('NOTION_PAGE_ID')
        )
        
        # Load sources from config
        self.sources = self._load_sources()
        logger.info(f"Initialized agent with {len(self.sources)} sources")
    
    def _load_sources(self) -> List[Source]:
        """Load monitoring sources from config file"""
        try:
            with open('sources.json', 'r') as f:
                sources_data = json.load(f)
            
            sources = []
            for src in sources_data['sources']:
                sources.append(Source(
                    name=src['name'],
                    url=src['url'],
                    type=src['type'],
                    selectors=src.get('selectors')
                ))
            return sources
        except Exception as e:
            logger.error(f"Failed to load sources: {e}")
            return []
    
    def collect_updates(self) -> List[Dict[str, Any]]:
        """Collect updates from all configured sources"""
        all_updates = []
        
        for source in self.sources:
            try:
                logger.info(f"Collecting from {source.name}")
                
                if source.type == 'website':
                    updates = self.scraper.scrape_website(source.url, source.selectors)
                elif source.type == 'rss':
                    updates = self.rss_parser.parse_feed(source.url)
                elif source.type in ['twitter', 'linkedin']:
                    updates = self.social_parser.parse_social(source.url, source.type)
                else:
                    logger.warning(f"Unknown source type: {source.type}")
                    continue
                
                # Add source info to each update
                for update in updates:
                    update['source'] = source.name
                    update['source_type'] = source.type
                
                all_updates.extend(updates)
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Failed to collect from {source.name}: {e}")
        
        logger.info(f"Collected {len(all_updates)} total updates")
        return all_updates
    
    def filter_recent_updates(self, updates: List[Dict], days: int = 7) -> List[Dict]:
        """Filter updates to only include recent ones"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_updates = []
        
        for update in updates:
            try:
                update_date = datetime.fromisoformat(update.get('date', ''))
                if update_date > cutoff_date:
                    recent_updates.append(update)
            except (ValueError, TypeError):
                # Include updates without valid dates to be safe
                recent_updates.append(update)
        
        logger.info(f"Filtered to {len(recent_updates)} recent updates")
        return recent_updates
    
    def generate_summary(self, updates: List[Dict]) -> Dict[str, Any]:
        """Generate AI summary of all updates"""
        if not updates:
            return {
                'summary': 'No significant competitor updates found this week.',
                'categories': {
                    'new_features': [],
                    'pricing_changes': [],
                    'messaging_updates': []
                },
                'total_updates': 0
            }
        
        # Prepare data for AI analysis
        updates_text = self._format_updates_for_analysis(updates)
        
        # Get AI summary
        summary = self.analyzer.analyze_updates(updates_text)
        summary['total_updates'] = len(updates)
        
        return summary
    
    def _format_updates_for_analysis(self, updates: List[Dict]) -> str:
        """Format updates for AI analysis"""
        formatted = []
        for update in updates:
            source = update.get('source', 'Unknown')
            title = update.get('title', 'No title')
            content = update.get('content', update.get('description', ''))
            date = update.get('date', 'Unknown date')
            
            formatted.append(f"Source: {source}\nDate: {date}\nTitle: {title}\nContent: {content}\n---")
        
        return '\n'.join(formatted)
    
    def send_notifications(self, summary: Dict[str, Any]):
        """Send summary to Slack and Notion"""
        try:
            # Send to Slack
            slack_message = self._format_slack_message(summary)
            self.slack_notifier.send_message(slack_message)
            logger.info("Sent summary to Slack")
            
            # Update Notion
            notion_content = self._format_notion_content(summary)
            self.notion_updater.update_page(notion_content)
            logger.info("Updated Notion page")
            
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
    
    def _format_slack_message(self, summary: Dict) -> str:
        """Format summary for Slack"""
        msg = f"🔍 **Weekly Competitor Intelligence Report**\n\n"
        msg += f"📊 **Total Updates**: {summary.get('total_updates', 0)}\n\n"
        
        msg += f"📋 **Summary**:\n{summary.get('summary', 'No updates')}\n\n"
        
        categories = summary.get('categories', {})
        if categories.get('new_features'):
            msg += f"🆕 **New Features** ({len(categories['new_features'])}):\n"
            for feature in categories['new_features'][:5]:  # Limit to 5
                msg += f"• {feature}\n"
            msg += "\n"
        
        if categories.get('pricing_changes'):
            msg += f"💰 **Pricing Changes** ({len(categories['pricing_changes'])}):\n"
            for change in categories['pricing_changes'][:5]:
                msg += f"• {change}\n"
            msg += "\n"
        
        if categories.get('messaging_updates'):
            msg += f"📢 **Messaging Updates** ({len(categories['messaging_updates'])}):\n"
            for update in categories['messaging_updates'][:5]:
                msg += f"• {update}\n"
        
        msg += f"\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        return msg
    
    def _format_notion_content(self, summary: Dict) -> Dict:
        """Format summary for Notion"""
        return {
            'title': f"Competitor Intelligence - Week of {datetime.now().strftime('%Y-%m-%d')}",
            'summary': summary.get('summary', ''),
            'total_updates': summary.get('total_updates', 0),
            'categories': summary.get('categories', {}),
            'generated_at': datetime.now().isoformat()
        }
    
    def run_weekly_analysis(self):
        """Run the complete weekly analysis pipeline"""
        logger.info("Starting weekly competitor analysis")
        
        try:
            # Collect all updates
            updates = self.collect_updates()
            
            # Filter to recent updates
            recent_updates = self.filter_recent_updates(updates)
            
            # Generate AI summary
            summary = self.generate_summary(recent_updates)
            
            # Send notifications
            self.send_notifications(summary)
            
            logger.info("Weekly analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Weekly analysis failed: {e}")
            # Send error notification
            error_msg = f"⚠️ Competitor monitoring failed: {str(e)}"
            try:
                self.slack_notifier.send_message(error_msg)
            except:
                pass

def main():
    """Main function to run the agent"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Validate required environment variables
    required_vars = ['GEMINI_API_KEY', 'SLACK_WEBHOOK_URL', 'NOTION_TOKEN', 'NOTION_PAGE_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    # Initialize agent
    agent = CompetitorAgent()
    
    # Schedule weekly runs (every Monday at 9 AM)
    schedule.every().monday.at("09:00").do(agent.run_weekly_analysis)
    
    # For testing, also allow manual run
    if len(os.sys.argv) > 1 and os.sys.argv[1] == '--run-now':
        agent.run_weekly_analysis()
        return
    
    logger.info("Competitor monitoring agent started. Waiting for scheduled runs...")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
