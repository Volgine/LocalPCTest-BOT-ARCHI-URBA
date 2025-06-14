const fs = require('fs');
const { JSDOM } = require('jsdom');

const code = fs.readFileSync('frontend/js/main.js', 'utf8');
const match = code.match(/function addMessage\(.*?\{[\s\S]*?\n\}/);
if (!match) throw new Error('addMessage not found');
const addMessageCode = match[0];

const dom = new JSDOM('<!DOCTYPE html><div id="chatMessages"></div>');
const { window } = dom;

const addMessage = new Function('window','document', `${addMessageCode}; return addMessage;`)(window, window.document);

addMessage('<img id="xss" src="x" onerror="global.malicious=true">', 'user');

const hasImg = window.document.querySelector('#xss') !== null;
const contentHTML = window.document.querySelector('.message-content').innerHTML.trim();
console.log(JSON.stringify({hasImg, contentHTML}));
