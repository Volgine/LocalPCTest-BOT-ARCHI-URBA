# 🐍 Image Python optimisée
FROM python:3.11-slim

# 📁 Dossier de travail dans le conteneur
WORKDIR /app

# 📦 Copier le backend (où se trouve requirements.txt et main.py)
COPY backend/ .

# 🔧 Installer les dépendances
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# 📡 Exposer le port
EXPOSE 8000

# 🚀 Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
