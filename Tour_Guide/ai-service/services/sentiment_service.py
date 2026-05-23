import logging
from textblob import TextBlob
from typing import Dict, List
import re

logger = logging.getLogger(__name__)

class SentimentService:
    def __init__(self):
        self.positive_words = [
            'amazing', 'awesome', 'excellent', 'fantastic', 'great', 'wonderful', 'beautiful',
            'stunning', 'breathtaking', 'perfect', 'love', 'loved', 'best', 'incredible',
            'spectacular', 'magnificent', 'gorgeous', 'paradise', 'heaven', 'memorable',
            'unforgettable', 'recommend', 'recommended', 'must visit', 'worth visiting'
        ]
        
        self.negative_words = [
            'terrible', 'awful', 'horrible', 'bad', 'worst', 'disappointing', 'disappointed',
            'poor', 'ugly', 'dirty', 'crowded', 'overpriced', 'expensive', 'boring', 'dull',
            'avoid', 'skip', 'not worth', 'waste of time', 'waste of money', 'don\'t recommend'
        ]
        
        self.tourism_keywords = [
            'destination', 'attraction', 'hotel', 'resort', 'beach', 'mountain', 'park',
            'museum', 'temple', 'tour', 'guide', 'safari', 'wildlife', 'culture', 'food',
            'service', 'staff', 'clean', 'beautiful', 'scenic', 'view', 'experience'
        ]
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text using TextBlob and custom tourism-specific analysis
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            # Basic TextBlob sentiment analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Custom tourism-specific sentiment analysis
            tourism_sentiment = self._analyze_tourism_sentiment(text)
            
            # Combine scores
            combined_score = (polarity * 0.6) + (tourism_sentiment * 0.4)
            
            # Determine sentiment label
            if combined_score > 0.1:
                sentiment_label = 'positive'
            elif combined_score < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            # Extract key aspects
            aspects = self._extract_aspects(text)
            
            return {
                'sentiment_score': round(combined_score, 3),
                'sentiment_label': sentiment_label,
                'polarity': round(polarity, 3),
                'subjectivity': round(subjectivity, 3),
                'tourism_sentiment': round(tourism_sentiment, 3),
                'aspects': aspects,
                'confidence': self._calculate_confidence(combined_score, subjectivity)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.0,
                'tourism_sentiment': 0.0,
                'aspects': [],
                'confidence': 0.0
            }
    
    def _analyze_tourism_sentiment(self, text: str) -> float:
        """Analyze sentiment using tourism-specific keywords"""
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        # Check for tourism-related content
        tourism_count = sum(1 for word in words if word in self.tourism_keywords)
        
        # Calculate tourism sentiment score
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        tourism_sentiment = (positive_count - negative_count) / total_sentiment_words
        
        # Boost score if tourism-related content is present
        if tourism_count > 0:
            tourism_sentiment *= 1.2
        
        return max(-1.0, min(1.0, tourism_sentiment))
    
    def _extract_aspects(self, text: str) -> List[Dict]:
        """Extract tourism-related aspects from text"""
        aspects = []
        text_lower = text.lower()
        
        # Define aspect patterns
        aspect_patterns = {
            'service': ['service', 'staff', 'guide', 'hospitality', 'helpful', 'friendly'],
            'cleanliness': ['clean', 'dirty', 'hygiene', 'sanitary', 'well-maintained'],
            'value': ['price', 'cost', 'expensive', 'cheap', 'worth', 'value', 'affordable'],
            'scenery': ['view', 'scenery', 'beautiful', 'stunning', 'breathtaking', 'landscape'],
            'facilities': ['facilities', 'amenities', 'equipment', 'infrastructure', 'facilities'],
            'accessibility': ['access', 'reachable', 'transport', 'location', 'distance'],
            'food': ['food', 'cuisine', 'restaurant', 'meal', 'dining', 'local food'],
            'activities': ['activities', 'things to do', 'attractions', 'entertainment']
        }
        
        for aspect, keywords in aspect_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Find the context around the keyword
                    context_start = max(0, text_lower.find(keyword) - 50)
                    context_end = min(len(text_lower), text_lower.find(keyword) + 50)
                    context = text[context_start:context_end]
                    
                    # Determine sentiment for this aspect
                    aspect_sentiment = self._get_aspect_sentiment(context)
                    
                    aspects.append({
                        'aspect': aspect,
                        'keyword': keyword,
                        'sentiment': aspect_sentiment,
                        'context': context.strip()
                    })
                    break  # Only add each aspect once
        
        return aspects
    
    def _get_aspect_sentiment(self, context: str) -> str:
        """Determine sentiment for a specific aspect context"""
        context_lower = context.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in context_lower)
        negative_count = sum(1 for word in self.negative_words if word in context_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_confidence(self, sentiment_score: float, subjectivity: float) -> float:
        """Calculate confidence score for the sentiment analysis"""
        # Higher confidence for more subjective text with stronger sentiment
        confidence = abs(sentiment_score) * 0.7 + subjectivity * 0.3
        return round(min(1.0, confidence), 3)
    
    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """Analyze sentiment for multiple texts"""
        results = []
        for text in texts:
            result = self.analyze_sentiment(text)
            results.append(result)
        return results
    
    def generate_summary(self, reviews: List[Dict]) -> Dict:
        """Generate sentiment summary from multiple reviews"""
        if not reviews:
            return {
                'total_reviews': 0,
                'average_sentiment': 0.0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'common_aspects': [],
                'summary': 'No reviews to analyze.'
            }
        
        total_sentiment = 0
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        all_aspects = []
        
        for review in reviews:
            sentiment = review.get('sentiment_label', 'neutral')
            sentiment_counts[sentiment] += 1
            total_sentiment += review.get('sentiment_score', 0)
            
            aspects = review.get('aspects', [])
            all_aspects.extend(aspects)
        
        # Calculate average sentiment
        average_sentiment = total_sentiment / len(reviews)
        
        # Find common aspects
        aspect_counts = {}
        for aspect in all_aspects:
            aspect_name = aspect['aspect']
            if aspect_name not in aspect_counts:
                aspect_counts[aspect_name] = {'positive': 0, 'negative': 0, 'neutral': 0}
            aspect_counts[aspect_name][aspect['sentiment']] += 1
        
        # Generate summary
        summary = self._generate_sentiment_summary(
            len(reviews), average_sentiment, sentiment_counts, aspect_counts
        )
        
        return {
            'total_reviews': len(reviews),
            'average_sentiment': round(average_sentiment, 3),
            'sentiment_distribution': sentiment_counts,
            'common_aspects': aspect_counts,
            'summary': summary
        }
    
    def _generate_sentiment_summary(self, total_reviews: int, avg_sentiment: float, 
                                  sentiment_counts: Dict, aspect_counts: Dict) -> str:
        """Generate a human-readable sentiment summary"""
        if total_reviews == 0:
            return 'No reviews to analyze.'
        
        # Overall sentiment
        if avg_sentiment > 0.3:
            overall = 'Most visitors had positive experiences'
        elif avg_sentiment < -0.3:
            overall = 'Most visitors had negative experiences'
        else:
            overall = 'Visitors had mixed experiences'
        
        # Key findings
        findings = []
        
        # Most common aspects
        if aspect_counts:
            most_discussed = max(aspect_counts.keys(), key=lambda x: sum(aspect_counts[x].values()))
            aspect_data = aspect_counts[most_discussed]
            
            if aspect_data['positive'] > aspect_data['negative']:
                findings.append(f"visitors praised the {most_discussed}")
            elif aspect_data['negative'] > aspect_data['positive']:
                findings.append(f"visitors mentioned issues with {most_discussed}")
        
        # Specific patterns
        if sentiment_counts['positive'] > sentiment_counts['negative'] * 2:
            findings.append("overwhelmingly positive feedback")
        elif sentiment_counts['negative'] > sentiment_counts['positive']:
            findings.append("significant concerns were raised")
        
        # Construct summary
        if findings:
            return f"{overall}. {', '.join(findings)}."
        else:
            return f"{overall}."
    
    def is_ready(self) -> bool:
        """Check if the service is ready"""
        return True
