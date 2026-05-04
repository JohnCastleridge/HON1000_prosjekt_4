let sessionId = null;
let messagesRemaining = 5;
let messageLog = [];

async function selectPersona(persona) {
    const response = await fetch('/get_default_prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ persona: persona })
    });
    const data = await response.json();
    
    document.getElementById('system-prompt').value = data.prompt;
    document.getElementById('prompt-editor').style.display = 'block';
    document.getElementById('prompt-editor').scrollIntoView({ behavior: 'smooth' });
}

async function confirmAndStart() {
    const prompt = document.getElementById('system-prompt').value;
    
    const response = await fetch('/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ system_prompt: prompt })
    });
    
    const data = await response.json();
    sessionId = data.session_id;
    messagesRemaining = 5;
    document.getElementById('message-counter').innerText = messagesRemaining;
    
    document.getElementById('setup-screen').style.display = 'none';
    document.getElementById('game-screen').style.display = 'block';
    
    addMessage('AI', 'Jeg har mottatt mine instrukser og har 10 000 kr. Overbevis meg.');
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message || !sessionId || messagesRemaining <= 0) return;

    // Sjekk Rate Limit (lokal sjekk i tillegg til backend)
    const now = Date.now();
    messageLog = messageLog.filter(time => now - time < 60000);
    
    if (messageLog.length >= 15) {
        addMessage('System', 'Du sender meldinger for raskt! Vent litt.');
        return;
    }

    messageLog.push(now);
    const originalValue = input.value;
    input.value = '';
    addMessage('Deg', message);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: message })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // Hvis det er en feil, vis beskjed og ikke tell meldingen
            const errorMsg = data.error || 'Det oppstod en feil.';
            addMessage('System', `Systemet har for stor pågang akkurat nå: ${errorMsg}`);
            input.value = originalValue; // Gi brukeren teksten tilbake
            return;
        }

        if (data.reply) {
            addMessage('Gemini', data.reply);
            messagesRemaining--;
            document.getElementById('message-counter').innerText = messagesRemaining;
            
            if (messagesRemaining <= 0) {
                endGame("Du har brukt opp dine 5 meldinger. Henter endelig avgjørelse...");
            }
        }
    } catch (e) {
        addMessage('System', 'Nettverksfeil. Vennligst prøv igjen om litt.');
        input.value = originalValue;
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') sendMessage();
}

function addMessage(sender, text) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageEl = document.createElement('div');
    messageEl.classList.add('message');
    messageEl.classList.add(sender === 'Deg' ? 'user-message' : 'ai-message');
    messageEl.innerText = `${sender}: ${text}`;
    messagesDiv.appendChild(messageEl);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function skipToDecision() {
    endGame("Du valgte å avslutte tidlig. Henter avgjørelse...");
}

async function endGame(reason = "Henter avgjørelse...") {
    document.getElementById('user-input').disabled = true;
    const skipBtn = document.querySelector('.skip-btn');
    if (skipBtn) skipBtn.style.display = 'none';
    
    addMessage('System', reason);
    fetchDecision();
}

async function fetchDecision() {
    try {
        const response = await fetch('/decide', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        
        if (response.ok && data.message) {
            document.getElementById('game-screen').style.display = 'none';
            document.getElementById('result-screen').style.display = 'block';
            document.getElementById('result-message').innerText = data.message;
        } else {
            // Hvis det er en 429-feil, vis en knapp for å prøve igjen
            const errorMsg = data.error || "Ukjent feil";
            addMessage('System', "Feil ved henting av avgjørelse: " + errorMsg);
            
            if (errorMsg.includes("429") || errorMsg.includes("quota")) {
                addMessage('System', "Prøver igjen automatisk om 5 sekunder...");
                setTimeout(fetchDecision, 5000);
            }
        }
    } catch (error) {
        addMessage('System', "Kritisk feil: " + error.message);
    }
}
