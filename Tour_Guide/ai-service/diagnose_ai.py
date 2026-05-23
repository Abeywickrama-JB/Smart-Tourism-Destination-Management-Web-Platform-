import logging
import sys
import os
import ctypes

# Force environment isolation and avoid OpenMP conflicts
os.environ['PYTHONNOUSERSITE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_WAIT_POLICY'] = 'PASSIVE'

# Manually load torch DLLs from venv to prevent WinError 1114
venv_torch_lib = os.path.join(os.getcwd(), 'venv', 'Lib', 'site-packages', 'torch', 'lib')
if os.path.exists(venv_torch_lib):
    for dll in ['c10.dll', 'torch_cpu.dll']:
        dll_path = os.path.join(venv_torch_lib, dll)
        if os.path.exists(dll_path):
            try:
                ctypes.CDLL(dll_path)
            except Exception:
                pass

# Configure logging to console
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def diagnose():
    try:
        logger.info("Starting AI Diagnostic...")
        logger.info(f"Python Executable: {sys.executable}")
        
        # Prune sys.path to remove global Windows Store paths that cause DLL conflicts
        original_path = sys.path[:]
        sys.path = [p for p in sys.path if "PythonSoftwareFoundation" not in p]
        
        if len(sys.path) < len(original_path):
            logger.info(f"Pruned {len(original_path) - len(sys.path)} global paths from sys.path")
        
        # Force DLL directory for torch
        torch_lib = os.path.join(os.path.dirname(sys.executable), "..", "Lib", "site-packages", "torch", "lib")
        if os.path.exists(torch_lib):
            logger.info(f"Adding DLL directory: {torch_lib}")
            os.add_dll_directory(torch_lib)
        
        from services.embedding_service import EmbeddingService
        from services.recommendation_service import RecommendationService
        
        logger.info("Initializing EmbeddingService...")
        embedding_service = EmbeddingService()
        
        logger.info("Initializing RecommendationService...")
        recommendation_service = RecommendationService(embedding_service)
        
        query = "A quiet beach in Sri Lanka"
        logger.info(f"Testing recommendations for query: '{query}'")
        
        results = recommendation_service.get_recommendations(query, limit=3)
        
        logger.info(f"Found {len(results)} recommendations:")
        for i, res in enumerate(results):
            dest = res['destination']
            score = res['similarity_score']
            logger.info(f"  {i+1}. {dest['name']} (Score: {score:.4f})")
            
        logger.info("Diagnostic completed successfully!")
        
    except Exception as e:
        logger.exception("Diagnostic FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    diagnose()
