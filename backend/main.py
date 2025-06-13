from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
import redis
import hashlib
from typing import Optional
import os
from dotenv import load_dotenv
import logging
import time
try:
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.llms import OpenAI
    from langchain.vectorstores import FAISS
    import openai
except ImportError:  # Dependencies may be missing in some environments
    OpenAIEmbeddings = None
    OpenAI = None
    FAISS = None
    openai = None

# Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Assistant Urbanisme API", version="0.1.0")

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis pour le cache (optionnel pour le test)
try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        password=os.getenv('REDIS_PASSWORD', None),
        decode_responses=True
    )
    r.ping()
    cache_enabled = True
    logger.info("✅ Redis connecté - Cache activé")
except Exception as e:
    cache_enabled = False
    logger.warning(f"⚠️ Redis non disponible - Mode sans cache: {e}")

# Configuration API GPU
GPU_API_BASE = "https://apicarto.ign.fr/api/gpu"
GPU_API_KEY = os.getenv('GPU_API_KEY', '')

# Modèles Pydantic
class QueryRequest(BaseModel):
    question: str
    commune: Optional[str] = None
    parcelle: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    source: str
    cached: bool = False
    processing_time: Optional[float] = None

class StatsResponse(BaseModel):
    total_queries: int
    cache_hits: int
    api_calls: int
    cache_enabled: bool

# Fonctions utilitaires
def get_cache_key(query: str) -> str:
    """Génère une clé de cache unique"""
    return f"urbanisme:{hashlib.md5(query.encode()).hexdigest()}"

def increment_stat(stat_name: str):
    """Incrémente une statistique si Redis est disponible"""
    if cache_enabled:
        try:
            r.incr(f"stats:{stat_name}")
        except:
            pass

# Middleware pour logger les requêtes
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {process_time:.3f}s")
    return response

# Routes
@app.get("/")
async def read_root():
    return {
        "message": "Assistant Urbanisme POC - API Ready! 🏗️",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "cache": "enabled" if cache_enabled else "disabled",
        "gpu_api": "configured" if GPU_API_KEY else "not configured"
    }

@app.post("/api/query", response_model=QueryResponse)
async def query_urbanisme(request: QueryRequest):
    """
    Endpoint principal pour les questions d'urbanisme
    """
    start_time = time.time()
    
    # Incrémenter le compteur total
    increment_stat("total")
    
    # Vérifier le cache
    cache_key = get_cache_key(f"{request.commune}:{request.question}")
    
    if cache_enabled:
        cached_result = r.get(cache_key)
        if cached_result:
            increment_stat("cache_hits")
            data = json.loads(cached_result)
            data['cached'] = True
            data['processing_time'] = time.time() - start_time
            return QueryResponse(**data)
    
    # Incrémenter les appels API
    increment_stat("api_calls")
    
    try:
        # Génération de la réponse via le LLM
        try:
            answer = generate_llm_response(request.question, request.commune)
            source = "LLM"
        except Exception as e:
            logger.warning(f"LLM unavailable, fallback to mock: {e}")
            answer = generate_mock_response(request.question, request.commune)
            source = "mock"

        response_data = {
            "answer": answer,
            "source": source,
            "cached": False
        }
        
        # Mettre en cache pour 24h
        if cache_enabled:
            try:
                r.setex(cache_key, 86400, json.dumps(response_data))
            except:
                logger.warning("Impossible de mettre en cache")
        
        response_data['processing_time'] = time.time() - start_time
        return QueryResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Statistiques d'utilisation"""
    stats = {
        "total_queries": 0,
        "cache_hits": 0,
        "api_calls": 0,
        "cache_enabled": cache_enabled
    }
    
    if cache_enabled:
        try:
            stats["total_queries"] = int(r.get("stats:total") or 0)
            stats["cache_hits"] = int(r.get("stats:cache_hits") or 0)
            stats["api_calls"] = int(r.get("stats:api_calls") or 0)
        except:
            logger.warning("Impossible de récupérer les stats")
    
    return StatsResponse(**stats)

