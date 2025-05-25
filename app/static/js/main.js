// Socket.IO instance
let socket = null;

// Get current user ID from the chat container
const chatContainer = document.querySelector('.chat-container');
const currentUserId = chatContainer ? parseInt(chatContainer.dataset.userId) : null;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Socket.IO if we're on a chat page
    if (document.querySelector('.chat-container')) {
        initializeSocket();
        initializeAutoRefresh();
    }

    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

function initializeSocket() {
    if (!socket) {
        socket = io();
        
        const messageForm = document.getElementById('message-form');
        const messageInput = document.getElementById('message-input');
        const roomId = messageForm ? messageForm.dataset.roomId : null;

        if (messageForm && messageInput && roomId) {
            // Handle form submission
            messageForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const content = messageInput.value.trim();
                
                if (content) {
                    socket.emit('message', {
                        room_id: roomId,
                        content: content
                    });
                    messageInput.value = '';
                }
            });

            // Join room when form is available
            socket.emit('join', { room_id: roomId });

            // Handle page unload
            window.addEventListener('beforeunload', function() {
                socket.emit('leave', { room_id: roomId });
            });
        }

        // Connection events
        socket.on('connect', () => {
            console.log('Connected to server');
            showToast('Connected to chat server', 'success');
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            showToast('Disconnected from chat server', 'warning');
        });

        // Chat events
        socket.on('message', (data) => {
            appendMessage(data);
        });

        socket.on('user_joined', (data) => {
            showToast(`${data.username} joined the room`, 'info');
            updateActiveMembers(data.active_members);
        });

        socket.on('user_left', (data) => {
            showToast(`${data.username} left the room`, 'info');
            updateActiveMembers(data.active_members);
        });
    }
}

function initializeAutoRefresh() {
    // Auto-refresh room topics periodically
    setInterval(updateRoomTopics, 120000); // Every 2 minutes
}

function appendMessage(data) {
    const messagesContainer = document.querySelector('.chat-messages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${data.user_id === currentUserId ? 'sent' : 'received'}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const username = document.createElement('small');
    username.className = 'text-muted d-block';
    username.textContent = data.username;
    
    const text = document.createElement('p');
    text.className = 'mb-0';
    text.textContent = data.content;
    
    const metadata = document.createElement('div');
    metadata.className = 'message-metadata';
    
    const intentEmoji = document.createElement('span');
    intentEmoji.className = 'message-emoji';
    intentEmoji.textContent = data.intent_emoji || '💬';
    
    const intentBadge = document.createElement('span');
    intentBadge.className = 'intent-badge';
    intentBadge.textContent = data.intent;
    
    const emotionEmoji = document.createElement('span');
    emotionEmoji.className = 'message-emoji';
    emotionEmoji.textContent = data.emotion_emoji || '😐';
    
    const emotionBadge = document.createElement('span');
    emotionBadge.className = `emotion-badge emotion-${data.primary_emotion}`;
    emotionBadge.textContent = data.primary_emotion;
    
    const timestamp = document.createElement('small');
    timestamp.className = 'text-muted float-end';
    timestamp.textContent = data.timestamp;
    
    metadata.appendChild(intentEmoji);
    metadata.appendChild(intentBadge);
    metadata.appendChild(emotionEmoji);
    metadata.appendChild(emotionBadge);
    metadata.appendChild(timestamp);
    
    messageContent.appendChild(username);
    messageContent.appendChild(text);
    messageContent.appendChild(metadata);
    messageDiv.appendChild(messageContent);
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom(messagesContainer);
}

function updateActiveMembers(members) {
    const membersList = document.getElementById('active-members');
    if (!membersList) return;

    membersList.innerHTML = members.map(username => `
        <li class="list-group-item d-flex justify-content-between align-items-center">
            ${username}
            <span class="badge bg-success rounded-pill">online</span>
        </li>
    `).join('');
}

function updateRoomTopics() {
    const topicsContainer = document.getElementById('room-topics');
    if (!topicsContainer) return;

    const roomId = document.getElementById('message-form').dataset.roomId;
    fetch(`/room/${roomId}/topics`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.topics && data.topics.length > 0) {
                topicsContainer.innerHTML = data.topics.map(topic => `
                    <div class="topic-item">
                        <div class="topic-header">
                            <strong>${topic.keywords.join(', ')}</strong>
                            ${topic.coherence ? `
                                <span class="topic-score" title="Topic Coherence Score">
                                    ${topic.coherence.toFixed(2)}
                                </span>
                            ` : ''}
                        </div>
                        ${topic.examples && topic.examples.length > 0 ? `
                            <div class="example-message">
                                <small class="text-muted">Example message:</small><br>
                                ${topic.examples[0]}
                            </div>
                        ` : ''}
                    </div>
                `).join('');
            } else {
                topicsContainer.innerHTML = '<p class="card-text">No topics detected yet.</p>';
            }
        })
        .catch(error => console.error('Error updating topics:', error));
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast show bg-${type} text-white position-fixed bottom-0 end-0 m-3`;
    toast.style.zIndex = '1050';
    toast.innerHTML = `
        <div class="toast-body">
            ${message}
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in other scripts
window.chatUtils = {
    showToast,
    formatDate,
    formatTime,
    debounce
}; 