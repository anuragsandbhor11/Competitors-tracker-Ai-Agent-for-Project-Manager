# Competitors-tracker-Ai-Agent-for-Project-Manager
# AI Competitor Monitoring Agent

An automated AI-powered system that monitors competitor websites, changelogs, RSS feeds, and social media for weekly intelligence reports delivered to Slack and Notion.

## Features

- Multi-Source Monitoring: Websites, RSS feeds, changelogs, social media
- AI Analysis: Gemini Pro analyzes and categorizes updates
- Smart Categorization: New features, pricing changes, messaging updates
- Automated Delivery: Weekly reports to Slack and Notion
- Production Ready: Error handling, logging, retry logic

## Quick Setup

### 1. Install Dependencies
bash
pip install -r requirements.txt


### 2. Configure Environment
bash
cp .env.example .env
# Edit .env with your API keys


### 3. Setup API Keys

Gemini API:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Add to GEMINI_API_KEY in .env

Slack Webhook:
1. Create Slack app at [api.slack.com](https://api.slack.com/apps)
2. Enable Incoming Webhooks
3. Copy webhook URL to SLACK_WEBHOOK_URL

Notion Integration:
1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create new integration
3. Copy token to NOTION_TOKEN
4. Share target page with integration
5. Copy page ID to NOTION_PAGE_ID

### 4. Configure Sources
Edit sources.json to add your competitor URLs:
json
{
  "sources": [
    {
      "name": "Competitor Blog",
      "url": "https://competitor.com/blog",
      "type": "website",
      "selectors": {
        "container": ".post",
        "title": "h2",
        "content": ".content",
        "date": ".date"
      }
    }
  ]
}


## Usage

### Run Once (Testing)
bash
python main.py --run-now


### Schedule Weekly Runs
bash
python main.py
# Runs every Monday at 9 AM


### Production Deployment

Using Cron:
bash
# Add to crontab for weekly runs
0 9 * * 1 /usr/bin/python3 /path/to/main.py --run-now


Using Docker:
dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]


Cloud Deployment:
- AWS Lambda + EventBridge
- Google Cloud Functions + Cloud Scheduler
- Azure Functions + Logic Apps

## Configuration

### Source Types

Website:
json
{
  "name": "Company Blog",
  "url": "https://company.com/blog",
  "type": "website",
  "selectors": {
    "container": ".post, article",
    "title": "h1, h2, .title",
    "content": ".content, p",
    "date": "time, .date"
  }
}


RSS Feed:
json
{
  "name": "Company Feed",
  "url": "https://company.com/feed.xml",
  "type": "rss"
}


Social Media:
json
{
  "name": "Company Twitter",
  "url": "https://twitter.com/company",
  "type": "twitter"
}


### CSS Selectors Guide

Common selectors for different sites:
- Changelog pages: .changelog-entry, .release-notes, .update
- Blog posts: article, .post, .blog-entry
- Pricing pages: .pricing-tier, .plan, .package
- Product pages: .feature, .product-update

## Output Examples

### Slack Message

🔍 Weekly Competitor Intelligence Report

📊 Total Updates: 12

📋 Summary: 
Major competitor launched new AI features, two pricing updates detected.

🆕 New Features (3):
• AI-powered analytics dashboard
• Real-time collaboration tools
• Mobile app redesign

💰 Pricing Changes (2):
• Enterprise plan increased by 20%
• New startup tier introduced

📢 Messaging Updates (1):
• Repositioning as "AI-first platform"


### Notion Page Structure
- Executive Summary
- New Features (bulleted list)
- Pricing Changes (bulleted list)
- Messaging Updates (bulleted list)
- Metadata (timestamp, update count)

## Troubleshooting

### Common Issues

Empty Results:
- Check CSS selectors in sources.json
- Verify URLs are accessible
- Some sites block automated scraping

API Errors:
- Verify API keys in .env
- Check API quotas and limits
- Review logs in competitor_agent.log

Social Media Limitations:
- Twitter/LinkedIn require official APIs
- Current implementation provides placeholders
- Consider upgrading to paid API access

### Logs
Check competitor_agent.log for detailed error information:
bash
tail -f competitor_agent.log


## Advanced Configuration

### Custom Analysis Prompts
Modify ai_analyzer.py to customize how Gemini analyzes updates:
python
def _build_analysis_prompt(self, updates_text: str) -> str:
    # Customize this prompt for your industry/needs


### Additional Integrations
Extend integrations.py to add:
- Email reports
- Teams notifications  
- Database storage
- Custom webhooks

### Rate Limiting
Adjust delays in scrapers for respectful crawling:
python
time.sleep(1)  # Wait between requests


## Security Notes

- Store API keys securely (use environment variables)
- Respect robots.txt and rate limits
- Monitor API usage to avoid quota exceeded errors
- Use HTTPS URLs only
- Regularly rotate API keys

## License

MIT License - See LICENSE file for details
