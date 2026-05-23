import logging
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
        self.max_recommendations = Config.MAX_RECOMMENDATIONS
        
        # Sample destination database (in production, this would come from the main database)
        self.destinations = []
        
        # Precompute embeddings for all destinations
        self.destination_embeddings = None
        # Removed automatic precompute from init to avoid circular wait
    
    def _initialize_destinations(self) -> List[Dict]:
        """Initialize destination database from Spring Boot backend"""
        try:
            import requests
            logger.info("Fetching destinations from backend...")
            # Retry mechanism for backend availability
            for attempt in range(5):
                try:
                    response = requests.get('http://localhost:8080/api/destinations', timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        destinations = []
                        for d in data:
                            dest = {
                                'id': d.get('id'),
                                'name': d.get('name', ''),
                                'category': d.get('category', ''),
                                'description': d.get('description', ''),
                                'location': d.get('location', ''),
                                'rating': d.get('rating', 0.0),
                                'average_cost': d.get('averageCost', 0.0),
                                'best_time_to_visit': d.get('bestTimeToVisit', ''),
                                'duration': d.get('estimatedDuration', ''),
                                'difficulty_level': d.get('difficultyLevel', ''),
                                'is_popular': d.get('isPopular', False),
                                'is_family_friendly': d.get('isFamilyFriendly', False),
                                'tags': [], 
                                'summarized_reviews': d.get('summarizedReviews', ''),
                                'safety_risk': d.get('safetyRisk') if d.get('safetyRisk') is not None and d.get('safetyRisk') > 0 else 5.0
                            }
                            if d.get('facilities'):
                                import json
                                try:
                                    dest['tags'] = json.loads(d.get('facilities')) if isinstance(d.get('facilities'), str) else d.get('facilities')
                                except:
                                    dest['tags'] = [d.get('facilities')]
                            destinations.append(dest)
                        logger.info(f"Successfully loaded {len(destinations)} destinations from backend.")
                        return destinations
                except Exception as e:
                    import time
                    logger.warning(f"Backend not ready (attempt {attempt+1}/5): {e}")
                    time.sleep(5)
            
            logger.error("Failed to fetch destinations after 5 attempts. Using empty list.")
            return []
        except Exception as e:
            logger.error(f"Error initializing destinations: {e}")
            return []
    
    def _precompute_destination_embeddings(self):
        """Precompute embeddings for all destinations"""
        try:
            logger.info("Precomputing destination embeddings")
            destination_texts = []
            
            for dest in self.destinations:
                # Combine name, description, and tags for better embedding (plus the summarized reviews!)
                text = f"{dest['name']} {dest['description']} {' '.join(dest.get('tags', []))} {dest.get('summarized_reviews', '')}"
                destination_texts.append(text)
            
            self.destination_embeddings = self.embedding_service.get_embedding(destination_texts)
            logger.info("Destination embeddings computed successfully")
            
        except Exception as e:
            logger.error(f"Error precomputing destination embeddings: {str(e)}")
            self.destination_embeddings = None
            
    def update_destination_reviews(self, destination_name: str, reviews: str):
        """Update reviews for a destination and recompute its embeddings."""
        for dest in self.destinations:
            if dest['name'] == destination_name:
                dest['summarized_reviews'] = reviews
                logger.info(f"Updated reviews for {destination_name}")
                self._precompute_destination_embeddings()
                break
    
    def get_recommendations(self, query: str, user_preferences: Dict = None, limit: int = None) -> List[Dict]:
        try:
            limit = limit or self.max_recommendations
            user_preferences = user_preferences or {}
            
            # Lazy load destinations if needed
            if not self.destinations:
                logger.info("Lazy loading destinations...")
                self.destinations = self._initialize_destinations()
                if self.destinations:
                    self._precompute_destination_embeddings()
            
            if not self.destinations:
                logger.warning("No destinations available for recommendations.")
                return []

            logger.info(f"Getting recommendations for query: {query}")
            
            # Get query embedding
            query_embedding = self.embedding_service.get_embedding(query)
            
            # Calculate similarities with all destinations
            similarities = self.embedding_service.batch_similarity(query, [
                f"{dest['name']} {dest['description']} {' '.join(dest.get('tags', []))} {dest.get('summarized_reviews', '')}"
                for dest in self.destinations
            ])
            
            # Create list of (destination, similarity) tuples
            destination_similarities = list(zip(self.destinations, similarities))
            
            # Define vibe keywords for boosting
            vibe_boosts = {
                'sunset': ['sunset', 'stunning sunsets', 'sunset views'],
                'beach': ['beach', 'ocean', 'coastal', 'sand'],
                'peaceful': ['peaceful', 'relaxation', 'calm', 'quiet', 'serene'],
                'adventure': ['adventure', 'hike', 'trek', 'surfing', 'climbing'],
                'historical': ['historical', 'ancient', 'heritage', 'heritage site'],
                'wildlife': ['wildlife', 'safari', 'animals', 'leopard', 'elephant']
            }
            
            # Apply preference-based filtering and scoring
            scored_destinations = self._apply_preference_scoring(destination_similarities, user_preferences)
            
            # Apply Vibe Keyword Boosting and Thresholding
            query_lower = query.lower()
            boosted_destinations = []
            
            # Use a conservative threshold to filter out garbage semantic matches
            # but allow vibe boosts to bring relevant items up
            similarity_threshold = 0.35
            
            for dest, score in scored_destinations:
                final_score = score
                has_vibe_match = False
                
                for vibe, keywords in vibe_boosts.items():
                    if vibe in query_lower or any(kw in query_lower for kw in keywords):
                        # Construct a search text for the destination to check for keywords
                        search_text = f"{dest['name']} {dest['description']} {' '.join(dest.get('tags', []))}".lower()
                        if any(kw in search_text for kw in keywords) or vibe == dest['category']:
                            final_score += 0.25 # Significant boost for matching vibes
                            has_vibe_match = True
                            logger.info(f"Boosting {dest['name']} for vibe: {vibe}")
                
                # Filter results that are neither similar enough nor a strong vibe match
                if final_score >= similarity_threshold or has_vibe_match:
                    # Cap final score at 1.0 (100%)
                    final_score = min(final_score, 1.0)
                    boosted_destinations.append((dest, final_score))
            
            # Sort by final score (descending)
            boosted_destinations.sort(key=lambda x: x[1], reverse=True)
            
            # Return top recommendations (using the provided limit or a sensible default)
            final_limit = limit if limit is not None else 10
            recommendations = []
            for dest, final_score in boosted_destinations[:final_limit]:
                recommendation = {
                    'destination': dest,
                    'similarity_score': final_score,
                    'recommendation_reason': self._generate_recommendation_reason(dest, query, user_preferences)
                }
                recommendations.append(recommendation)
            
            logger.info(f"Returning {len(recommendations)} recommendations (with thresholding and capping)")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    def _apply_preference_scoring(self, destination_similarities: List, preferences: Dict) -> List:
        """Apply user preference-based scoring to destinations"""
        scored_destinations = []
        
        for dest, base_similarity in destination_similarities:
            final_score = base_similarity
            
            # Category preference
            preferred_categories = preferences.get('travel_interests', [])
            if isinstance(preferred_categories, str):
                preferred_categories = [preferred_categories]
            
            if dest['category'] in preferred_categories:
                final_score += 0.2
            
            # Budget preference
            max_budget = preferences.get('max_budget')
            if max_budget and dest['average_cost'] <= max_budget:
                final_score += 0.1
            elif max_budget and dest['average_cost'] > max_budget:
                final_score -= 0.2
            
            # Family-friendly preference
            if preferences.get('travel_companions') == 'family' and dest['is_family_friendly']:
                final_score += 0.15
            
            # Difficulty level preference
            activity_level = preferences.get('activity_level', 'moderate')
            if activity_level == 'easy' and dest['difficulty_level'] == 'easy':
                final_score += 0.1
            elif activity_level == 'adventurous' and dest['difficulty_level'] in ['moderate', 'challenging']:
                final_score += 0.1
            
            # Popular destinations bonus
            if dest['is_popular']:
                final_score += 0.05
            
            # Rating bonus
            if dest['rating'] >= 4.5:
                final_score += 0.1
            
            # Seasonal preference matching
            seasonal_preference = preferences.get('seasonal_preference')
            if seasonal_preference:
                best_time = dest.get('best_time_to_visit', '').lower()
                if seasonal_preference == 'january-march' and any(month in best_time for month in ['january', 'february', 'march', 'december']):
                    final_score += 0.15
                elif seasonal_preference == 'april-june' and any(month in best_time for month in ['april', 'may', 'june']):
                    final_score += 0.15
                elif seasonal_preference == 'july-september' and any(month in best_time for month in ['july', 'august', 'september']):
                    final_score += 0.15
                elif seasonal_preference == 'october-december' and any(month in best_time for month in ['october', 'november', 'december']):
                    final_score += 0.15
                elif seasonal_preference == 'year-round':
                    final_score += 0.05
            
            # Safety risk optimization (Penalty for higher risk)
            # Risk is 1.0 (safe) to 10.0 (risky)
            safety_risk = dest.get('safety_risk', 5.0)
            if safety_risk > 0:
                # Deduct up to 0.3 for high risk (10.0 risk = -0.3, 1.0 risk = 0.0)
                risk_penalty = ((safety_risk - 1.0) / 9.0) * 0.3
                final_score -= risk_penalty
            
            scored_destinations.append((dest, final_score))
        
        return scored_destinations
    
    def _generate_recommendation_reason(self, destination: Dict, query: str, preferences: Dict) -> str:
        """Generate a reason for the recommendation"""
        reasons = []
        query_lower = query.lower()
        
        # Enhanced semantic matching for relaxation queries
        if any(word in query_lower for word in ['relax', 'relaxing', 'relaxation', 'peaceful', 'calm', 'quiet', 'serene']):
            if destination['category'] == 'beach':
                reasons.append("perfect for beach relaxation")
            elif destination['category'] == 'nature':
                reasons.append("ideal for peaceful nature experience")
            elif any(tag in destination.get('tags', []) for tag in ['Meditation', 'Yoga', 'Spa']):
                reasons.append("offers wellness and relaxation activities")
        
        # Enhanced semantic matching for sunset queries
        if any(word in query_lower for word in ['sunset', 'sunrise', 'dawn', 'dusk', 'golden hour']):
            if any(tag in destination.get('tags', []) for tag in ['Sunset Views', 'Sunrise Views', 'Photography']):
                reasons.append("spectacular sunset/sunrise views")
            elif destination['category'] == 'beach':
                reasons.append("beautiful sunset over the ocean")
            elif destination['category'] in ['adventure', 'nature']:
                reasons.append("great scenic views for sunset")
        
        # Category-based reasons
        if destination['category'] == 'beach' and any(word in query_lower for word in ['beach', 'coast', 'sea', 'ocean', 'shore']):
            reasons.append("perfect beach destination")
        elif destination['category'] == 'wildlife' and any(word in query_lower for word in ['wildlife', 'animals', 'safari', 'elephant', 'leopard']):
            reasons.append("excellent for wildlife viewing")
        elif destination['category'] == 'historical' and any(word in query_lower for word in ['historical', 'ancient', 'history', 'heritage']):
            reasons.append("rich historical significance")
        elif destination['category'] == 'adventure' and any(word in query_lower for word in ['adventure', 'hike', 'trek', 'climbing', 'exciting']):
            reasons.append("great for adventure activities")
        elif destination['category'] == 'nature' and any(word in query_lower for word in ['nature', 'forest', 'green', 'natural']):
            reasons.append("perfect nature destination")
        
        # Rating-based reasons
        if destination['rating'] >= 4.7:
            reasons.append("highly rated by visitors")
        
        # Cost-based reasons
        if destination['average_cost'] == 0:
            reasons.append("free to visit")
        elif destination['average_cost'] <= 20:
            reasons.append("affordable")
        
        # Family-friendly reasons
        if destination['is_family_friendly'] and preferences.get('travel_companions') == 'family':
            reasons.append("family-friendly")
        
        # Popular destination reasons
        if destination['is_popular']:
            reasons.append("popular among tourists")
        
        # Seasonal preference reasons
        seasonal_preference = preferences.get('seasonal_preference')
        if seasonal_preference:
            best_time = destination.get('best_time_to_visit', '').lower()
            if seasonal_preference == 'january-march' and any(month in best_time for month in ['january', 'february', 'march', 'december']):
                reasons.append("perfect for your preferred travel time")
            elif seasonal_preference == 'april-june' and any(month in best_time for month in ['april', 'may', 'june']):
                reasons.append("ideal for your travel period")
            elif seasonal_preference == 'july-september' and any(month in best_time for month in ['july', 'august', 'september']):
                reasons.append("great for your preferred season")
            elif seasonal_preference == 'october-december' and any(month in best_time for month in ['october', 'november', 'december']):
                reasons.append("perfect timing for your visit")
            elif seasonal_preference == 'year-round':
                reasons.append("suitable for year-round travel")
        
        if not reasons:
            reasons.append("matches your interests")
        
        return f"Recommended because it's {', '.join(reasons[:3])}"
    
    def get_similar_destinations(self, destination_id: int, limit: int = 5) -> List[Dict]:
        try:
            target_dest = None
            for dest in self.destinations:
                if dest['id'] == destination_id:
                    target_dest = dest
                    break
            
            if not target_dest:
                return []
            
            query = f"{target_dest['name']} {target_dest['description']} {' '.join(target_dest.get('tags', []))} {target_dest.get('summarized_reviews', '')}"
            
            recommendations = self.get_recommendations(query, limit=limit + 1)
            
            similar_destinations = [
                rec for rec in recommendations 
                if rec['destination']['id'] != destination_id
            ][:limit]
            
            return similar_destinations
            
        except Exception as e:
            logger.error(f"Error getting similar destinations: {str(e)}")
            return []
    
    def get_category_recommendations(self, category: str, limit: int = 5) -> List[Dict]:
        try:
            category_destinations = [
                dest for dest in self.destinations 
                if dest['category'] == category
            ]
            
            category_destinations.sort(key=lambda x: x['rating'], reverse=True)
            
            recommendations = []
            for dest in category_destinations[:limit]:
                recommendation = {
                    'destination': dest,
                    'similarity_score': dest['rating'] / 5.0,
                    'recommendation_reason': f"top-rated {category} destination"
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting category recommendations: {str(e)}")
            return []
    
    def is_ready(self) -> bool:
        return (
            self.embedding_service is not None and
            self.embedding_service.is_ready() and
            self.destination_embeddings is not None and
            len(self.destinations) > 0
        )
