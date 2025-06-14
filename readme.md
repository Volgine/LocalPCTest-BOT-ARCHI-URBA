# 🚀 URBA.AI - Guide de Démarrage Rapide

## 🎯 Changements principaux

### Backend amélioré
- **RAG avec ChromaDB** : Stockage vectoriel local des documents
- **Groq AI** : LLM gratuit (Mixtral 8x7B)
- **Upload documents** : PDF, DOCX, TXT
- **Recherche sémantique** : Contexte intelligent

### Frontend futuriste
- **Design cyberpunk** : Néon, glassmorphism
- **Interface interactive** : Animations fluides
- **Dashboard stats** : Temps réel

## 📦 Installation locale

```bash
# 1. Cloner le repo
git clone https://github.com/Volgine/LocalPCTest-BOT-ARCHI-URBA.git
cd LocalPCTest-BOT-ARCHI-URBA

# 2. Installer les dépendances Python
python -m venv .venv
source .venv/bin/activate       # sous Windows : .venv\Scripts\activate
pip install -r backend/requirements.txt

# 3. Configurer Groq
cp backend/.env.example backend/.env
# puis ajoutez votre clé Groq : https://console.groq.com/keys
# vous pouvez aussi définir `ALLOWED_ORIGINS` (liste séparée par des virgules)

# 4. Lancer le serveur
python backend/main.py
```

## 🌐 Déploiement Railway

### Backend
1. Connecter GitHub à Railway
2. Créer nouveau projet depuis votre repo
3. Sélectionner le dossier `/backend`
4. Variables d'environnement :
   ```
   GROQ_API_KEY=gsk_votre_cle_groq
   REDIS_URL=${{Redis.REDIS_URL}}  # Si Redis ajouté
   ALLOWED_ORIGINS=*  # Liste d'origines séparées par des virgules
   ```
5. Deploy!

### Frontend (Vercel)
1. Importer sur Vercel
2. Root directory : `frontend`
3. Ouvrir `index.html` et ajuster la fonction `getApiUrl()` pour qu'elle renvoie l'adresse de votre backend
  ```javascript
  const getApiUrl = () => {
    const host = window.location.hostname;
    if (['localhost', '127.0.0.1'].includes(host)) {
      return 'http://localhost:8000'; // backend local
    }
    // Remplacez l'URL ci-dessous par celle de votre backend déployé
    return 'https://striking-clarity-actelle.up.railway.app';
  };
  const API_URL = getApiUrl();
  console.log('Using API_URL:', API_URL);
  ```
4. Deploy!

## 🔑 Obtenir Groq API Key

1. Aller sur https://console.groq.com
2. Créer un compte (gratuit)
3. Générer une API key
4. Limites gratuites : 30 req/min, 14400 req/jour

## 🧪 Tester les fonctionnalités

### 1. Upload de document
- Cliquer sur "📁 Upload"
- Sélectionner un PDF/DOCX de PLU
- Le document est chunké et indexé

### 2. Questions contextuelles
- "Quelle est la hauteur max en zone UB ?"
- "Puis-je construire une piscine ?"
- Le bot utilise les documents uploadés

### 3. Mode sans document
- Questions générales urbanisme
- Réponses basées sur Groq AI

## ⚡ Optimisations Railway

### Dockerfile optimisé
- Cache des dépendances
- Pre-download du modèle d'embeddings
- Build rapide

### Performance
- ChromaDB persistant
- Redis cache (optionnel)
- Embeddings locaux (pas d'API externe)

## 🛠️ Personnalisation

### Changer le modèle Groq
Dans `main.py` ligne ~180 :
```python
model="llama2-70b-4096"  # Plus rapide
model="mixtral-8x7b-32768"  # Par défaut
```

### Modifier le style
Dans `index.html` :
- Variables CSS `--primary-neon`, `--secondary-neon`

## 📊 Monitoring

- `/api/stats` : Statistiques d'usage
- `/health` : État des services
- Logs Railway : Temps réel

## 🧪 Running tests

Les tests unitaires utilisent `pytest`. Installez d'abord les dépendances de
développement&nbsp;:

```bash
pip install -r backend/requirements.txt -r requirements-dev.txt
pytest -q
```

Le script `load_test.py` permet de lancer des tests de performance
séparés pour évaluer la charge de l'API.

## 🐛 Troubleshooting

### "Groq rate limit"
→ Attendre 1 minute ou utiliser le cache

### "ChromaDB error"
→ Vérifier les permissions du dossier

### "Upload failed"
→ Vérifier la taille < 10MB

## 🔜 Prochaines étapes

1. **Connexion Sogefi API** : Données urbanisme temps réel
2. **Multi-tenancy** : Sessions utilisateurs
3. **Export rapports** : PDF avec analyses
4. **Voice interface** : Questions vocales
5. **Mobile app** : React Native

---

**Support** : Créer une issue sur GitHub
**Stack** : FastAPI + ChromaDB + Groq
