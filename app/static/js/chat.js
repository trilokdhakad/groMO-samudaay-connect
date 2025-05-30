// Initialize socket connection
const socket = io();

// Debug logging for socket events
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('error', (error) => {
    console.error('Socket error:', error);
});

// Join room when page loads
socket.emit('join', {
    room_id: ROOM_ID  // This should be set in your template
});

// Handle moderation warnings
socket.on('moderation_warning', function(data) {
    alert(data.message);
});

// Handle incoming messages
socket.on('message', function(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    if (data.user_id === CURRENT_USER_ID) {
        messageDiv.className += ' message-own';
    }
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="username">${data.username}</span>
            <span class="timestamp">${data.timestamp}</span>
        </div>
        <div class="message-content">
            ${data.content}
        </div>
    `;
    
    document.getElementById('chat-messages').appendChild(messageDiv);
    scrollToBottom();
});

// Handle user join/leave events
socket.on('user_joined', function(data) {
    console.log('User joined:', data);
});

socket.on('user_left', function(data) {
    console.log('User left:', data);
});

// Send message
document.getElementById('message-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value.trim();
    
    if (content) {
        socket.emit('message', {
            content: content,
            room_id: ROOM_ID
        });
        messageInput.value = '';
    }
});

// Add CSS for animations and styling
const style = document.createElement('style');
style.textContent = `
    .shake-animation {
        animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
    }
    @keyframes shake {
        10%, 90% { transform: translate3d(-1px, 0, 0); }
        20%, 80% { transform: translate3d(2px, 0, 0); }
        30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
        40%, 60% { transform: translate3d(4px, 0, 0); }
    }
    
    .warning-message {
        background-color: #ffebee !important;
        border-left: 4px solid #f44336 !important;
        margin: 10px 0 !important;
        padding: 10px !important;
        color: #d32f2f !important;
        font-weight: 500 !important;
    }
    
    .warning-content {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .system-message {
        text-align: center;
        font-size: 0.9em;
        margin: 8px 0;
    }
`;
document.head.appendChild(style);

// Utility function to scroll chat to bottom
function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
} 