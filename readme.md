# 🚀 URBA.AI - Guide de Démarrage Rapide

## 🎯 Changements principaux

### Backend amélioré
- **RAG avec ChromaDB** : Stockage vectoriel local des documents
- **Groq AI** : LLM gratuit (Mixtral 8x7B)
- **Upload documents** : PDF, DOCX, TXT
- **Recherche sémantique** : Contexte intelligent

### Frontend futuriste
- **Design cyberpunk** : Néon, glassmorphism
- **Three.js 3D** : Particules animées
- **Interface interactive** : Animations fluides
- **Dashboard stats** : Temps réel

## 📦 Installation locale

```bash
# 1. Cloner le repo
git clone https://github.com/Volgine/LocalPCTest-BOT-ARCHI-URBA.git
cd LocalPCTest-BOT-ARCHI-URBA

# 2. Installer (Windows)
install.bat

# 3. Configurer Groq
# Copier backend/.env.example vers backend/.env
# Ajouter votre clé Groq : https://console.groq.com/keys

# 4. Lancer
start.bat

# Ou via Docker
docker-compose up --build
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
   ```
5. Deploy!

### Frontend (Vercel)
1. Importer sur Vercel
2. Root directory : `frontend`
3. Modifier `API_URL` dans index.html : ligne 131
  const API_URL = window.location.hostname === 'localhost' 
            ? 'http://localhost:8000' 
            : localpctest-esemple.up.railway.app;
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
- Animations Three.js ligne ~370
- Effets particules ligne ~350

## 📊 Monitoring

- `/api/stats` : Statistiques d'usage
- `/health` : État des services
- Logs Railway : Temps réel

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
**Stack** : FastAPI + ChromaDB + Groq + Three.js
