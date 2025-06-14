# 🖥️ Guide Test Local - Assistant Urbanisme POC

## 📋 Vue d'ensemble
Test complet de l'application sur votre PC Windows en local, sans déploiement cloud.

**Repository GitHub** : https://github.com/Volgine/LocalPCTest-BOT-ARCHI-URBA

---

## 🚀 Installation (première fois)

### 1. **Prérequis**
- Python 3.8+ installé
- Cloner le projet : `git clone https://github.com/Volgine/LocalPCTest-BOT-ARCHI-URBA.git`
- Terminal/CMD disponible

### 2. **Installation automatique**
- **Double-clic sur `install.bat`**
- Ce script automatise :
  - Création de l'environnement virtuel Python
  - Installation des dépendances (FastAPI, uvicorn, etc.)
  - Création du fichier .env depuis .env.example
  - Affichage des instructions

### 3. **Vérification**
- Un dossier `venv` est créé dans `/backend`
- Le fichier `.env` existe dans `/backend`
- Message "Installation terminée !" s'affiche

### 4. **Configuration IA**
Ajoutez vos clés dans `/backend/.env` et configurez l'index vectoriel :

```env
OPENAI_API_KEY=
VECTOR_STORE_PATH=./data/index.faiss
```

Installez également les dépendances LLM/RAG (langchain, faiss-cpu, openai, tqdm)
si ce n'est pas déjà fait :

```bash
cd backend
venv\Scripts\activate  # ou `source venv/bin/activate` sous Linux/Mac
pip install -r requirements.txt

```

### Installation des dépendances de test
Si vous souhaitez exécuter les tests, installez également :

```bash
pip install -r requirements-test.txt
```

#### Construction de l'index FAISS

Placez vos documents `.txt` dans un dossier (par ex. `./docs`) puis générez
l'index vectoriel :

```bash
python build_index.py ./docs ./data/index.faiss
```

L'API détectera automatiquement l'index et utilisera le mode RAG pour répondre
aux questions si `OPENAI_API_KEY` est défini.

Exemple de démarrage manuel du backend avec RAG activé :

```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```

### 5. **Activer le chatbot réel**
Pour passer des réponses mockées au véritable modèle de langage :

1. Installez les versions figées indispensables :
   ```bash
   pip install langchain==0.1.13 langsmith==0.0.70 pydantic==1.10.13
   ```
2. Renseignez les variables dans `backend/.env` :
   ```env
   LLM_PROVIDER=openai        # ou ollama, lm_studio...
   LLM_API_KEY=VotreCleIci
   LLM_MODEL=gpt-3.5-turbo
   EMBEDDINGS_MODEL=text-embedding-ada-002
   ```
3. En alternative hors ligne, vous pouvez utiliser un LLM local comme [Ollama](https://github.com/ollama-ai/ollama) ou [LM Studio](https://lmstudio.ai).

---

## 🏃 Lancement de l'application

### Option A : Automatique (Recommandé)
1. **Double-clic sur `start.bat`**
2. Deux fenêtres CMD s'ouvrent :
   - Backend (API FastAPI) sur port 8000
   - Frontend (serveur HTTP) sur port 3000
3. Le navigateur s'ouvre automatiquement sur http://localhost:3000
4. Pour arrêter : **Double-clic sur `stop.bat`**

### Option B : Manuelle
1. **Terminal 1 - Backend :**
   ```
   cd backend
   venv\Scripts\activate
   uvicorn main:app --reload
   ```
2. **Terminal 2 - Frontend :**
   ```
   cd frontend
   python -m http.server 3000
   ```
3. Ouvrir http://localhost:3000

---

## ✅ Fonctionnalités testables

### Interface chat
- Questions sur l'urbanisme (hauteur max, zonage, etc.)
- Réponses instantanées (mockées)
- Boutons de suggestions
- Indicateur de connexion (en ligne/hors ligne)

### Statistiques
- Compteur de requêtes totales
- Compteur de hits cache (si Redis actif)
- Temps de traitement affiché

### API directe
- http://localhost:8000 → Message de bienvenue
- http://localhost:8000/docs → Documentation Swagger
- http://localhost:8000/health → État du service

---

## 🧪 Tests de performance

### Lancement des tests
- **Double-clic sur `test.bat`**
- Menu interactif :
  1. Test de charge simple (50 requêtes)
  2. Test de montée en charge (10, 25, 50, 100 requêtes)
  3. Test du cache
  4. Tous les tests

### Métriques disponibles
- Temps de réponse (moyen, min, max)
- Taux de réussite
- Débit (requêtes/seconde)
- Efficacité du cache

---

## 🔧 Problèmes rencontrés

### Problème : "Redis non disponible"
**Solution** : Normal, le cache Redis est optionnel. L'app fonctionne sans.

### Problème : Frontend affiche "Hors ligne"
**Solutions** :
1. Vérifier que le backend tourne sur le port 8000
2. Rafraîchir la page (F5)
3. Vérifier la console du navigateur (F12)

### Problème : Page blanche ou chat non fonctionnel
**Solution** : Le JavaScript était dans `app.js` séparé, on l'a intégré directement dans `index.html`

---

## 📁 Structure locale

```
urbanisme-poc/
├── backend/
│   ├── main.py         # API FastAPI
│   ├── requirements.txt
│   ├── .env            # Variables (créé par install.bat)
│   └── venv/           # Environnement Python
├── frontend/
│   └── index.html      # Interface (JS intégré)
├── tests/
│   └── test_load.py    # Tests de charge
├── install.bat         # Installation auto
├── start.bat          # Lancement auto
├── stop.bat           # Arrêt auto
└── test.bat           # Tests auto
```

---

## 💡 Points clés

### Avantages du test local
- ✅ Pas besoin d'internet
- ✅ Modifications instantanées
- ✅ Debug facile
- ✅ Gratuit
- ✅ Scripts .bat pour Windows

### Limitations
- ❌ Pas accessible depuis l'extérieur
- ❌ Pas de HTTPS
- ❌ Redis non configuré
- ❌ Réponses mockées (pas d'IA)

---

## 🎯 Bilan test local

Le POC fonctionne parfaitement en local avec :
- Backend FastAPI opérationnel
- Frontend responsive
- Communication frontend ↔ backend
- Tests de performance
- Installation/lancement en 1 clic

**Prêt pour la phase de déploiement cloud !**