@app.delete("/api/cache")
async def clear_cache():
    """Vider le cache (admin only)"""
    if cache_enabled:
        try:
            # Récupérer toutes les clés urbanisme:*
            keys = r.keys("urbanisme:*")
            if keys:
                r.delete(*keys)
            return {"message": f"Cache vidé: {len(keys)} entrées supprimées"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        return {"message": "Cache non activé"}

def generate_llm_response(question: str, commune: Optional[str] = None) -> str:
    """Interroge un LLM à l'aide d'un contexte récupéré depuis un vecteur store."""
    if not (OpenAIEmbeddings and OpenAI and FAISS):
        raise ImportError("LLM dependencies are not installed")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    store_path = os.getenv("VECTOR_STORE_PATH", "vector_store")

    docs = []
    if os.path.exists(store_path):
        try:
            vs = FAISS.load_local(store_path, embeddings)
            docs = vs.similarity_search(question, k=4)
        except Exception as e:
            logger.warning(f"Vector store load failed: {e}")

    context = "\n".join([d.page_content for d in docs])
    prompt = (
        "Réponds à la question suivante en utilisant le contexte fourni s'il est disponible.\n"
        f"Contexte:\n{context}\n\nQuestion: {question}"
    )
    llm = OpenAI(openai_api_key=api_key, temperature=0)
    return llm.predict(prompt).strip()

def generate_mock_response(question: str, commune: Optional[str] = None) -> str:
    """
    Génère des réponses simulées pour le POC
    TODO: Remplacer par l'intégration réelle GPU + IA
    """
    q_lower = question.lower()
    
    # Réponses contextuelles basées sur les mots-clés
    if "hauteur" in q_lower:
        if "maximum" in q_lower or "maximale" in q_lower:
            return "La hauteur maximale autorisée dans cette zone est de 12 mètres (R+3), mesurée depuis le terrain naturel jusqu'au faîtage du toit."
        else:
            return "Les règles de hauteur varient selon le zonage. En zone UA centre-ville : 15m max, en zone UB : 12m max, en zone UC : 9m max."
    
    elif "zone" in q_lower or "zonage" in q_lower:
        if commune and commune.lower() == "montpellier":
            return "Cette parcelle est située en zone UB - Zone urbaine mixte à dominante résidentielle. Les constructions à usage d'habitation, de commerce et de bureau y sont autorisées."
        else:
            return "Le zonage dépend de la commune et du PLU en vigueur. Les principales zones sont : UA (centre-ville), UB (urbain mixte), UC (pavillonnaire), N (naturelle), A (agricole)."
    
    elif "emprise" in q_lower or "sol" in q_lower:
        return "L'emprise au sol maximale est de 60% de la surface de la parcelle en zone UB. Cela inclut l'ensemble des constructions, y compris les annexes."
    
    elif "limite" in q_lower and "propriété" in q_lower:
        return "En zone UB, les constructions peuvent être implantées soit en limite séparative, soit avec un recul minimum de 3 mètres. La hauteur en limite ne peut excéder 3,50 mètres."
    
    elif "stationnement" in q_lower or "parking" in q_lower:
        return "Le nombre de places de stationnement requis dépend de l'usage : Pour l'habitat : 1 place par logement jusqu'à 50m², 2 places au-delà. Pour les bureaux : 1 place pour 50m² de surface de plancher."
    
    elif "permis" in q_lower and "construire" in q_lower:
        return "Un permis de construire est nécessaire pour toute construction nouvelle de plus de 20m² (ou 40m² en zone urbaine avec PLU). Le délai d'instruction est de 2 mois pour une maison individuelle."
    
    elif "piscine" in q_lower:
        return "Une piscine de plus de 10m² nécessite une déclaration préalable (jusqu'à 100m²) ou un permis de construire (au-delà). Elle doit respecter un recul de 3m minimum des limites séparatives."
    
    elif "clôture" in q_lower:
        return "La hauteur maximale des clôtures est généralement de 2 mètres. En limite de voie publique, une partie pleine de 0,80m maximum peut être surmontée d'un dispositif ajouré."
    
    elif "recul" in q_lower or "retrait" in q_lower:
        return "Le recul par rapport à la voirie est généralement de 5 mètres minimum en zone UB. Par rapport aux limites séparatives : soit en limite, soit à une distance égale à la moitié de la hauteur avec un minimum de 3 mètres."
    
    else:
        # Réponse générique
        return f"""Je peux vous aider avec les questions sur :
        
• Le zonage et les règles associées
• Les hauteurs maximales autorisées
• L'emprise au sol et les distances aux limites
• Les règles de stationnement
• Les autorisations nécessaires (permis de construire, déclaration préalable)

Précisez votre question et indiquez si possible la commune et/ou la référence cadastrale concernée."""

# Pour tester localement
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)