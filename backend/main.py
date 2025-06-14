from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import redis
import hashlib
from typing import Optional, List
import os
from dotenv import load_dotenv
import logging
import time
import chromadb
from chromadb.utils import embedding_functions
import PyPDF2
import io
import docx
from groq import Groq
from datetime import datetime
from rag_utils import retrieve_context, generate_llm_answer

# Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Assistant Urbanisme AI", version="2.0.0")

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis pour le cache
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

# Configuration Groq
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    logger.info("✅ Groq configuré")
else:
    groq_client = None
    logger.warning("⚠️ Groq non configuré - Mode simulation")

# Configuration ChromaDB pour le RAG
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Collection pour les documents d'urbanisme
collection = chroma_client.get_or_create_collection(
    name="urbanisme_docs",
    embedding_function=embedding_function
)

# Modèles Pydantic
class QueryRequest(BaseModel):
    question: str
    commune: Optional[str] = None
    parcelle: Optional[str] = None
    use_context: bool = True
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    source: str
    cached: bool = False
    processing_time: Optional[float] = None
    confidence: Optional[float] = None
    sources_used: Optional[List[str]] = None

class DocumentInfo(BaseModel):
    filename: str
    doc_type: str
    size: int
    chunks: int
    upload_date: str

class StatsResponse(BaseModel):
    total_queries: int
    cache_hits: int
    api_calls: int
    documents_indexed: int
    cache_enabled: bool
    ai_model: str

# Fonctions utilitaires
def extract_text_from_pdf(file_content: bytes) -> str:
    """Extrait le texte d'un PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Erreur extraction PDF: {e}")
        return ""

def extract_text_from_docx(file_content: bytes) -> str:
    """Extrait le texte d'un DOCX"""
    try:
        doc = docx.Document(file_content)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Erreur extraction DOCX: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Divise le texte en chunks avec overlap"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

async def query_groq(prompt: str, context: str = "") -> str:
    """Interroge Groq avec le contexte RAG"""
    if not groq_client:
        return generate_mock_response(prompt)
    
    try:
        messages = [
            {
                "role": "system",
                "content": """Tu es un assistant expert en urbanisme et architecture. 
                Tu utilises le contexte fourni pour répondre de manière précise et technique.
                Si le contexte ne contient pas l'information, tu l'indiques clairement."""
            }
        ]
        
        if context:
            messages.append({
                "role": "user",
                "content": f"Contexte des documents:\n{context}\n\nQuestion: {prompt}"
            })
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })
        
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            temperature=0.3,
            max_tokens=1024
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Erreur Groq: {e}")
        return generate_mock_response(prompt)

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

# Routes
@app.get("/")
async def read_root():
    return {
        "message": "Assistant Urbanisme AI 2.0 - Powered by RAG & Groq 🏗️",
        "version": "2.0.0",
        "features": ["RAG", "Document Upload", "AI Chat", "Cache"],
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "cache": "enabled" if cache_enabled else "disabled",
        "ai_model": "groq" if groq_client else "simulation",
        "rag": "chromadb",
        "documents": collection.count()
    }

@app.post("/api/upload", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """Upload et indexe un document dans le RAG"""
    try:
        # Lire le fichier
        content = await file.read()
        filename = file.filename
        
        # Extraire le texte selon le type
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(content)
            doc_type = "pdf"
        elif filename.lower().endswith('.docx'):
            text = extract_text_from_docx(content)
            doc_type = "docx"
        elif filename.lower().endswith('.txt'):
            text = content.decode('utf-8')
            doc_type = "txt"
        else:
            raise HTTPException(status_code=400, detail="Format non supporté")
        
        if not text:
            raise HTTPException(status_code=400, detail="Impossible d'extraire le texte")
        
        # Chunker le texte
        chunks = chunk_text(text)
        
        # Indexer dans ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}_{i}_{session_id or 'global'}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "filename": filename,
                "chunk_index": i,
                "session_id": session_id or "global",
                "upload_date": datetime.now().isoformat()
            })
        
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        
        return DocumentInfo(
            filename=filename,
            doc_type=doc_type,
            size=len(content),
            chunks=len(chunks),
            upload_date=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erreur upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse)
