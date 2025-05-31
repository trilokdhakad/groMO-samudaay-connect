// Socket.IO instance
let socket = null;

// Get current user ID from the chat container
const chatContainer = document.querySelector('.chat-container');
const currentUserId = chatContainer ? parseInt(chatContainer.dataset.userId) : null;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Socket.IO if we're on a chat page
    if (document.querySelector('.chat-container')) {
        console.log('Initializing chat...');
        try {
            socket = io({
                transports: ['websocket'],
                upgrade: false,
                reconnection: true,
                reconnectionAttempts: 5,
                autoConnect: true
            });

            socket.on('connect', () => {
                console.log('Connected to server');
                showToast('Connected to chat server', 'success');
                
                // Only initialize other features after socket is connected
                initializeSocket();
                initializeAutoRefresh();
                initializeQASystem();
            });

            socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                showToast('Failed to connect to chat server. Retrying...', 'error');
            });

            socket.on('disconnect', () => {
                console.log('Disconnected from server');
                showToast('Disconnected from chat server. Attempting to reconnect...', 'warning');
            });
        } catch (error) {
            console.error('Error initializing socket:', error);
            showToast('Failed to initialize chat. Please refresh the page.', 'error');
        }
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

function initializeQASystem() {
    const isQuestionCheckbox = document.getElementById('is-question');
    const pointsInput = document.getElementById('points-input');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');

    // Toggle points input when question checkbox changes
    if (isQuestionCheckbox) {
        isQuestionCheckbox.addEventListener('change', function() {
            pointsInput.style.display = this.checked ? 'block' : 'none';
            if (this.checked) {
                pointsInput.value = '10'; // Default points
                pointsInput.min = '1';  // Minimum points
                pointsInput.max = document.querySelector('.card-body .badge.bg-warning.text-dark')?.textContent || '100';  // Max is user's current points
            }
        });
    }

    // Handle answer button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.answer-btn')) {
            const btn = e.target.closest('.answer-btn');
            const questionId = btn.dataset.questionId;
            handleAnswerClick(questionId);
        }
    });

    // Handle accept answer button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.accept-answer-btn')) {
            const btn = e.target.closest('.accept-answer-btn');
            const answerId = btn.dataset.answerId;
            handleAcceptAnswer(answerId);
        }
    });

    // Handle rating stars clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.rating-stars i')) {
            const star = e.target.closest('.rating-stars i');
            const rating = parseInt(star.dataset.rating);
            const messageId = star.closest('.rating-container').dataset.messageId;
            handleRating(messageId, rating);
        }
    });

    // Handle message form submission
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const messageInput = document.getElementById('message-input');
            const content = messageInput.value.trim();
            const isQuestion = document.getElementById('is-question').checked;
            const pointsInput = document.getElementById('points-input');
            const points = isQuestion ? parseInt(pointsInput.value) || 10 : 0;
            const questionId = messageInput.dataset.answeringQuestion;
            
            if (!content) return;

            // Disable submit button to prevent double submission
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            
            if (questionId) {
                // We're answering a specific question
                console.log('Sending answer to question:', questionId);
                socket.emit('answer', {
                    room_id: messageForm.dataset.roomId,
                    content: content,
                    question_id: questionId
                });
                
                // Clear the reply indicator
                const replyIndicator = document.getElementById('reply-indicator');
                if (replyIndicator) {
                    replyIndicator.remove();
                }
                
                // Reset the message input
                messageInput.removeAttribute('data-answering-question');
                messageInput.placeholder = 'Type your message...';
            } else {
                // Regular message or question
                socket.emit('message', {
                    room_id: messageForm.dataset.roomId,
                    content: content,
                    is_question: isQuestion,
                    points_offered: points
                });
            }
            
            // Clear form
            messageInput.value = '';
            if (isQuestion) {
                document.getElementById('is-question').checked = false;
                pointsInput.value = '';
                pointsInput.style.display = 'none';
            }
            
            // Re-enable submit button after a short delay
            setTimeout(() => {
                submitButton.disabled = false;
            }, 500);
        });
    }
}

