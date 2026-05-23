import numpy as np
import openai
from sklearn.metrics.pairwise import cosine_similarity
import logging
from typing import List, Union
from config import Config

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = None
        self.model_name = Config.OPENAI_EMBEDDING_MODEL
        self.use_openai = Config.USE_OPENAI_EMBEDDINGS
        self.fallback_model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model - prefer OpenAI, fallback to sentence transformers"""
        try:
            if self.use_openai and Config.OPENAI_API_KEY:
                logger.info(f"Loading OpenAI embedding model: {self.model_name}")
                self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
                logger.info("OpenAI embedding model loaded successfully")
            else:
                logger.info("OpenAI not available, trying sentence transformers fallback...")
                self._load_sentence_transformer()
        except Exception as e:
            logger.error(f"Error loading OpenAI embedding model: {str(e)}")
            logger.info("Attempting sentence transformers fallback...")
            try:
                self._load_sentence_transformer()
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                raise
    
    def _load_sentence_transformer(self):
        """Load sentence transformer as fallback"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading sentence transformer model: {Config.EMBEDDING_MODEL}")
            self.fallback_model = SentenceTransformer(Config.EMBEDDING_MODEL)
            self.use_openai = False
            logger.info("Sentence transformer fallback loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentence transformer fallback: {str(e)}")
            raise
    
    def get_embedding(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Get embedding for a single text or list of texts
        """
        try:
            if isinstance(text, str):
                text = [text]
            
            if self.use_openai and self.client:
                # Use OpenAI embeddings
                embeddings_list = []
                for t in text:
                    response = self.client.embeddings.create(
                        model=self.model_name,
                        input=t
                    )
                    embedding = np.array(response.data[0].embedding)
                    embeddings_list.append(embedding)
                
                embeddings = np.array(embeddings_list)
                return embeddings[0] if len(embeddings) == 1 else embeddings
            elif self.fallback_model:
                # Use sentence transformers fallback
                embeddings = self.fallback_model.encode(text, convert_to_numpy=True)
                return embeddings[0] if len(embeddings) == 1 else embeddings
            else:
                raise Exception("No embedding model available")
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        try:
            embedding1 = self.get_embedding(text1)
            embedding2 = self.get_embedding(text2)
            
            embedding1 = embedding1.reshape(1, -1)
            embedding2 = embedding2.reshape(1, -1)
            
            similarity = cosine_similarity(embedding1, embedding2)[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            raise
    
    def find_most_similar(self, query: str, candidates: List[str], top_k: int = 5) -> List[tuple]:
        """Find most similar texts to query from candidates"""
        try:
            if not candidates:
                return []
            
            query_embedding = self.get_embedding(query)
            candidate_embeddings = self.get_embedding(candidates)
            
            similarities = cosine_similarity(
                query_embedding.reshape(1, -1),
                candidate_embeddings
            )[0]
            
            results = list(zip(candidates, similarities))
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding most similar texts: {str(e)}")
            raise
    
    def batch_similarity(self, query: str, candidates: List[str]) -> List[float]:
        """Calculate similarity between query and multiple candidates"""
        try:
            if not candidates:
                return []
            
            query_embedding = self.get_embedding(query)
            candidate_embeddings = self.get_embedding(candidates)
            
            similarities = cosine_similarity(
                query_embedding.reshape(1, -1),
                candidate_embeddings
            )[0]
            
            return [float(sim) for sim in similarities]
            
        except Exception as e:
            logger.error(f"Error in batch similarity: {str(e)}")
            raise
    
    def is_ready(self) -> bool:
        """Check if the service is ready"""
        return (self.use_openai and self.client is not None) or (self.fallback_model is not None)
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        if self.use_openai and self.client:
            return {
                'model_name': self.model_name,
                'is_ready': self.is_ready(),
                'embedding_type': 'openai',
                'embedding_dimension': 1536  # OpenAI text-embedding-3-small dimension
            }
        elif self.fallback_model:
            return {
                'model_name': Config.EMBEDDING_MODEL,
                'is_ready': self.is_ready(),
                'embedding_type': 'sentence_transformers',
                'embedding_dimension': self.fallback_model.get_sentence_embedding_dimension()
            }
        else:
            return {
                'model_name': 'none',
                'is_ready': False,
                'embedding_type': 'none',
                'embedding_dimension': None
            }
