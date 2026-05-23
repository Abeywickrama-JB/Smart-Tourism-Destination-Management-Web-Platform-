import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_EMBEDDING_MODEL = 'text-embedding-3-small'
    OPENAI_MAX_RETRIES = 3
    OPENAI_RETRY_DELAY = 1.0
    OPENAI_RATE_LIMIT_DELAY = 0.1
    
    # Legacy Sentence Transformers (fallback)
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    USE_OPENAI_EMBEDDINGS = True
    
    # Chatbot Configuration
    TOURISM_SIMILARITY_THRESHOLD = 0.45  # Lowered from 0.5 for better detection
    MAX_RECOMMENDATIONS = 5
    
    # Tourism Keywords for Intent Detection
    TOURISM_KEYWORDS = [
        'beach', 'mountain', 'temple', 'hotel', 'resort', 'tour', 'guide', 'travel',
        'destination', 'attraction', 'vacation', 'holiday', 'trip', 'safari', 'wildlife',
        'adventure', 'cultural', 'historical', 'nature', 'sri lanka', 'colombo', 'kandy',
        'galle', 'sigiriya', 'ella', 'mirissa', 'yala', 'nuwara eliya', 'anuradhapura',
        'polonnaruwa', 'dambulla', 'trincomalee', 'visit', 'explore', 'discover',
        'experience', 'journey', 'excursion', 'tea', 'plantation', 'surfing', 'diving',
        'hiking', 'trekking', 'climbing', 'wildlife', 'leopard', 'elephant', 'whale',
        'dolphin', 'bird watching', 'photography', 'scenic', 'landscape', 'coastal',
        'island', 'tropical', 'monsoon', 'climate', 'weather', 'season', 'festival',
        'heritage', 'unesco', 'ancient', 'ruins', 'stupa', 'buddha', 'museum', 'art',
        'craft', 'spices', 'cuisine', 'food', 'restaurant', 'shopping', 'market',
        'transport', 'train', 'bus', 'tuk-tuk', 'taxi', 'airport', 'visa', 'currency',
        'accommodation', 'guesthouse', 'homestay', 'budget', 'luxury', 'family',
        'romantic', 'honeymoon', 'backpacker', 'solo', 'group', 'tourist', 'local',
        'traditional', 'cultural', 'religious', 'spiritual', 'meditation', 'yoga',
        'wellness', 'spa', 'ayurveda', 'massage', 'relaxation', 'peaceful', 'beautiful',
        'affordable', 'cheap', 'expensive', 'price', 'cost', 'destinations', 'recommend'
    ]
    
    # Rejection message for non-tourism questions
    TOURISM_REJECTION_MESSAGE = "I'm here to help you with Sri Lankan tourism questions only. Please ask me about destinations, activities, travel tips, or anything related to visiting Sri Lanka!"
    
    # Tourism Question Examples for Similarity Matching
    TOURISM_EXAMPLES = [
        "What are best beaches in Sri Lanka?",
        "How much does it cost to visit Sigiriya?",
        "When is the best time to visit Yala National Park?",
        "Can you recommend cultural sites in Kandy?",
        "What wildlife can I see in Udawalawe?",
        "How do I get to Ella from Colombo?",
        "What adventure activities are available in Ella?",
        "Which are the most popular tourist destinations?",
        "How many days should I spend in Sri Lanka?",
        "What is the best time to visit Sri Lanka?",
        "Can you suggest a 3-day itinerary?",
        "Where can I see elephants in Sri Lanka?",
        "What are the must-visit historical sites?",
        "How much does a safari cost?",
        "What should I pack for a trip to Sri Lanka?",
        "Are there good beaches near Colombo?",
        "What is the best way to travel around Sri Lanka?",
        "Can you recommend a good tour guide?",
        "What are the top attractions in Galle?",
        "Is it safe to travel to Sri Lanka?",
        "What are affordable beach destinations?",
        "Recommend family-friendly destinations",
        "Best places for budget travel",
        "Cheap accommodation options",
        "Affordable safari experiences",
        "What is Sigiriya?",
        "Tell me about Sigiriya",
        "Describe Sigiriya",
        "What is Kandy?",
        "What is Ella?",
        "What is Yala National Park?",
        "Information about Mirissa",
        "What to see in Anuradhapura",
        "Tell me about Polonnaruwa",
        "What is Dambulla",
        "Describe Galle Fort",
        "What is Nuwara Eliya?",
        "Tell me about Kandy",
        "Information about Kandy",
        "Describe Kandy",
        "What is in Kandy",
        "Tell me about Galle",
        "Information about Galle",
        "Describe Galle",
        "What is Trincomalee",
        "Tell me about Anuradhapura",
        "Information about Anuradhapura",
        "Describe Anuradhapura",
        "What is Polonnaruwa",
        "Tell me about Polonnaruwa",
        "Information about Polonnaruwa",
        "Describe Polonnaruwa"
    ]
    
    # Non-Tourism Examples for Negative Training
    NON_TOURISM_EXAMPLES = [
        "What is 2+2?",
        "How do I learn programming?",
        "Who is the president?",
        "What is the capital of France?",
        "How do I cook pasta?",
        "What is the meaning of life?",
        "How do I fix my computer?",
        "What is quantum physics?",
        "How do I invest in stocks?",
        "What is the weather like?",
        "How do I learn English?",
        "What is the best phone to buy?",
        "How do I start a business?",
        "What is machine learning?",
        "How do I lose weight?",
        "What is the best movie?",
        "How do I write a resume?",
        "What is climate change?",
        "How do I learn guitar?",
        "What is cryptocurrency?"
    ]
    
    # Flask Configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5001))  # Changed from 5000 to avoid AirPlay conflict
    HOST = os.environ.get('HOST', '0.0.0.0')
    
    # CORS Configuration
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5176"  # Frontend port
    ]