function handleAnswerClick(questionId) {
    const messageInput = document.getElementById('message-input');
    const questionElement = document.querySelector(`.message[data-message-id="${questionId}"]`);
    
    if (!questionElement) {
        console.error('Question element not found');
        return;
    }

    // Create or get the reply indicator
    let replyIndicator = document.getElementById('reply-indicator');
    if (!replyIndicator) {
        replyIndicator = document.createElement('div');
        replyIndicator.id = 'reply-indicator';
        replyIndicator.className = 'reply-indicator bg-light p-2 mb-2 rounded border-start border-4 border-primary d-flex justify-content-between align-items-center';
        messageInput.parentElement.insertBefore(replyIndicator, messageInput);
    }

    // Get the question content
    const questionContent = questionElement.querySelector('.mb-0').textContent;
    
    // Update reply indicator
    replyIndicator.innerHTML = `
        <div>
            <small class="text-muted">Answering question:</small>
            <div class="text-truncate" style="max-width: 300px;">${questionContent}</div>
        </div>
        <button type="button" class="btn-close" aria-label="Cancel reply"></button>
    `;

    // Handle cancel reply
    replyIndicator.querySelector('.btn-close').addEventListener('click', function() {
        replyIndicator.remove();
        messageInput.removeAttribute('data-answering-question');
        messageInput.placeholder = 'Type your message...';
    });

    messageInput.focus();
    messageInput.setAttribute('data-answering-question', questionId);
    messageInput.placeholder = 'Type your answer...';
    
    // Hide question checkbox and points input when answering
    const isQuestionCheckbox = document.getElementById('is-question');
    const pointsInput = document.getElementById('points-input');
    if (isQuestionCheckbox) isQuestionCheckbox.checked = false;
    if (pointsInput) pointsInput.style.display = 'none';
    
    // Scroll the question into view
    questionElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function handleAcceptAnswer(answerId) {
    socket.emit('accept_answer', { answer_id: answerId });
}

function handleRating(messageId, rating) {
    socket.emit('rate_answer', { 
        message_id: messageId,
        rating: rating
    });
    
    // Update the stars UI
    const stars = document.querySelectorAll(`.rating-container[data-message-id="${messageId}"] .rating-stars i`);
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

function initializeSocket() {
    if (!socket) {
        console.error('Socket not initialized');
        return;
    }

    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const roomId = messageForm ? messageForm.dataset.roomId : null;

    if (messageForm && messageInput && roomId) {
        console.log('Setting up message form handlers for room:', roomId);
        
        // Join room
        console.log('Joining room:', roomId);
        socket.emit('join', { room_id: roomId });

        // Handle page unload
        window.addEventListener('beforeunload', function() {
            console.log('Leaving room:', roomId);
            socket.emit('leave', { room_id: roomId });
        });
    }

    // Socket event handlers
    socket.on('message', (data) => {
        console.log('Received message:', data);
        appendMessage(data);
    });

    socket.on('answer_accepted', (data) => {
        console.log('Answer accepted:', data);
        const answerElement = document.querySelector(`.message[data-message-id="${data.answer_id}"]`);
        if (answerElement) {
            answerElement.classList.add('accepted-answer');
            showToast(`Answer accepted! ${data.points_transferred} points transferred.`, 'success');
        }
    });

    socket.on('rating_updated', (data) => {
        console.log('Rating updated:', data);
        showToast(`Rating submitted successfully! New rating: ${data.new_rating}`, 'success');
    });

    socket.on('user_joined', (data) => {
        console.log('User joined:', data);
        showToast(`${data.username} joined the room`, 'info');
        updateActiveMembers(data.active_members);
    });

    socket.on('user_left', (data) => {
        console.log('User left:', data);
        showToast(`${data.username} left the room`, 'info');
        updateActiveMembers(data.active_members);
    });

    socket.on('error', (data) => {
        console.error('Server error:', data);
        showToast(data.message || 'An error occurred', 'error');
        
        // Re-enable form if points deduction failed
        if (data.message && data.message.includes('points')) {
            const messageForm = document.getElementById('message-form');
            const submitButton = messageForm.querySelector('button[type="submit"]');
            submitButton.disabled = false;
        }
    });

    socket.on('points_update', (data) => {
        console.log('Points updated:', data);
        updateUserPoints(data.points);
    });

    // Handle vote button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.vote-btn')) {
            const btn = e.target.closest('.vote-btn');
            const messageId = btn.closest('.vote-buttons').dataset.messageId;
            const voteType = btn.dataset.voteType;
            
            socket.emit('vote_message', {
                message_id: messageId,
                vote_type: voteType
            });
        }
    });

    // Handle vote updates from server
    socket.on('vote_updated', function(data) {
        const messageElement = document.querySelector(`.vote-buttons[data-message-id="${data.message_id}"]`);
        if (messageElement) {
            messageElement.querySelector('.likes-count').textContent = `Upvote (${data.likes || 0})`;
            messageElement.querySelector('.dislikes-count').textContent = `Downvote (${data.dislikes || 0})`;
        }
    });
}

function initializeAutoRefresh() {
    // Auto-refresh room topics periodically
    setInterval(updateRoomTopics, 120000); // Every 2 minutes
}

