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
    const sendBtn = document.querySelector('button[onclick="sendMessage()"]');
    const message = input.value.trim();
    if (!message || !sessionId || messagesRemaining <= 0 || input.disabled) return;

    // Sjekk Rate Limit (lokal sjekk i tillegg til backend)
    const now = Date.now();
    messageLog = messageLog.filter(time => now - time < 60000);
    
    if (messageLog.length >= 15) {
        addMessage('System', 'Du sender meldinger for raskt! Vent litt.');
        return;
    }

    messageLog.push(now);
    const originalValue = input.value;
    
    // Deaktiver input og knapper mens vi venter
    input.disabled = true;
    if (sendBtn) sendBtn.disabled = true;
    const skipBtn = document.querySelector('.skip-btn');
    if (skipBtn) skipBtn.disabled = true;
    
    const originalPlaceholder = input.placeholder;
    input.placeholder = "Gemini tenker...";
    
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
            const errorMsg = data.error || 'Det oppstod en feil.';
            addMessage('System', `Systemet har for stor pågang akkurat nå: ${errorMsg}`);
            input.value = originalValue;
            return;
        }

        if (data.reply) {
            addMessage('Gemini', data.reply);
            messagesRemaining--;
            document.getElementById('message-counter').innerText = messagesRemaining;
            
            if (messagesRemaining <= 0) {
                // Ikke avslutt automatisk, men deaktiver input og vis en knapp for å se resultatet
                input.disabled = true;
                if (sendBtn) sendBtn.disabled = true;
                const skipBtn = document.querySelector('.skip-btn');
                if (skipBtn) {
                    skipBtn.innerText = "Se endelig avgjørelse";
                    skipBtn.classList.add('final-decision-btn');
                    // Vi fjerner disabled her slik at de kan trykke på den nye knappen
                    skipBtn.disabled = false;
                }
                addMessage('System', "Du har brukt opp dine 5 meldinger. Trykk på knappen over for å se resultatet.");
            }
        }
    } catch (e) {
        addMessage('System', 'Nettverksfeil. Vennligst prøv igjen om litt.');
        input.value = originalValue;
    } finally {
        // Aktiver input igjen når vi er ferdige (hvis spillet ikke er slutt)
        if (messagesRemaining > 0) {
            input.disabled = false;
            if (sendBtn) sendBtn.disabled = false;
            const skipBtn = document.querySelector('.skip-btn');
            if (skipBtn) skipBtn.disabled = false;
            input.placeholder = originalPlaceholder;
            input.focus();
        }
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
        
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const text = await response.text();
            console.error("Server returnerte ikke JSON:", text);
            throw new Error("Serveren returnerte en feilside (HTML) i stedet for data. Sjekk serverloggen.");
        }

        const data = await response.json();
        
        if (response.ok && data.message) {
            document.getElementById('game-screen').style.display = 'none';
            document.getElementById('result-screen').style.display = 'block';
            document.getElementById('result-message').innerText = data.message;
        } else {
            // Hvis det er en 429-feil, vis en knapp for å prøve igjen
            const errorMsg = data.error || "Ukjent feil";
            addMessage('System', "Feil ved henting av avgjørelse: " + errorMsg);
            
            if (response.status === 429 || errorMsg.includes("429") || errorMsg.includes("quota")) {
                addMessage('System', "Prøver igjen automatisk om 5 sekunder...");
                setTimeout(fetchDecision, 5000);
            }
        }
    } catch (error) {
        addMessage('System', "Kritisk feil: " + error.message);
    }
}
