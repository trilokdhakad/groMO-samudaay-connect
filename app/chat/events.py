from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import Message, Room, UserMetrics, RoomMembership
from app.sentiment import sentiment_analyzer
from datetime import datetime
import json

@socketio.on('join')
def on_join(data):
    """Handle user joining a chat room."""
    room = Room.query.get(data['room_id'])
    if room:
        join_room(str(room.id))
        # Update user metrics and membership
        metrics = UserMetrics.query.filter_by(user_id=current_user.id).first()
        if metrics:
            metrics.rooms_joined += 1
            metrics.last_active = datetime.utcnow()
        
        # Update room membership
        membership = RoomMembership.query.filter_by(user_id=current_user.id, room_id=room.id).first()
        if membership:
            membership.is_active = True
            membership.last_active = datetime.utcnow()
        
        db.session.commit()
        
        # Get active members
        active_members = [m.user.username for m in room.memberships.filter_by(is_active=True).all()]
        
        # Notify others
        emit('user_joined', {
            'username': current_user.username,
            'active_members': active_members
        }, room=str(room.id))

@socketio.on('message')
def handle_message(data):
    """Handle incoming chat messages."""
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    content = data.get('content', '').strip()  # Changed from msg to content
    
    if not room_id or not content:
        return
    
    room = Room.query.get(room_id)
    if not room:
        return
        
    # Create new message
    message = Message(
        content=content,
        author=current_user,
        room=room,
        timestamp=datetime.utcnow()
    )
    
    # Analyze message content
    from app.text_analysis import text_analyzer
    analysis = text_analyzer.analyze_message(content)
    
    # Update message with analysis results
    message.primary_emotion = analysis['emotions']['primary_emotion']
    message.emotion_score = analysis['emotions']['emotion_score']
    message.all_emotions = json.dumps(analysis['emotions']['all_emotions'])
    message.intent = analysis['intent']['intent']
    message.intent_confidence = analysis['intent']['confidence']
    message.all_intents = json.dumps(analysis['intent']['all_intents'])
    
    # Save to database
    db.session.add(message)
    
    # Update user metrics
    if current_user.metrics:
        current_user.metrics.message_count += 1
        current_user.metrics.last_active = datetime.utcnow()
        
        if message.sentiment_label == 'positive':
            current_user.metrics.positive_message_count += 1
        elif message.sentiment_label == 'negative':
            current_user.metrics.negative_message_count += 1
        else:
            current_user.metrics.neutral_message_count += 1
    
    # Update room membership
    membership = RoomMembership.query.filter_by(user_id=current_user.id, room_id=room.id).first()
    if membership:
        membership.messages_sent += 1
        membership.last_active = datetime.utcnow()
    
    db.session.commit()
    
    # Emit message to room with consistent structure
    emit('message', {
        'content': message.content,
        'username': current_user.username,
        'user_id': current_user.id,
        'timestamp': message.timestamp.strftime('%H:%M'),
        'room_id': str(room_id),
        'intent': message.intent,
        'intent_emoji': analysis['intent'].get('emoji', '💬'),
        'primary_emotion': message.primary_emotion,
        'emotion_emoji': analysis['emotions'].get('emoji', '😐')
    }, room=str(room_id))

@socketio.on('leave')
def on_leave(data):
    """Handle user leaving a chat room."""
    room_id = data.get('room_id')
    if room_id:
        leave_room(str(room_id))
        
        # Update room membership
        membership = RoomMembership.query.filter_by(user_id=current_user.id, room_id=room_id).first()
        if membership:
            membership.is_active = False
            db.session.commit()
            
            # Get remaining active members
            room = Room.query.get(room_id)
            if room:
                active_members = [m.user.username for m in room.memberships.filter_by(is_active=True).all()]
                
                # Notify others
                emit('user_left', {
                    'username': current_user.username,
                    'active_members': active_members
                }, room=str(room_id)) 