function appendMessage(data) {
    const messagesContainer = document.querySelector('.chat-messages');
    if (!messagesContainer) {
        console.error('Messages container not found');
        return;
    }

    try {
        const messageDiv = document.createElement('div');
        // Set proper classes for questions and answers
        let messageClasses = ['message'];
        if (data.is_question) messageClasses.push('question');
        if (data.is_answer) messageClasses.push('answer');
        if (data.user_id === currentUserId) messageClasses.push('sent');
        else messageClasses.push('received');
        messageDiv.className = messageClasses.join(' ');
        messageDiv.setAttribute('data-message-id', data.id);
        messageDiv.setAttribute('data-user-id', data.user_id);

        // If this is an answer, add parent question reference and styling
        if (data.parent_id) {
            messageDiv.setAttribute('data-parent-id', data.parent_id);
            messageDiv.style.marginLeft = '2rem';
            messageDiv.style.borderLeft = '2px solid #007bff';
            
            // Find parent question
            const parentQuestion = document.querySelector(`.message[data-message-id="${data.parent_id}"]`);
            if (parentQuestion) {
                // Insert answer after the parent question
                let insertAfter = parentQuestion;
                // Find the last answer to this question
                const existingAnswers = document.querySelectorAll(`.message[data-parent-id="${data.parent_id}"]`);
                if (existingAnswers.length > 0) {
                    insertAfter = existingAnswers[existingAnswers.length - 1];
                }
                insertAfter.parentNode.insertBefore(messageDiv, insertAfter.nextSibling);
            } else {
                // If parent question not found, append at the end
                messagesContainer.appendChild(messageDiv);
            }
        } else {
            // Regular message or question - append at the end
            messagesContainer.appendChild(messageDiv);
        }

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        // If this is an answer, show what question it's answering
        if (data.parent_id) {
            const answerIndicator = document.createElement('div');
            answerIndicator.className = 'answer-indicator small text-muted mb-1';
            const questionElement = document.querySelector(`.message[data-message-id="${data.parent_id}"]`);
            if (questionElement) {
                const questionText = questionElement.querySelector('.mb-0').textContent;
                answerIndicator.innerHTML = `
                    <i class="fas fa-reply text-primary"></i>
                    <span>Replying to: ${questionText.substring(0, 50)}${questionText.length > 50 ? '...' : ''}</span>
                `;
                messageContent.appendChild(answerIndicator);
            }
        }
        
        // Header with username and points (if question)
        const header = document.createElement('div');
        header.className = 'd-flex justify-content-between align-items-start';
        
        const username = document.createElement('small');
        username.className = 'text-muted';
        username.textContent = data.username;
        header.appendChild(username);
        
        if (data.is_question) {
            const pointsBadge = document.createElement('span');
            pointsBadge.className = 'points-badge';
            pointsBadge.textContent = `${data.points_offered} points`;
            header.appendChild(pointsBadge);
        }
        
        messageContent.appendChild(header);
        
        const text = document.createElement('p');
        text.className = 'mb-0';
        text.textContent = data.content;
        messageContent.appendChild(text);
        
        const metadata = document.createElement('div');
        metadata.className = 'message-metadata';
        
        const timestamp = document.createElement('small');
        timestamp.className = 'text-muted float-end';
        timestamp.textContent = data.timestamp;
        
        metadata.appendChild(timestamp);
        messageContent.appendChild(metadata);
        
        // Add message actions
        const actions = document.createElement('div');
        actions.className = 'message-actions';
        
        // Show answer button for questions that aren't from the current user
        if (data.is_question && data.user_id !== currentUserId) {
            const answerBtn = document.createElement('button');
            answerBtn.className = 'btn btn-sm btn-outline-success answer-btn';
            answerBtn.setAttribute('data-question-id', data.id);
            answerBtn.textContent = `Answer (${data.points_offered} points)`;
            actions.appendChild(answerBtn);
        }
        
        // Show accept answer button for answers to the current user's questions
        if (data.parent_id) {
            const question = document.querySelector(`.message[data-message-id="${data.parent_id}"]`);
            if (question && parseInt(question.dataset.userId) === currentUserId && !data.accepted_answer_id) {
                const acceptBtn = document.createElement('button');
                acceptBtn.className = 'btn btn-sm btn-outline-primary accept-answer-btn';
                acceptBtn.setAttribute('data-answer-id', data.id);
                acceptBtn.textContent = 'Accept Answer';
                actions.appendChild(acceptBtn);
            }
        }
        
        messageContent.appendChild(actions);
        messageDiv.appendChild(messageContent);
        messagesContainer.appendChild(messageDiv);
        scrollToBottom(messagesContainer);
        
        console.log('Message appended successfully with data:', data);
    } catch (error) {
        console.error('Error appending message:', error);
    }
}

function updateActiveMembers(members) {
    try {
        const container = document.getElementById('active-members');
        if (container) {
            // Handle case where members is undefined or null
            const membersList = Array.isArray(members) ? members : [];
            container.innerHTML = membersList.map(member => `
                <span class="badge bg-success me-1">${member}</span>
            `).join('');
        }
    } catch (error) {
        console.error('Error updating active members:', error);
    }
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
    try {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        const container = document.getElementById('toast-container') || document.body;
        container.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000
        });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    } catch (error) {
        console.error('Error showing toast:', error);
    }
}

function updateUserPoints(points) {
    const pointsDisplay = document.querySelector('.card-body .badge.bg-warning.text-dark');
    if (pointsDisplay) {
        pointsDisplay.textContent = points;
    }
}

function scrollToBottom(container) {
    try {
        container.scrollTop = container.scrollHeight;
    } catch (error) {
        console.error('Error scrolling to bottom:', error);
    }
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

function formatTime(date) {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    const options = {
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return date.toLocaleString('en-US', options);
}

function formatDate(date) {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return date.toLocaleString('en-US', options);
}

// Export functions for use in other scripts
window.chatUtils = {
    showToast,
    formatDate,
    formatTime,
    debounce
}; 