// Configuration
const getApiUrl = () => {
    if (window.ENV && window.ENV.API_URL) {
        return window.ENV.API_URL;
    }
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


// Fonctions utilitaires
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Gestion des fichiers
async function uploadFile(file) {
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
    }
}

document.getElementById('fileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    await uploadFile(file);
    e.target.value = '';
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
    addMessage(`<span class="loading-dots">Analyse en cours</span>`, 'bot', loadingId, [], true);
    
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
function addMessage(content, type, id = null, badges = [], allowHtml = false) {
    const messagesDiv = document.getElementById('messagesContainer') ||
                        document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    if (id) messageDiv.id = `msg-${id}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    function sanitizeHtml(html) {
        if (typeof DOMPurify !== 'undefined') {
            return DOMPurify.sanitize(html);
        }
        const template = document.createElement('template');
        template.innerHTML = html;
        template.content.querySelectorAll('script').forEach(s => s.remove());
        template.content.querySelectorAll('*').forEach(el => {
            [...el.attributes].forEach(attr => {
                if (attr.name.startsWith('on')) el.removeAttribute(attr.name);
            });
        });
        return template.innerHTML;
    }

    if (allowHtml) {
        contentDiv.innerHTML = sanitizeHtml(content);
    } else {
        contentDiv.textContent = content;
    }
    messageDiv.appendChild(contentDiv);

    if (badges.length > 0) {
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        badges.forEach(badge => {
            const badgeSpan = document.createElement('span');
            badgeSpan.className = 'source-badge';
            badgeSpan.textContent = badge;
            metaDiv.appendChild(badgeSpan);
        });
        messageDiv.appendChild(metaDiv);
    }

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
        if (document.getElementById('apiCalls')) {
            document.getElementById('apiCalls').textContent = data.api_calls;
        }
        if (document.getElementById('documentsIndexed')) {
            document.getElementById('documentsIndexed').textContent = data.documents_indexed;
        }

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

// Quick actions
function quickAction(text) {
    document.getElementById('chatInput').value = text;
    sendMessage();
}

// Feasibility study management
function addFeasibilityStudy(name) {
    const list = document.getElementById('projectList');
    if (!list) return;
    const card = document.createElement('div');
    card.className = 'project-card';
    card.textContent = name;
    card.dataset.action = `Étude de faisabilité pour ${name}`;
    card.addEventListener('click', () => {
        quickAction(card.dataset.action);
        init3DPreview(name);
    });
    list.appendChild(card);
}

function init3DPreview(project) {
    const preview = document.getElementById('preview3d');
    if (preview) {
        preview.textContent = `Prévisualisation 3D pour ${project}...`;
    }
}

// Event bindings
document.querySelectorAll('.quick-action').forEach(btn => {
    btn.addEventListener('click', () => quickAction(btn.dataset.action));
});

document.querySelectorAll('.project-card').forEach(card => {
    card.addEventListener('click', () => {
        quickAction(card.dataset.action || card.textContent);
        init3DPreview(card.textContent);
    });
});

const uploadZone = document.getElementById('uploadZone');
if (uploadZone) {
    ['dragover', 'drop'].forEach(event => {
        uploadZone.addEventListener(event, e => e.preventDefault());
    });
    uploadZone.addEventListener('drop', e => {
        const file = e.dataTransfer.files[0];
        uploadFile(file);
    });
}

// Demo project card
if (document.getElementById('addStudyBtn')) {
    document.getElementById('addStudyBtn').addEventListener('click', () => {
        const name = prompt('Nom du projet ?');
        if (name) addFeasibilityStudy(name);
    });
}
