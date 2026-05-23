import logging
import sys
import os
import ctypes
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config

from services.embedding_service import EmbeddingService
from services.chatbot_service import ChatbotService
from services.recommendation_service import RecommendationService
from services.sentiment_service import SentimentService

# Manually load torch DLLs from venv to prevent WinError 1114 on Windows
venv_torch_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Lib', 'site-packages', 'torch', 'lib')
if os.path.exists(venv_torch_lib):
    for dll in ['c10.dll', 'torch_cpu.dll']:
        dll_path = os.path.join(venv_torch_lib, dll)
        if os.path.exists(dll_path):
            try:
                ctypes.CDLL(dll_path)
            except Exception:
                pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Python path: {sys.path}")

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app, origins=Config.CORS_ORIGINS)

# Initialize services lazily
_services = {
    'embedding': None,
    'chatbot': None,
    'recommendation': None,
    'sentiment': None
}

def get_embedding_service():
    if _services['embedding'] is None:
        logger.info("Initializing EmbeddingService (Lazy)...")
        _services['embedding'] = EmbeddingService()
    return _services['embedding']

def get_chatbot_service():
    if _services['chatbot'] is None:
        logger.info("Initializing ChatbotService (Lazy)...")
        _services['chatbot'] = ChatbotService(get_embedding_service(), get_recommendation_service())
    return _services['chatbot']

def get_recommendation_service():
    if _services['recommendation'] is None:
        logger.info("Initializing RecommendationService (Lazy)...")
        _services['recommendation'] = RecommendationService(get_embedding_service())
    return _services['recommendation']

def get_sentiment_service():
    if _services['sentiment'] is None:
        logger.info("Initializing SentimentService (Lazy)...")
        _services['sentiment'] = SentimentService()
    return _services['sentiment']

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'services': {
            'embedding': _services['embedding'].is_ready() if _services['embedding'] else "Initializing on first request",
            'chatbot': _services['chatbot'].is_ready() if _services['chatbot'] else "Initializing on first request",
            'recommendation': _services['recommendation'].is_ready() if _services['recommendation'] else "Initializing on first request",
            'sentiment': _services['sentiment'].is_ready() if _services['sentiment'] else "Initializing on first request"
        }
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Chatbot endpoint"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message']
        user_preferences = data.get('preferences', {})
        
        # Check if message is tourism-related
        is_tourism, confidence = get_chatbot_service().is_tourism_related(user_message)
        
        if not is_tourism:
            return jsonify({
                'response': Config.TOURISM_REJECTION_MESSAGE,
                'is_tourism_related': False,
                'confidence': confidence
            })
        
        # Generate response (now returns a dict with text and recommendations)
        chat_result = get_chatbot_service().generate_response(user_message, user_preferences)
        
        return jsonify({
            'response': chat_result['text'],
            'recommendations': chat_result.get('recommendations', []),
            'is_tourism_related': True,
            'confidence': confidence
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    """Get destination recommendations based on user query"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        user_preferences = data.get('preferences', {})
        limit = data.get('limit', Config.MAX_RECOMMENDATIONS)
        
        recommendations = get_recommendation_service().get_recommendations(
            query, user_preferences, limit
        )
        
        return jsonify({
            'recommendations': recommendations,
            'query': query,
            'count': len(recommendations)
        })
        
    except Exception as e:
        logger.exception("Error in recommendations endpoint")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/embeddings', methods=['POST'])
def get_embeddings():
    """Get embeddings for text"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        embedding = get_embedding_service().get_embedding(text)
        
        return jsonify({
            'embedding': embedding.tolist(),
            'text': text,
            'model': Config.EMBEDDING_MODEL
        })
        
    except Exception as e:
        logger.error(f"Error in embeddings endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/sentiment', methods=['POST'])
def analyze_sentiment():
    """Analyze sentiment of text"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        sentiment = get_sentiment_service().analyze_sentiment(text)
        
        return jsonify({
            'sentiment': sentiment,
            'text': text
        })
        
    except Exception as e:
        logger.error(f"Error in sentiment endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/summarize_reviews', methods=['POST'])
def summarize_reviews():
    """Summarize a list of reviews for a destination"""
    try:
        data = request.get_json()
        if not data or 'reviews' not in data:
            return jsonify({'error': 'A list of reviews is required'}), 400
        
        reviews = data['reviews']
        if not isinstance(reviews, list):
            return jsonify({'error': 'Reviews must be a list of strings'}), 400
            
        # For simplicity, if we don't have an OpenAI key setup for summary, 
        # we can just use the sentiment_service to generate a summary
        analyzed_reviews = get_sentiment_service().batch_analyze(reviews)
        summary = get_sentiment_service().generate_summary(analyzed_reviews)
        
        return jsonify({
            'summary': summary['summary'],
            'stats': summary
        })
        
    except Exception as e:
        logger.error(f"Error in summarize_reviews endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/update_destination_reviews', methods=['POST'])
def update_destination_reviews():
    """Update in-memory destination reviews and recompute embeddings"""
    try:
        data = request.get_json()
        if not data or 'destination_name' not in data or 'reviews' not in data:
            return jsonify({'error': 'destination_name and reviews are required'}), 400
            
        get_recommendation_service().update_destination_reviews(data['destination_name'], data['reviews'])
        
        return jsonify({
            'success': True,
            'message': f"Updated reviews for {data['destination_name']}"
        })
    except Exception as e:
        logger.error(f"Error in update_destination_reviews endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/similarity', methods=['POST'])
def calculate_similarity():
    """Calculate similarity between two texts"""
    try:
        data = request.get_json()
        if not data or 'text1' not in data or 'text2' not in data:
            return jsonify({'error': 'Both text1 and text2 are required'}), 400
        
        text1 = data['text1']
        text2 = data['text2']
        
        similarity = get_embedding_service().calculate_similarity(text1, text2)
        
        return jsonify({
            'similarity': similarity,
            'text1': text1,
            'text2': text2
        })
        
    except Exception as e:
        logger.error(f"Error in similarity endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=False
    )
