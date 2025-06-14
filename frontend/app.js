// Configuration
const getApiUrl = () => {
    const host = window.location.hostname;
    if (['localhost', '127.0.0.1'].includes(host)) {
        return 'http://localhost:8000';
    }
    return 'https://striking-clarity-actelle.up.railway.app';
};
const API_URL = getApiUrl();
if (['localhost', '127.0.0.1'].includes(window.location.hostname)) {
    console.log('Using API_URL:', API_URL);
}

// État
let isLoading = false;
let sessionId = generateSessionId();
let uploadedDocuments = [];

// Three.js Background
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ 
    canvas: document.getElementById('bg-canvas'),
    alpha: true,
    antialias: true
});

renderer.setSize(window.innerWidth, window.innerHeight);
camera.position.z = 5;

// Créer des particules pour l'effet cyberpunk
const particlesGeometry = new THREE.BufferGeometry();
const particlesCount = 3000;
const posArray = new Float32Array(particlesCount * 3);

for(let i = 0; i < particlesCount * 3; i++) {
    posArray[i] = (Math.random() - 0.5) * 10;
}

particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

const particlesMaterial = new THREE.PointsMaterial({
    size: 0.02,
    color: 0x00fff0,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending
});

const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
scene.add(particlesMesh);

// Créer une grille 3D
const gridHelper = new THREE.GridHelper(20, 20, 0x00fff0, 0x00fff0);
gridHelper.material.opacity = 0.2;
gridHelper.material.transparent = true;
gridHelper.rotation.x = Math.PI / 2;
scene.add(gridHelper);

// Animation Three.js
function animate() {
    requestAnimationFrame(animate);
    
    particlesMesh.rotation.x += 0.0003;
    particlesMesh.rotation.y += 0.0005;
    
    const positions = particlesMesh.geometry.attributes.position.array;
    for(let i = 0; i < positions.length; i += 3) {
        positions[i + 1] += Math.sin(Date.now() * 0.001 + i) * 0.0001;
    }
    particlesMesh.geometry.attributes.position.needsUpdate = true;
    
    renderer.render(scene, camera);
}
animate();

// Responsive Three.js
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Fonctions utilitaires
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Gestion des fichiers
document.getElementById('fileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    
    const uploadButton = document.querySelector('.upload-button');
    uploadButton.textContent = '⏳ Upload...';
    uploadButton.disabled = true;
    
    try {
        const response = await fetch(`${API_URL}/api/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        const data = await response.json();
        uploadedDocuments.push(data);
        updateDocumentsList();
        
        addMessage(`📄 Document "${data.filename}" uploadé avec succès (${data.chunks} chunks indexés)`, 'system');
        
    } catch (error) {
        console.error('Upload error:', error);
        addMessage('❌ Erreur lors de l\'upload du document', 'system');
    } finally {
        uploadButton.textContent = '📁 Upload';
        uploadButton.disabled = false;
        e.target.value = '';
    }
});

// Envoyer un message
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message || isLoading) return;
    
    isLoading = true;
    document.getElementById('sendButton').disabled = true;
    
    // Ajouter le message utilisateur
    addMessage(message, 'user');
    input.value = '';
    
    // Ajouter un message de chargement
    const loadingId = Date.now();
    addMessage(`<span class="loading-dots">Analyse en cours</span>`, 'bot', loadingId);
    
    try {
        const startTime = Date.now();
        
        const response = await fetch(`${API_URL}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: message,
                session_id: sessionId,
                use_context: uploadedDocuments.length > 0
            })
        });
        
        if (!response.ok) throw new Error('Query failed');
        
        const data = await response.json();
        const responseTime = Date.now() - startTime;
        
        // Remplacer le message de chargement
        const loadingMsg = document.getElementById(`msg-${loadingId}`);
        if (loadingMsg) loadingMsg.remove();
        
        // Ajouter la réponse
        let responseContent = data.answer;
        let badges = [];
        
        if (data.cached) badges.push('💾 Cache');
        if (data.sources_used && data.sources_used.length > 0) {
            badges.push(`📄 ${data.sources_used.length} sources`);
        }
        if (data.confidence) badges.push(`🎯 ${Math.round(data.confidence * 100)}%`);
        
        addMessage(responseContent, 'bot', null, badges);
        
        // Mettre à jour les stats
        document.getElementById('responseTime').textContent = responseTime;
        updateStats();
        
    } catch (error) {
        console.error('Query error:', error);
        const loadingMsg = document.getElementById(`msg-${loadingId}`);
        if (loadingMsg) loadingMsg.remove();
        addMessage('❌ Erreur lors de l\'analyse. Veuillez réessayer.', 'bot');
    } finally {
        isLoading = false;
        document.getElementById('sendButton').disabled = false;
        input.focus();
    }
}

// Ajouter un message au chat
function addMessage(content, type, id = null, badges = []) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    if (id) messageDiv.id = `msg-${id}`;
    
    let badgesHtml = '';
    if (badges.length > 0) {
        badgesHtml = badges.map(badge => `<span class="source-badge">${badge}</span>`).join('');
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">${content}</div>
        ${badgesHtml ? `<div class="message-meta">${badgesHtml}</div>` : ''}
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Exemples de questions
function askExample(question) {
    document.getElementById('chatInput').value = question;
    sendMessage();
}

// Mettre à jour la liste des documents
function updateDocumentsList() {
    const listDiv = document.getElementById('documentsList');
    
    if (uploadedDocuments.length === 0) {
        listDiv.innerHTML = '<div style="color: var(--text-secondary); text-align: center; padding: 20px;">Aucun document uploadé</div>';
        return;
    }
    
    listDiv.innerHTML = uploadedDocuments.map(doc => `
        <div class="document-item">
            <div>
                <div class="document-name">${doc.filename}</div>
                <div class="document-size">${doc.chunks} chunks • ${formatBytes(doc.size)}</div>
            </div>
        </div>
    `).join('');
    
    document.getElementById('docCount').textContent = uploadedDocuments.length;
}

// Mettre à jour les statistiques
async function updateStats() {
    const errorEl = document.getElementById('error-message');
    if (errorEl) errorEl.style.display = 'none';
    try {
        const response = await fetch(`${API_URL}/api/stats`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        document.getElementById('queryCount').textContent = data.total_queries;
        document.getElementById('cacheHits').textContent = data.cache_hits;

    } catch (error) {
        console.error('Stats error:', error);
        if (errorEl) {
            errorEl.textContent = 'Erreur de connexion API';
            errorEl.style.display = 'block';
        }
    }
}

// Utilitaires
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialisation
updateStats();
setInterval(updateStats, 10000);

// Focus sur l'input
document.getElementById('chatInput').focus();

// Raccourcis clavier
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        document.getElementById('chatInput').focus();
    }
});
