#!/usr/bin/env python3
"""
OpenAI-powered response generation for dynamic, intelligent chatbot responses
"""
import openai
import logging
from typing import Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class OpenAIResponseService:
    """Service for generating dynamic responses using OpenAI"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.system_prompt = """You are an expert Sri Lankan tourism guide. You ONLY answer questions about Sri Lankan tourism, travel, destinations, activities, and related topics.

Key guidelines:
- Be friendly, helpful, and enthusiastic about Sri Lanka
- Provide accurate, up-to-date information
- Give practical tips and insider knowledge
- Mention costs, best times, and practical details
- If asked non-tourism questions, politely decline with: "I'm here to help you with Sri Lankan tourism questions only. Please ask me about destinations, activities, travel tips, or anything related to visiting Sri Lanka!"
- Keep responses concise but comprehensive
- Use emojis occasionally for friendliness 🌴🐘🏛️

You have access to this destination knowledge:
{destination_knowledge}

Use this knowledge as base, but elaborate naturally based on the specific question asked."""
    
    def generate_response(self, user_message: str, entities: Dict = None, destination_knowledge: Dict = None) -> str:
        """Original legacy method used for simple responses"""
        return self.generate_human_response(user_message, entities, str(destination_knowledge))

    def generate_human_response(self, user_message: str, entities: Dict = None, context: str = "") -> str:
        """
        Generate dynamic response using OpenAI with RAG context
        
        Args:
            user_message: The user's question
            entities: Extracted entities
            context: Retrieved destination data from database
            
        Returns:
            Natural, helpful response
        """
        try:
            # Customize system prompt with current knowledge from RAG
            custom_system_prompt = f"""You are an expert Sri Lankan tourism assistant. 
Use the following retrieved destination data to provide accurate and specific recommendations.
If the data contains specific destinations, mention them by name and highlight their best features.

RETRIEVED DATA:
{context}

Guidelines:
- Be warm and professional.
- If you find specific destinations in the data, describe them naturally.
- If the query is "I need to hiking", mention Ella Rock, Little Adams Peak, etc. if they are in the data.
- Keep it concise (under 200 words).
"""
            
            messages = [
                {"role": "system", "content": custom_system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return "Sri Lanka has many beautiful spots for that! I recommend checking out our destinations page for detailed guides."
    
    def is_tourism_related_openai(self, message: str) -> tuple[bool, float]:
        """
        Use OpenAI to determine if message is tourism-related
        
        Args:
            message: User's message
            
        Returns:
            Tuple of (is_tourism, confidence)
        """
        try:
            system_prompt = """You are a tourism classification expert. Determine if the following message is related to Sri Lankan tourism.

Respond with ONLY:
- "TOURISM:0.95" (if clearly tourism-related with high confidence)
- "TOURISM:0.70" (if tourism-related with medium confidence)  
- "TOURISM:0.40" (if possibly tourism-related with low confidence)
- "TOURISM:0.10" (if probably not tourism-related)

Consider these tourism topics: destinations, attractions, activities, transport, accommodation, food, culture, weather, costs, travel tips, Sri Lanka-specific questions.

Message: {message}"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            if "TOURISM:" in result:
                confidence = float(result.split(":")[1])
                is_tourism = confidence >= 0.45
                return is_tourism, confidence
            
            return False, 0.0
            
        except Exception as e:
            logger.error(f"Error in OpenAI tourism detection: {str(e)}")
            return False, 0.0
