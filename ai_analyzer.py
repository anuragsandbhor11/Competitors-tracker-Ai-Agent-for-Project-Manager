"""
Gemini AI analyzer for competitor intelligence
"""

import json
import logging
from typing import Dict, Any, List
import google.generativeai as genai
import time

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    """AI analyzer using Google's Gemini API"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-flash-2.0')
        logger.info("Gemini analyzer initialized")
    
    def analyze_updates(self, updates_text: str, retry_count: int = 3) -> Dict[str, Any]:
        """Analyze competitor updates and generate structured summary"""
        prompt = self._build_analysis_prompt(updates_text)
        
        for attempt in range(retry_count):
            try:
                response = self.model.generate_content(prompt)
                
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                # Try to parse JSON response
                analysis = self._parse_analysis_response(response.text)
                logger.info("Successfully analyzed updates with Gemini")
                return analysis
                
            except Exception as e:
                logger.warning(f"Gemini analysis attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("All Gemini analysis attempts failed")
                    return self._get_fallback_analysis(updates_text)
    
    def _build_analysis_prompt(self, updates_text: str) -> str:
        """Build the analysis prompt for Gemini"""
        return f"""You are a competitive intelligence analyst. Analyze the following competitor updates and provide a structured summary.

COMPETITOR UPDATES:
{updates_text[:8000]}  

Please provide your analysis in the following JSON format:

{{
    "summary": "A concise 2-3 sentence summary of the most important developments",
    "categories": {{
        "new_features": [
            "List of new features or product updates mentioned"
        ],
        "pricing_changes": [
            "List of any pricing updates, plans, or monetization changes"
        ],
        "messaging_updates": [
            "List of branding, positioning, or marketing message changes"
        ]
    }},
    "key_insights": [
        "List of 3-5 strategic insights or competitive implications"
    ],
    "threat_level": "low/medium/high - based on competitive threat",
    "recommended_actions": [
        "List of 2-3 recommended responses or actions"
    ]
}}

Focus on:
1. New product features or capabilities
2. Pricing strategy changes
3. Market positioning shifts
4. Competitive advantages or threats
5. Customer experience improvements

Be concise but comprehensive. If no significant updates are found, indicate that in the summary.

IMPORTANT: Respond ONLY with valid JSON. No additional text or formatting."""
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate Gemini's JSON response"""
        try:
            # Clean the response - remove any markdown formatting
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            # Parse JSON
            analysis = json.loads(cleaned_text.strip())
            
            # Validate structure
            required_keys = ['summary', 'categories', 'key_insights']
            for key in required_keys:
                if key not in analysis:
                    raise ValueError(f"Missing required key: {key}")
            
            # Ensure categories has expected structure
            if 'categories' in analysis:
                categories = analysis['categories']
                for cat_key in ['new_features', 'pricing_changes', 'messaging_updates']:
                    if cat_key not in categories:
                        categories[cat_key] = []
            
            # Set defaults for optional fields
            analysis.setdefault('threat_level', 'medium')
            analysis.setdefault('recommended_actions', [])
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            # Try to extract partial information
            return self._extract_partial_analysis(response_text)
        
        except Exception as e:
            logger.error(f"Analysis parsing failed: {e}")
            raise
    
    def _extract_partial_analysis(self, response_text: str) -> Dict[str, Any]:
        """Extract partial analysis when JSON parsing fails"""
        return {
            'summary': self._extract_summary_fallback(response_text),
            'categories': {
                'new_features': [],
                'pricing_changes': [],
                'messaging_updates': []
            },
            'key_insights': [],
            'threat_level': 'medium',
            'recommended_actions': []
        }
    
    def _extract_summary_fallback(self, text: str) -> str:
        """Extract summary when structured parsing fails"""
        # Look for summary-like content in the response
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 50 and ('update' in line.lower() or 'competitor' in line.lower()):
                return line[:300]
        
        return "Analysis completed but summary extraction failed."
    
    def _get_fallback_analysis(self, updates_text: str) -> Dict[str, Any]:
        """Provide fallback analysis when AI fails"""
        # Count updates and provide basic analysis
        lines = updates_text.split('\n')
        update_count = len([line for line in lines if line.startswith('Source:')])
        
        return {
            'summary': f"Collected {update_count} competitor updates this week. AI analysis temporarily unavailable - manual review recommended.",
            'categories': {
                'new_features': [],
                'pricing_changes': [],
                'messaging_updates': []
            },
            'key_insights': [
                "AI analysis failed - manual review needed",
                f"{update_count} updates collected for review"
            ],
            'threat_level': 'medium',
            'recommended_actions': [
                "Review collected updates manually",
                "Check AI service status and retry analysis"
            ]
        }
    
    def categorize_single_update(self, update_text: str) -> str:
        """Categorize a single update (helper function)"""
        try:
            prompt = f"""Categorize this competitor update into one of these categories:
1. new_features
2. pricing_changes  
3. messaging_updates
4. other

Update: {update_text[:500]}

Respond with only the category name."""
            
            response = self.model.generate_content(prompt)
            category = response.text.strip().lower()
            
            if category in ['new_features', 'pricing_changes', 'messaging_updates']:
                return category
            else:
                return 'other'
                
        except Exception as e:
            logger.warning(f"Failed to categorize update: {e}")
            return 'other'
