import logging
import random
import re
from typing import Dict, List, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from config import Config
from services.embedding_service import EmbeddingService
from services.openai_response_service import OpenAIResponseService

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self, embedding_service: EmbeddingService, recommendation_service):
        self.embedding_service = embedding_service
        self.recommendation_service = recommendation_service
        self.openai_response_service = OpenAIResponseService()
        self.tourism_keywords = Config.TOURISM_KEYWORDS
        self.tourism_examples = Config.TOURISM_EXAMPLES
        self.non_tourism_examples = Config.NON_TOURISM_EXAMPLES
        self.similarity_threshold = Config.TOURISM_SIMILARITY_THRESHOLD
        
        # Precompute embeddings for examples
        self._precompute_example_embeddings()
        
        # Response templates
        self._initialize_response_templates()
    
    def _precompute_example_embeddings(self):
        """Precompute embeddings for tourism and non-tourism examples"""
        try:
            logger.info("Precomputing example embeddings for intent detection")
            self.tourism_embeddings = self.embedding_service.get_embedding(self.tourism_examples)
            self.non_tourism_embeddings = self.embedding_service.get_embedding(self.non_tourism_examples)
            logger.info("Example embeddings computed successfully")
        except Exception as e:
            logger.error(f"Error precomputing embeddings: {str(e)}")
            self.tourism_embeddings = None
            self.non_tourism_embeddings = None
    
    def _initialize_response_templates(self):
        """Initialize response templates for different types of tourism queries"""
        self.response_templates = {
            'destination_recommendation': [
                "Based on your interest in {interest}, I recommend these amazing destinations: {destinations}",
                "For {interest} enthusiasts, you'll love: {destinations}",
                "Here are the best places for {interest}: {destinations}"
            ],
            'best_time': [
                "The best time to visit {destination} is {time}. {additional_info}",
                "I recommend visiting {destination} during {time}. {additional_info}",
                "Plan your trip to {destination} in {time} for the best experience. {additional_info}"
            ],
            'cost_info': [
                "The cost for {destination} is approximately {cost}. {additional_info}",
                "You can expect to pay around {cost} for {destination}. {additional_info}",
                "Budget about {cost} for your visit to {destination}. {additional_info}"
            ],
            'duration': [
                "I recommend spending {duration} at {destination}. {additional_info}",
                "Plan for {duration} to fully enjoy {destination}. {additional_info}",
                "You'll need {duration} to explore {destination} properly. {additional_info}"
            ],
            'activities': [
                "At {destination}, you can enjoy: {activities}",
                "Popular activities at {destination} include: {activities}",
                "Don't miss these activities at {destination}: {activities}"
            ],
            'itinerary': [
                "Here's a {duration} itinerary for {destination}: {itinerary}",
                "For {duration} in {destination}, I suggest: {itinerary}",
                "Your {duration} plan for {destination}: {itinerary}"
            ],
            'general': [
                "{response}",
                "Here's what I can tell you about that: {response}",
                "Based on my knowledge: {response}"
            ]
        }
        
        # Destination knowledge base
        self.destination_knowledge = {
            'sigiriya': {
                'cost': '$30 USD for foreigners',
                'best_time': 'December to April',
                'duration': '3-4 hours',
                'activities': 'climbing the rock, viewing frescoes, photography, exploring gardens',
                'description': 'ancient rock fortress with stunning views'
            },
            'yala': {
                'cost': '$60 USD for safari',
                'best_time': 'February to July',
                'duration': 'full day',
                'activities': 'wildlife safari, leopard spotting, bird watching',
                'description': 'famous national park for wildlife'
            },
            'ella': {
                'cost': 'free for most attractions',
                'best_time': 'December to March',
                'duration': '2-3 days',
                'activities': 'hiking Ella Rock, Little Adams Peak, Nine Arch Bridge',
                'description': 'scenic hill country town'
            },
            'mirissa': {
                'cost': '$15 USD for whale watching',
                'best_time': 'November to April',
                'duration': 'half day',
                'activities': 'whale watching, surfing, beach relaxation',
                'description': 'beautiful beach destination'
            },
            'kandy': {
                'cost': 'free for Temple of Tooth',
                'best_time': 'December to April',
                'duration': '1-2 days',
                'activities': 'visiting Temple of Tooth, botanical gardens, cultural shows',
                'description': 'cultural capital of Sri Lanka'
            },
            'galle': {
                'cost': 'free to explore fort',
                'best_time': 'November to April',
                'duration': 'half day',
                'activities': 'exploring Galle Fort, beaches, shopping',
                'description': 'historic coastal city'
            },
            'nuwara eliya': {
                'cost': '$10-20 USD for attractions',
                'best_time': 'March to May, September to November',
                'duration': '1-2 days',
                'activities': 'visiting tea plantations, Horton Plains, Gregory Lake',
                'description': 'Little England of Sri Lanka, cool climate'
            },
            'polonnaruwa': {
                'cost': '$25 USD for foreign visitors',
                'best_time': 'April to September',
                'duration': 'full day',
                'activities': 'exploring ancient ruins, cycling, archaeological sites',
                'description': 'medieval capital with ancient ruins'
            },
            'trincomalee': {
                'cost': 'free beaches, $15 for boat trips',
                'best_time': 'May to September',
                'duration': '2-3 days',
                'activities': 'beach visits, whale watching, hot springs',
                'description': 'beautiful natural harbor and beaches'
            },
            'dambulla': {
                'cost': '$15 USD for cave temple',
                'best_time': 'December to April',
                'duration': '2-3 hours',
                'activities': 'cave temple visit, golden Buddha statue',
                'description': 'UNESCO World Heritage cave temple'
            },
            'anuradhapura': {
                'cost': '$25 USD for foreign visitors',
                'best_time': 'April to September',
                'duration': 'full day',
                'activities': 'visiting ancient stupas, Bodhi tree, archaeological sites',
                'description': 'ancient capital with sacred Buddhist sites'
            }
        }
    
    def is_tourism_related(self, text: str) -> Tuple[bool, float]:
        """
        Determine if text is tourism-related using keyword matching and similarity
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (is_tourism, confidence_score)
        """
        try:
            text_lower = text.lower()
            
            # Greetings and farewells should always be considered tourism-related
            if any(word in text_lower for word in ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'welcome', 'bye', 'goodbye', 'thank you', 'thanks', 'see you', 'farewell']):
                return True, 1.0
            
            # Method 1: Keyword matching
            keyword_matches = sum(1 for keyword in self.tourism_keywords if keyword in text_lower)
            keyword_score = min(keyword_matches / 3.0, 1.0)  # Normalize to 0-1
            
            # Method 2: Similarity with examples (if embeddings are available)
            similarity_score = 0.0
            if self.tourism_embeddings is not None and self.non_tourism_embeddings is not None:
                # Calculate similarity with tourism examples
                tourism_similarities = self.embedding_service.batch_similarity(text, self.tourism_examples)
                max_tourism_similarity = max(tourism_similarities) if tourism_similarities else 0.0
                
                # Calculate similarity with non-tourism examples
                non_tourism_similarities = self.embedding_service.batch_similarity(text, self.non_tourism_examples)
                max_non_tourism_similarity = max(non_tourism_similarities) if non_tourism_similarities else 0.0
                
                # Combined similarity score
                similarity_score = max_tourism_similarity - max_non_tourism_similarity
                similarity_score = max(0.0, similarity_score)  # Ensure non-negative
            
            # Combine scores (weighted average)
            combined_score = 0.6 * keyword_score + 0.4 * similarity_score
            
            is_tourism = combined_score >= self.similarity_threshold
            
            logger.info(f"Tourism detection - Keyword: {keyword_score:.3f}, Similarity: {similarity_score:.3f}, Combined: {combined_score:.3f}")
            
            return is_tourism, combined_score
            
        except Exception as e:
            logger.error(f"Error in tourism detection: {str(e)}")
            return False, 0.0
    
    def generate_response(self, user_message: str, user_preferences: Dict = None) -> str:
        """
        Generate a response to a tourism-related query using OpenAI
        
        Args:
            user_message: The user's message
            user_preferences: User preferences and context
            
        Returns:
            Dynamic, intelligent response
        """
        try:
            # Extract entities and query type
            query_type, entities = self._analyze_query(user_message)
            
            # RAG: Use RecommendationService to find relevant destinations from the ACTUAL database
            recommendations = self.recommendation_service.get_recommendations(user_message, user_preferences, limit=5)
            
            # Format recommendations for context
            if recommendations:
                recommendations_ctx = []
                for rec in recommendations:
                    d = rec['destination']
                    recommendations_ctx.append(
                        f"Destination: {d['name']} (Category: {d['category']}, Rating: {d['rating']}/5)\n"
                        f"Description: {d['description']}\n"
                        f"Facilities: {d['tags']}\n"
                        f"Best Time: {d['best_time_to_visit']}, Duration: {d['duration']}\n"
                        f"Average Cost: ${d['average_cost']} USD"
                    )
                context = "\n\n".join(recommendations_ctx)
                logger.info(f"RAG: Retrieved {len(recommendations)} destinations for context.")
            else:
                context = "No specific destinations found for this query in our database."
                logger.info("RAG: No destinations retrieved for context.")

            # Use OpenAI for dynamic response generation, passing retrieved context
            response = self.openai_response_service.generate_human_response(
                user_message=user_message,
                entities=entities,
                context=context
            )
            
            return {
                'text': response,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'd be happy to help you with Sri Lankan tourism! Could you please rephrase your question?"
    
    def _analyze_query(self, message: str) -> Tuple[str, Dict]:
        """Analyze query to determine type and extract entities"""
        message_lower = message.lower()
        entities = {}
        
        # Extract destination first
        destination = self._extract_destination(message)
        if destination:
            entities['destination'] = destination
        
        # Check for greeting queries first
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'welcome']):
            return 'greeting', {}
        
        # Check for farewell queries
        if any(word in message_lower for word in ['bye', 'goodbye', 'thank you', 'thanks', 'see you', 'farewell']):
            return 'farewell', {}
        
        # Check for cost-related queries (broader patterns) - PRIORITY 1
        if any(word in message_lower for word in ['cost', 'price', 'how much', 'fee', 'ticket', 'budget', 'expensive', 'cheap']):
            return 'cost_info', {'destination': destination}
        
        # Check for destination recommendations (broader patterns)
        if any(word in message_lower for word in ['recommend', 'suggest', 'best', 'top', 'good', 'amazing', 'beautiful', 'popular', 'famous']):
            if any(word in message_lower for word in ['beach', 'beaches', 'coastal', 'ocean', 'sea']):
                return 'destination_recommendation', {'interest': 'beaches', 'type': 'beach', 'destination': destination}
            elif any(word in message_lower for word in ['wildlife', 'safari', 'animals', 'elephant', 'leopard', 'whale', 'dolphin']):
                return 'destination_recommendation', {'interest': 'wildlife', 'type': 'wildlife', 'destination': destination}
            elif any(word in message_lower for word in ['cultural', 'historical', 'temple', 'history', 'ancient', 'ruins', 'heritage', 'unesco']):
                return 'destination_recommendation', {'interest': 'cultural sites', 'type': 'cultural', 'destination': destination}
            elif any(word in message_lower for word in ['adventure', 'hiking', 'trek', 'climbing', 'rafting']):
                return 'destination_recommendation', {'interest': 'adventure', 'type': 'adventure', 'destination': destination}
            elif any(word in message_lower for word in ['tea', 'plantation', 'cool', 'hill', 'mountain']):
                return 'destination_recommendation', {'interest': 'tea plantations', 'type': 'nature', 'destination': destination}
            elif any(word in message_lower for word in ['family', 'kids', 'children', 'romantic', 'honeymoon']):
                return 'destination_recommendation', {'interest': 'family friendly', 'type': 'family', 'destination': destination}
            elif any(word in message_lower for word in ['surfing', 'dive', 'diving', 'water sports']):
                return 'destination_recommendation', {'interest': 'water sports', 'type': 'beach', 'destination': destination}
        
        # Check for specific activity questions
        if any(word in message_lower for word in ['what to do', 'activities', 'things to do', 'see', 'visit', 'explore']):
            return 'activities', {'destination': destination}
        
        # Check for transportation queries (broader patterns)
        if any(word in message_lower for word in ['how to get', 'transport', 'travel', 'reach', 'get to', 'go to', 'train', 'bus', 'taxi']):
            return 'transportation', {'destination': destination}
        
        # Check for accommodation queries (broader patterns)
        if any(word in message_lower for word in ['where to stay', 'hotel', 'accommodation', 'lodging', 'resort', 'guesthouse', 'stay']):
            return 'accommodation', {'destination': destination}
        
        # Check for weather queries (broader patterns)
        if any(word in message_lower for word in ['weather', 'climate', 'rainy', 'sunny', 'temperature', 'season']):
            return 'weather', {'destination': destination}
        
        # Check for time-related queries (broader patterns) - PRIORITY 2
        if any(word in message_lower for word in ['when', 'best time', 'season', 'time to visit', 'month']):
            return 'best_time', {'destination': destination}
        
        # Check for duration queries - PRIORITY 3
        if any(word in message_lower for word in ['how long', 'duration', 'days', 'hours']):
            return 'duration', {'destination': destination}
        
        # Check for itinerary queries
        if any(word in message_lower for word in ['itinerary', 'plan', 'schedule', 'day trip', 'tour']):
            return 'itinerary', {'destination': destination}
        
        # Check for destination-specific questions
        if destination:
            if any(word in message_lower for word in ['tell me about', 'what is', 'describe', 'information']):
                return 'destination_info', {'destination': destination}
        
        # Check for general Sri Lanka questions
        if any(word in message_lower for word in ['sri lanka', 'country', 'visa', 'currency', 'language', 'food', 'culture']):
            return 'general_info', {'query': message}
        
        # Default to general response
        return 'general', {'destination': destination}
    
    def _extract_destination(self, message: str) -> str:
        """Extract destination name from message"""
        message_lower = message.lower()
        for destination in self.destination_knowledge.keys():
            if destination in message_lower:
                return destination
        return None
    
    def _extract_duration(self, message: str) -> str:
        """Extract duration from message"""
        import re
        patterns = [
            r'(\d+)\s*day',
            r'(\d+)\s*week',
            r'weekend',
            r'half day',
            r'full day'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(0)
        return None
    
    def _generate_destination_response(self, entities: Dict, preferences: Dict) -> str:
        """Generate destination recommendation response"""
        interest_type = entities.get('type', 'general')
        
        recommendations = {
            'beach': ['Mirissa Beach', 'Unawatuna Beach', 'Arugam Bay', 'Nilaveli Beach', 'Bentota Beach'],
            'wildlife': ['Yala National Park', 'Udawalawe National Park', 'Minneriya National Park', 'Wilpattu National Park'],
            'cultural': ['Sigiriya Lion Rock', 'Temple of the Tooth', 'Ancient City of Polonnaruwa', 'Dambulla Cave Temple', 'Galle Fort'],
            'adventure': ['Ella Rock', 'Little Adam\'s Peak', 'Adam\'s Peak', 'Horton Plains', 'Sinharaja Forest Reserve']
        }
        
        destinations = recommendations.get(interest_type, recommendations['cultural'][:3])
        destinations_str = ', '.join(destinations[:3])
        
        template = self.response_templates['destination_recommendation'][0]
        return template.format(interest=entities['interest'], destinations=destinations_str)
    
    def _generate_time_response(self, entities: Dict) -> str:
        """Generate best time to visit response"""
        destination = entities.get('destination')
        if destination and destination in self.destination_knowledge:
            info = self.destination_knowledge[destination]
            return self.response_templates['best_time'][0].format(
                destination=destination.title(),
                time=info['best_time'],
                additional_info=f"This is when you'll experience the best weather conditions."
            )
        return "The best time to visit most places in Sri Lanka is from December to April during the dry season."
    
    def _generate_cost_response(self, entities: Dict) -> str:
        """Generate cost information response"""
        destination = entities.get('destination')
        if destination and destination in self.destination_knowledge:
            info = self.destination_knowledge[destination]
            return self.response_templates['cost_info'][0].format(
                destination=destination.title(),
                cost=info['cost'],
                additional_info="Prices may vary based on the season and tour operator."
            )
        return "Costs vary widely depending on the destination and activities. Most attractions range from $10-60 USD for foreigners."
    
    def _generate_duration_response(self, entities: Dict) -> str:
        """Generate duration recommendation response"""
        destination = entities.get('destination')
        if destination and destination in self.destination_knowledge:
            info = self.destination_knowledge[destination]
            return self.response_templates['duration'][0].format(
                destination=destination.title(),
                duration=info['duration'],
                additional_info="This allows you to fully experience the main attractions."
            )
        return "Most attractions require 2-4 hours to explore properly, while full experiences may take a full day."
    
    def _generate_activities_response(self, entities: Dict) -> str:
        """Generate activities response"""
        destination = entities.get('destination')
        if destination and destination in self.destination_knowledge:
            info = self.destination_knowledge[destination]
            return self.response_templates['activities'][0].format(
                destination=destination.title(),
                activities=info['activities']
            )
        return "Popular activities include wildlife safaris, cultural site visits, beach activities, hiking, and exploring local cuisine."
    
    def _generate_itinerary_response(self, entities: Dict, preferences: Dict) -> str:
        """Generate itinerary response"""
        destination = entities.get('destination')
        duration = entities.get('duration', '3 days')
        
        if destination == 'kandy':
            itinerary = f"Day 1: Temple of the Tooth and cultural show, Day 2: Botanical Gardens and city tour, Day 3: Day trip to Sigiriya"
        elif destination == 'ella':
            itinerary = f"Day 1: Little Adam's Peak sunrise, Day 2: Ella Rock hike and Nine Arch Bridge, Day 3: Tea plantation visit"
        else:
            itinerary = f"Day 1: Main attractions, Day 2: Local experiences, Day 3: Nature and relaxation"
        
        return self.response_templates['itinerary'][0].format(
            duration=duration,
            destination=destination.title() if destination else 'Sri Lanka',
            itinerary=itinerary
        )
    
    def _generate_general_response(self, message: str, entities: Dict) -> str:
        """Generate general tourism response"""
        # Simple keyword-based responses
        if 'sri lanka' in message.lower():
            return "Sri Lanka is a beautiful island nation known for its stunning beaches, ancient cities, wildlife, and warm hospitality. It's often called the Pearl of the Indian Ocean."
        elif 'visa' in message.lower():
            return "Most tourists need a visa to visit Sri Lanka. You can apply for an Electronic Travel Authorization (ETA) online before your trip."
        elif 'currency' in message.lower():
            return "The currency in Sri Lanka is the Sri Lankan Rupee (LKR). Credit cards are widely accepted in tourist areas, but it's good to carry cash for smaller establishments."
        elif 'transport' in message.lower():
            return "Sri Lanka has various transport options: trains (scenic routes), buses (cheap but crowded), tuk-tuks (short distances), and private drivers for tours."
        else:
            return "I'd be happy to help you plan your Sri Lankan adventure! Feel free to ask me about specific destinations, activities, costs, or travel tips."
    
    def _generate_transportation_response(self, entities: Dict) -> str:
        """Generate transportation response"""
        destination = entities.get('destination')
        if destination:
            transport_info = {
                'colombo': 'You can reach Colombo by plane (Bandaranaike Airport), train from major cities, or bus from anywhere in Sri Lanka.',
                'kandy': 'Take the scenic train from Colombo (3 hours), bus (4 hours), or hire a private car (2.5 hours). The train route is recommended for beautiful views.',
                'ella': 'The train from Kandy or Nuwara Eliya to Ella is one of the most scenic journeys. You can also take a bus or hire a car.',
                'mirissa': 'Take the Southern Highway from Colombo (2 hours), train to Matara then tuk-tuk, or a direct bus.',
                'sigiriya': 'Best reached by private car or taxi from Dambulla (30 minutes). Buses are available but less convenient.'
            }
            return transport_info.get(destination, f"For {destination.title()}, you can use train, bus, or hire a private driver for the most convenient travel.")
        return "Sri Lanka offers trains, buses, tuk-tuks, and private cars. Trains are scenic but slow, buses are cheap, and private cars offer flexibility."
    
    def _generate_accommodation_response(self, entities: Dict) -> str:
        """Generate accommodation response"""
        destination = entities.get('destination')
        if destination:
            accommodation_info = {
                'colombo': 'Colombo has luxury hotels (Cinnamon Grand, Shangri-La), mid-range options (Cinnamon Red), and budget guesthouses in Colombo 5.',
                'kandy': 'Stay near the Temple of the Tooth for convenience, or in the hills for peaceful views. Options range from luxury resorts to budget guesthouses.',
                'ella': 'Ella offers charming guesthouses with mountain views, eco-lodges, and boutique hotels. Book in advance during peak season.',
                'mirissa': 'Beachfront resorts, boutique hotels, and budget guesthouses along the coast. Whale watching packages often include accommodation.',
                'sigiriya': 'Stay in Dambulla or Habarana for better hotel options. Luxury resorts and mid-range hotels are available.'
            }
            return accommodation_info.get(destination, f"{destination.title()} has various accommodation options from luxury resorts to budget guesthouses.")
        return "Sri Lanka offers accommodation for all budgets: luxury resorts, boutique hotels, guesthouses, and homestays. Book in advance during peak season (December-April)."
    
    def _generate_weather_response(self, entities: Dict) -> str:
        """Generate weather response"""
        destination = entities.get('destination')
        if destination:
            weather_info = {
                'colombo': 'Colombo is hot and humid year-round (28-32°C). Rain from May-August, best time December-March.',
                'kandy': 'Kandy is cooler (18-28°C). Rain from October-November and April-May. Best time December-March.',
                'ella': 'Ella is cool and misty (15-25°C). Can rain anytime. Best time January-April for clear views.',
                'mirissa': 'Mirissa is tropical (27-32°C). Monsoon from May-August. Best for beaches November-April.',
                'sigiriya': 'Sigiriya is hot and dry (28-35°C). Rain from October-November. Best time December-April for climbing.'
            }
            return weather_info.get(destination, f"{destination.title()} has tropical climate. Check the best season to visit for optimal weather.")
        return "Sri Lanka has tropical climate with two monsoons. Best time to visit: December-April for south/west coast, May-September for east/north coast."
    
    def _generate_destination_info_response(self, entities: Dict) -> str:
        """Generate destination information response"""
        destination = entities.get('destination')
        if destination and destination in self.destination_knowledge:
            info = self.destination_knowledge[destination]
            return f"{destination.title()} is {info['description']}. Best time to visit: {info['best_time']}. Popular activities: {info['activities']}. Average cost: {info['cost']}."
        return "I'd be happy to tell you about that destination! Please specify which place you're interested in learning about."
    
    def _generate_general_info_response(self, entities: Dict) -> str:
        """Generate general Sri Lanka information response"""
        query = entities.get('query', '').lower()
        
        if 'visa' in query:
            return "Most tourists need a visa to visit Sri Lanka. You can apply for an Electronic Travel Authorization (ETA) online before your trip."
        elif 'currency' in query:
            return "The currency in Sri Lanka is the Sri Lankan Rupee (LKR). Credit cards are widely accepted in tourist areas, but it's good to carry cash for smaller establishments."
        elif 'language' in query:
            return "Sinhala and Tamil are the official languages, but English is widely spoken in tourist areas and major cities."
        elif 'food' in query or 'cuisine' in query:
            return "Sri Lankan cuisine is famous for rice and curry, seafood, hoppers, kottu roti, and spicy dishes. Must-try dishes include lamprais, string hoppers, and wood apple juice."
        elif 'culture' in query:
            return "Sri Lanka has rich Buddhist culture with ancient traditions, colorful festivals, religious ceremonies, and warm hospitality. Major festivals include Vesak, Sinhala/Tamil New Year, and Kandy Esala Perahera."
        else:
            return "Sri Lanka is a beautiful island nation known for its stunning beaches, ancient cities, wildlife, and warm hospitality. It's often called the Pearl of the Indian Ocean."
    
    def _generate_greeting_response(self, entities: Dict) -> str:
        """Generate greeting response"""
        import random
        
        greetings = [
            "Hello! 👋 I'm your AI travel assistant for Sri Lanka. I can help you with destinations, activities, transport, accommodation, and travel tips. What would you like to know about Sri Lanka?",
            "Hi there! 🌴 Welcome to your Sri Lanka travel assistant! I'm here to help you plan the perfect trip. Ask me about beaches, wildlife, cultural sites, or anything related to Sri Lankan tourism!",
            "Greetings! 🇱🇰 I'm excited to help you discover the beauty of Sri Lanka! Whether you're looking for adventure, relaxation, or cultural experiences, I've got you covered. What interests you most?",
            "Welcome! 🏝️ Your Sri Lanka travel expert is here! I can provide recommendations for destinations, activities, weather, transport, and much more. How can I assist your Sri Lankan adventure today?",
            "Hello traveler! 🌺 I'm here to make your Sri Lanka trip unforgettable. From pristine beaches to ancient cities, wildlife safaris to cultural experiences - just ask me anything! What's on your mind?"
        ]
        
        return random.choice(greetings)
    
    def _generate_farewell_response(self, entities: Dict) -> str:
        """Generate farewell response"""
        import random
        
        farewells = [
            "Goodbye! 👋 Thank you for using the Sri Lanka travel assistant. Have a wonderful trip to the Pearl of the Indian Ocean! 🇱🇰",
            "Thank you for chatting! 🌴 I hope you have an amazing time exploring Sri Lanka. Feel free to come back if you need more travel tips!",
            "Safe travels! 🏝️ It was great helping you plan your Sri Lankan adventure. Don't hesitate to ask if you need more information!",
            "Bye for now! 🌺 Wishing you unforgettable experiences in Sri Lanka. Remember, I'm always here to help with your travel questions!",
            "Farewell traveler! 🌺 May your Sri Lanka journey be filled with beautiful memories, stunning sights, and warm hospitality! Ayubowan!"
        ]
        
        return random.choice(farewells)
    
    def is_ready(self) -> bool:
        """Check if the service is ready"""
        return (
            self.embedding_service is not None and
            self.embedding_service.is_ready() and
            hasattr(self, 'tourism_embeddings') and
            self.tourism_embeddings is not None
        )
