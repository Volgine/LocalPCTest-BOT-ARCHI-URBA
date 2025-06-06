�
�
 Assistant Urbanisme POC
 Un assistant IA pour répondre aux questions sur les réglementations d'urbanisme (PLU, zonage, hauteurs
 autorisées, etc.)
 🚀
 Démarrage rapide
 Prérequis
 Python 3.8+
 Node.js (pour Vercel)
 Redis (optionnel)
 Installation
 1. Cloner le repository
 bash
 git clone https://github.com/yourusername/urbanisme-poc.git
 git
 cd
 clone https://github.com/yourusername/urbanisme-poc.git
 cd urbanisme-poc
 urbanisme-poc
 2. Backend
 bash
 cd
 cd backend
 backend
 python -m venv venv
 python -m venv venv
 source
 source venv/bin/activate  
venv/bin/activate  # Windows: venv\Scripts\activate
 pip 
pip install
 # Windows: venv\Scripts\activate
 install -r requirements.txt-r requirements.txt
 3. Variables d'environnement
 bash
 cp
 cp .env.example .env
 .env.example .env
 # Éditer .env avec vos clés API
 # Éditer .env avec vos clés API
 Lancement local
 Backend:
 bash
 cd
 cd backend
 backend
 uvicorn main:app --reload
 uvicorn main:app --reload
Frontend:
 bash
 cd frontend
 frontend
 cd
 python -m http.server 
python -m http.server 3000
 Ouvrir 
3000
 http://localhost:3000
 📦
 Structure du projet
 urbanisme-poc/
 urbanisme-poc/
 ├── backend/
 ├── backend/
 │   ├── main.py          
│   ├── main.py          
# API FastAPI
 # API FastAPI
 │   ├── requirements.txt # Dépendances Python
 │   ├── requirements.txt # Dépendances Python
 │   ├── .env.example     
│   ├── .env.example     
│   └── railway.json     
│   └── railway.json     
├── frontend/
 ├── frontend/
 │   ├── index.html       
│   ├── index.html       
│   ├── app.js          
│   ├── app.js          
│   └── vercel.json     
│   └── vercel.json     
├── tests/
 ├── tests/
 │   └── test_load.py    
│   └── test_load.py    
└── README.md
 └── README.md
 🚀
 Déploiement
 Backend (Railway)
 1. Push sur GitHub
 # Template variables d'env
 # Template variables d'env
 # Config Railway
 # Config Railway
 # Interface utilisateur
 # Interface utilisateur
 # Logique frontend
 # Logique frontend
 # Config Vercel
 # Config Vercel
 # Tests de charge
 # Tests de charge
 2. Connecter Railway au repo
 3. Ajouter les variables d'environnement
 4. Deploy!
 Frontend (Vercel)
 1. Installer Vercel CLI: 
2. Dans 
npm i -g vercel
 /frontend : 
vercel
 3. Suivre les instructions
 🧪
 Tests
bash
 cd
 cd tests
 tests
 python test_load.py
 python test_load.py
 📈
 Roadmap
 POC basique
 Cache Redis
 Déploiement cloud
 Intégration vraie API GPU
 Ajout IA/RAG
 Authentification
 Dashboard analytics
 🤝
 Contribution
 Les PRs sont les bienvenues !
 📝
 License
 MIT
