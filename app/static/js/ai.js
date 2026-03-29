// Jarrabha Intelligence Engine (Orbital Assistant)
let aiConfig = {
    welcome_message: "Greetings. I am the Jarrabha Orbital Assistant. How can I guide your mission today?",
    system_instruction: "You are the Jarrabha AI assistant."
};

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/ai-config');
        if (response.ok) {
            aiConfig = await response.ok ? await response.json() : aiConfig;
            // Initialize with the configured welcome message
            const msgContainer = document.getElementById('aiPanelMessages');
            if (msgContainer && msgContainer.children.length === 0) {
                appendAiMessage(aiConfig.welcome_message, 'bot');
            }
        }
    } catch (e) { console.error("AI Config fetch failed", e); }
});

function toggleAiPanel() {
    const panel = document.getElementById('aiAssistantPanel');
    const bubble = document.getElementById('aiAssistantBubble');
    if (!panel) return;
    
    if (getComputedStyle(panel).display === 'none') {
        panel.style.display = 'flex';
        panel.classList.add('animate-fade-in-up');
        if(bubble) bubble.style.transform = 'scale(0) rotate(90deg)';
    } else {
        panel.style.display = 'none';
        if(bubble) bubble.style.transform = 'scale(1) rotate(0deg)';
    }
}

function askAi(customText) {
    const input = document.getElementById('aiInput');
    const question = customText || input.value.trim();
    if (!question) return;

    if (!customText && input) input.value = '';

    appendAiMessage(question, 'user');

    // Simulate Orbital Processing
    const container = document.getElementById('aiPanelMessages');
    const typing = document.createElement('div');
    typing.className = 'ai-message ai-bot animate-pulse';
    typing.innerHTML = '<p><i class="fas fa-ellipsis-h"></i> Analyzing Frequency...</p>';
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;

    setTimeout(() => {
        typing.remove();
        let response = "";
        const q = question.toLowerCase();

        // High-level intent routing
        if (q.includes('task') || q.includes('mission') || q.includes('work')) {
            response = "To initiate a mission, navigate to 'Mission Boards', select an objective matching your specialization, and click 'Engage'. You will be granted access to a dedicated secure workspace.";
        } else if (q.includes('leaderboard') || q.includes('rank') || q.includes('standing')) {
            response = "The Global Standing board tracks our elite pioneers. Advance your sector rank by successfully completing high-complexity missions and maintaining a 5.0 reliability index.";
        } else if (q.includes('course') || q.includes('learn') || q.includes('academy')) {
            response = "The Learning Academy hosts critical curriculum modules designed to upgrade your technical capabilities. Completing modules unlocks higher-tier mission access.";
        } else if (q.includes('company') || q.includes('hire') || q.includes('partner')) {
            response = "Partners can deploy missions and vet global talent. All entities are reviewed by Command before orbital deployment to ensure ecosystem integrity.";
        } else if (q.includes('certificate') || q.includes('award')) {
            response = "Upon mission validation by the deploying entity, an immutable cryptographic certificate is generated and displayed on your public profile.";
        } else if (q.includes('hello') || q.includes('hi') || q.includes('greet')) {
            response = "Frequency established. I am here to facilitate your platform navigation and mission oversight. How may I assist?";
        } else {
            response = "Inquiry received. While I am still calibrating my intelligence matrix, I recommend consulting your Mission Control dashboard or the Academy records for deeper intel.";
        }

        appendAiMessage(response, 'bot');
    }, 1200);
}

function appendAiMessage(text, side) {
    const container = document.getElementById('aiPanelMessages');
    if (!container) return;
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `ai-message ai-${side} reveal`;
    msgDiv.style.opacity = '1';
    msgDiv.style.transform = 'translateY(0)';
    msgDiv.innerHTML = `<p>${text}</p>`;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}
