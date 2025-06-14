FROM python:3.11-slim

WORKDIR /app

# Installer pip + dépendances système utiles (optionnel)
RUN apt-get update && apt-get install -y build-essential && apt-get clean

# Copier le requirements.txt en premier (bonne pratique Docker)
COPY backend/requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copier le reste des fichiers
COPY backend/ .

# Exposer le port de l'API
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

