let chatInterval = null;
let isEditing = false;
let editingMessageId = null;

function initChat() {
    if (typeof window.chatTaskId === 'undefined' || !window.chatTaskId) return;
    loadMessages();
    // Poll every 3 seconds for new messages
    if (chatInterval) clearInterval(chatInterval);
    chatInterval = setInterval(() => {
        if (!isEditing) loadMessages();
    }, 3000);
}

function loadMessages() {
    const studentIdParam = (window.chatStudentId && window.chatStudentId !== 'null' && window.chatStudentId !== null) ? `?student_id=${window.chatStudentId}` : '';
    fetch(`/chat/${window.chatTaskId}/messages${studentIdParam}`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('chatContainer');
            if(!container) return;
            
            // Check if user is near bottom before update
            const threshold = 150;
            const isNearBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + threshold;
            
            if (data.error) {
                container.innerHTML = `<div style="color:var(--error); padding: 2rem; text-align:center; font-weight:600;">${data.error}</div>`;
                return;
            }

            if (data.length === 0) {
                container.innerHTML = `
                    <div style="flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; opacity:0.4; padding:3rem;">
                        <i class="fas fa-comments" style="font-size:3rem; margin-bottom:1rem;"></i>
                        <p style="font-weight:600;">No messages yet.</p>
                        <p style="font-size:0.85rem;">Send a message to start the collaboration.</p>
                    </div>`;
                return;
            }

            let html = '';
            data.forEach(msg => {
                const isSender = msg.sender_id === window.currentUserId;
                const timeStr = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                
                let fileHtml = '';
                if (msg.file_url) {
                    const filename = msg.file_url.split(/[\\/]/).pop().split('_').slice(1).join('_') || "Attachment";
                    fileHtml = `
                        <a href="${msg.file_url}" target="_blank" class="msg-file-pill">
                            <i class="fas fa-file-alt"></i>
                            <span>${filename}</span>
                            <i class="fas fa-download ms-auto" style="font-size:0.7rem; opacity:0.6;"></i>
                        </a>
                    `;
                }

                html += `
                    <div id="msg-${msg.id}" class="message-wrapper ${isSender ? 'sender' : 'receiver'}" style="display: flex; flex-direction: column; align-items: ${isSender ? 'flex-end' : 'flex-start'};">
                        <div class="message-bubble" style="
                            max-width: 80%;
                            padding: 0.85rem 1.1rem;
                            border-radius: 18px;
                            background: ${isSender ? 'linear-gradient(135deg, var(--primary), var(--secondary))' : 'rgba(255,255,255,0.05)'};
                            color: ${isSender ? 'white' : 'var(--text-main)'};
                            border: ${isSender ? 'none' : '1px solid var(--glass-border)'};
                            position: relative;
                            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                            ${isSender ? 'border-bottom-right-radius: 4px;' : 'border-bottom-left-radius: 4px;'}
                        ">
                            ${fileHtml}
                            <div class="msg-text-content" style="white-space: pre-wrap; word-break: break-word; line-height: 1.5; font-size: 0.95rem;">${msg.content || ''}</div>
                        </div>
                        <div class="message-meta" style="font-size: 0.65rem; color: var(--text-subtle); margin-top: 0.4rem; display: flex; align-items: center; gap: 0.75rem;">
                            <span>${timeStr}</span>
                            ${isSender ? `
                                <div class="msg-actions" style="display:flex; gap:0.5rem;">
                                    <span style="cursor:pointer; transition:color 0.2s;" onmouseover="this.style.color='var(--primary-light)'" onmouseout="this.style.color=''" onclick="startEdit(${msg.id})"><i class="fas fa-pencil-alt"></i></span>
                                    <span style="cursor:pointer; transition:color 0.2s;" onmouseover="this.style.color='var(--error)'" onmouseout="this.style.color=''" onclick="deleteMessage(${msg.id})"><i class="fas fa-trash"></i></span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
            
            // Auto-scroll to bottom if user was already at bottom or it's a new message from sender
            if (isNearBottom) {
                container.scrollTop = container.scrollHeight;
            }
        })
        .catch(err => console.error('Chat load error', err));
}

function startEdit(msgId) {
    isEditing = true;
    editingMessageId = msgId;
    const msgDiv = document.getElementById(`msg-${msgId}`);
    if(!msgDiv) return;
    const txtNode = msgDiv.querySelector('.msg-text-content');
    const oldText = txtNode ? txtNode.textContent : "";
    const messageInput = document.getElementById('messageInput');
    messageInput.value = oldText;
    messageInput.focus();
    messageInput.style.borderColor = 'var(--primary)';
    
    const fileBtn = document.querySelector('label[for="realFileInput"]');
    if (fileBtn) fileBtn.style.opacity = '0.3';
    
    if (!document.getElementById('cancelEditBtn')) {
        const form = document.getElementById('chatForm');
        const cancelBtn = document.createElement('button');
        cancelBtn.id = 'cancelEditBtn';
        cancelBtn.type = 'button';
        cancelBtn.className = 'btn btn-outline';
        cancelBtn.style.cssText = 'width: 46px; height: 46px; padding: 0; display: flex; align-items: center; justify-content: center; border-radius: 12px; color: var(--error); border-color: rgba(239, 68, 68, 0.2);';
        cancelBtn.innerHTML = '<i class="fas fa-times"></i>';
        cancelBtn.onclick = cancelEdit;
        form.insertBefore(cancelBtn, form.lastElementChild);
    }
}

function cancelEdit() {
    isEditing = false;
    editingMessageId = null;
    const messageInput = document.getElementById('messageInput');
    messageInput.value = '';
    messageInput.style.borderColor = '';
    
    const fileBtn = document.querySelector('label[for="realFileInput"]');
    if (fileBtn) fileBtn.style.opacity = '1';
    
    const cancelBtn = document.getElementById('cancelEditBtn');
    if (cancelBtn) cancelBtn.remove();
}

function deleteMessage(msgId) {
    if (!confirm("This message will be permanently removed. Continue?")) return;
    fetch(`/chat/${window.chatTaskId}/messages/${msgId}`, { method: 'DELETE' })
    .then(res => res.json())
    .then(data => {
        if (data.success) loadMessages();
        else alert(data.error);
    });
}

function showFilePreview() {
    const fileInput = document.getElementById('realFileInput');
    const preview = document.getElementById('filePreview');
    const fileNameDisplay = document.getElementById('fileName');
    if (!preview || !fileNameDisplay) return;
    if (fileInput.files.length > 0) {
        fileNameDisplay.textContent = fileInput.files[0].name;
        preview.style.display = 'flex';
    } else {
        preview.style.display = 'none';
    }
}

function clearFile() {
    const fileInput = document.getElementById('realFileInput');
    if(fileInput) fileInput.value = '';
    showFilePreview();
}

function sendMessage(e) {
    e.preventDefault();
    const messageInput = document.getElementById('messageInput');
    const fileInput = document.getElementById('realFileInput');
    const content = messageInput.value.trim();
    const submitBtn = e.target.querySelector('button[type="submit"]');

    if (isEditing && editingMessageId) {
        if (!content) return false;
        submitBtn.disabled = true;
        fetch(`/chat/${window.chatTaskId}/messages/${editingMessageId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        }).then(res => res.json()).then(data => {
            submitBtn.disabled = false;
            if (data.success) {
                cancelEdit();
                loadMessages();
            } else alert(data.error);
        });
        return false;
    }
    
    if (!content && fileInput.files.length === 0) return false;
    const formData = new FormData();
    formData.append('content', content);
    if (window.chatStudentId && window.chatStudentId !== 'null') formData.append('receiver_id', window.chatStudentId);
    if (fileInput.files.length > 0) formData.append('file', fileInput.files[0]);
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    
    fetch(`/chat/${window.chatTaskId}/send`, { method: 'POST', body: formData })
    .then(res => res.json())
    .then(data => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        if (data.success) {
            messageInput.value = '';
            clearFile();
            loadMessages();
            // Scroll to bottom immediately after sending
            setTimeout(() => {
                const container = document.getElementById('chatContainer');
                if(container) container.scrollTop = container.scrollHeight;
            }, 100);
        } else alert(data.error);
    });
    return false;
}

// Global styles for JS-injected elements
const styleSheet = document.createElement("style");
styleSheet.innerText = `
    .msg-file-pill {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem;
        background: rgba(0,0,0,0.15);
        border-radius: 12px;
        color: inherit;
        text-decoration: none;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(255,255,255,0.05);
        transition: background 0.2s;
    }
    .msg-file-pill:hover {
        background: rgba(0,0,0,0.25);
    }
    .msg-file-pill i:first-child {
        color: var(--primary-light);
    }
`;
document.head.appendChild(styleSheet);