async def query_urbanisme(request: QueryRequest):
    """Endpoint principal pour les questions d'urbanisme avec RAG"""
    start_time = time.time()
    
    increment_stat("total")
    
    # Vérifier le cache
    cache_key = get_cache_key(f"{request.commune}:{request.question}:{request.use_context}")
    
    if cache_enabled:
        cached_result = r.get(cache_key)
        if cached_result:
            increment_stat("cache_hits")
            data = json.loads(cached_result)
            data['cached'] = True
            data['processing_time'] = time.time() - start_time
            return QueryResponse(**data)
    
    increment_stat("api_calls")
    
    try:
        context = ""
        sources_used = []

        if request.use_context:
            snippets = retrieve_context(request.question)
            if snippets:
                context = "\n\n".join(f"[Snippet {i+1}]: {s}" for i, s in enumerate(snippets))

        answer = await generate_llm_answer(request.question, context, GROQ_API_KEY)

        confidence = None
        
        response_data = {
            "answer": answer,
            "source": "RAG + Groq AI" if context else "Groq AI",
            "cached": False,
            "confidence": confidence,
            "sources_used": sources_used if sources_used else None
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
        "documents_indexed": collection.count(),
        "cache_enabled": cache_enabled,
        "ai_model": "groq" if groq_client else "simulation"
    }
    
    if cache_enabled:
        try:
            stats["total_queries"] = int(r.get("stats:total") or 0)
            stats["cache_hits"] = int(r.get("stats:cache_hits") or 0)
            stats["api_calls"] = int(r.get("stats:api_calls") or 0)
        except:
            logger.warning("Impossible de récupérer les stats")
    
    return StatsResponse(**stats)

@app.delete("/api/documents/{session_id}")
async def clear_session_documents(session_id: str):
    """Supprime les documents d'une session"""
    try:
        # Récupérer les IDs des documents de la session
        results = collection.get(
            where={"session_id": session_id}
        )
        
        if results['ids']:
            collection.delete(ids=results['ids'])
            return {"message": f"{len(results['ids'])} documents supprimés"}
        else:
            return {"message": "Aucun document trouvé pour cette session"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_mock_response(question: str) -> str:
    """Génère des réponses simulées améliorées"""
    q_lower = question.lower()
    
    # Base de réponses plus élaborées
    responses = {
        "hauteur": """D'après la réglementation en vigueur :
        
        • Zone UA (centre-ville) : 15m max (R+4)
        • Zone UB (urbain mixte) : 12m max (R+3)  
        • Zone UC (pavillonnaire) : 9m max (R+2)
        • Zone UE (activités) : 12m max sauf dérogation
        
        La hauteur se mesure depuis le terrain naturel jusqu'au faîtage.""",
        
        "emprise": """L'emprise au sol maximale autorisée :
        
        • Zone UA : 80% de la parcelle
        • Zone UB : 60% de la parcelle
        • Zone UC : 40% de la parcelle
        • Zone N/A : 20% maximum
        
        Incluant toutes constructions et annexes.""",
        
        "recul": """Les règles de recul obligatoires :
        
        • Voirie : 5m minimum (3m en UA)
        • Limites séparatives : H/2 min 3m
        • Fond de parcelle : 5m minimum
        • Entre bâtiments : H+3m minimum""",
        
        "default": """Je peux vous aider sur :
        
        • Règles de hauteur et gabarit
        • Emprise au sol et COS
        • Distances et prospects
        • Zonage PLU/PLUi
        • Autorisations d'urbanisme
        
        Précisez votre question ou uploadez vos documents PLU."""
    }
    
    for key, response in responses.items():
        if key in q_lower:
            return response
    
    return responses["default"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
