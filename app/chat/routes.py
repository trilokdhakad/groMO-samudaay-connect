from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, socketio
from app.chat import bp
from app.models import Room, Message, RoomMembership
from app.forms import CreateRoomForm
from app.text_analysis import text_analyzer
from datetime import datetime, timedelta
import json
from collections import defaultdict
from flask_socketio import emit, join_room, leave_room

# Predefined lists of states and products
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi"
]

PRODUCT_CATEGORIES = [
    "Credit Cards",
    "Demat Accounts",
    "Loans",
    "Savings Account",
    "Insurance",
    "Line of Credit",
    "Investment"
]

@bp.route('/rooms')
@login_required
def rooms():
    # Get filter parameters
    state = request.args.get('state', '')
    product = request.args.get('product', '')
    
    # Query rooms with filters
    query = Room.query
    
    # Only show rooms that follow the State - Product format
    query = query.filter(Room.name.like('% - %'))
    
    if state:
        query = query.filter(Room.name.like(f"{state} - %"))
    if product:
        query = query.filter(Room.name.like(f"% - {product}"))
    
    rooms = query.all()
    
    return render_template('chat/rooms.html', 
                         rooms=rooms,
                         states=INDIAN_STATES,
                         products=PRODUCT_CATEGORIES,
                         selected_state=state,
                         selected_product=product)

@bp.route('/room/<int:room_id>')
@login_required
def room(room_id):
    room = Room.query.get_or_404(room_id)
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.asc()).all()
    
    # Create or update room membership
    membership = RoomMembership.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if not membership:
        membership = RoomMembership(user=current_user, room=room)
        db.session.add(membership)
    membership.last_active = datetime.utcnow()
    membership.is_active = True
    db.session.commit()
    
    return render_template('chat/room.html', room=room, messages=messages)

@bp.route('/room/<int:room_id>/topics')
@login_required
def room_topics(room_id):
    """Get current topics for a room."""
    room = Room.query.get_or_404(room_id)
    
    # Update topics if needed
    if (not room.last_topic_update or 
        datetime.utcnow() - room.last_topic_update > timedelta(minutes=30)):
        room.update_topic_model(text_analyzer)
    
    try:
        # Get topic data
        topic_data = json.loads(room.topic_data or '{}')
        
        # Format topics for display
        topics = []
        for topic in topic_data.get('topics', []):
            topics.append({
                'id': topic['id'] + 1,  # Make it 1-based for display
                'keywords': topic['keywords'],
                'weight': topic['size'],
                'examples': topic['documents'][:3]  # Up to 3 example messages
            })
        
        # Sort topics by weight
        topics.sort(key=lambda x: x['weight'], reverse=True)
        
        return jsonify({
            'success': True,
            'topics': topics,
            'last_update': room.last_topic_update.isoformat() if room.last_topic_update else None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@bp.route('/room/<int:room_id>/leave')
@login_required
def leave_room(room_id):
    """Leave a chat room."""
    membership = RoomMembership.query.filter_by(user_id=current_user.id, room_id=room_id).first()
    if membership:
        membership.is_active = False
        membership.last_active = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('chat.rooms'))

@bp.route('/room/<int:room_id>/analytics')
@login_required
def room_analytics(room_id):
    """Get analytics data for a room."""
    room = Room.query.get_or_404(room_id)
    
    # Get messages from the last 24 hours
    cutoff = datetime.utcnow() - timedelta(days=1)
    messages = Message.query.filter(
        Message.room_id == room_id,
        Message.timestamp >= cutoff
    ).order_by(Message.timestamp.asc()).all()
    
    # Initialize data structures
    emotion_counts = defaultdict(int)
    intent_counts = defaultdict(int)
    timeline_data = {
        'labels': [],
        'datasets': defaultdict(list)
    }
    
    # Group messages by hour for timeline
    hour_groups = defaultdict(lambda: defaultdict(int))
    
    for message in messages:
        # Update overall counts
        emotion_counts[message.primary_emotion] += 1
        intent_counts[message.intent] += 1
        
        # Update hourly data
        hour = message.timestamp.strftime('%H:00')
        hour_groups[hour][message.primary_emotion] += 1
    
    # Sort hours and prepare timeline data
    sorted_hours = sorted(hour_groups.keys())
    timeline_data['labels'] = sorted_hours
    
    # Get all unique emotions
    all_emotions = set(emotion_counts.keys())
    
    # Initialize datasets with zeros for all hours
    for emotion in all_emotions:
        timeline_data['datasets'][emotion] = [0] * len(sorted_hours)
    
    # Fill in the actual values
    for i, hour in enumerate(sorted_hours):
        for emotion in all_emotions:
            timeline_data['datasets'][emotion][i] = hour_groups[hour][emotion]
    
    # Calculate distributions as percentages
    total_messages = len(messages) or 1  # Avoid division by zero
    emotion_distribution = {
        emotion: (count / total_messages) * 100
        for emotion, count in emotion_counts.items()
    }
    intent_distribution = {
        intent: (count / total_messages) * 100
        for intent, count in intent_counts.items()
    }
    
    return jsonify({
        'success': True,
        'emotion_timeline': timeline_data,
        'emotion_distribution': emotion_distribution,
        'intent_distribution': intent_distribution,
        'last_update': datetime.utcnow().isoformat()
    })

@socketio.on('join')
def on_join(data):
    """Event handler for when a user joins a room."""
    room_id = data.get('room_id')
    if room_id:
        join_room(room_id)
        emit('user_joined', {
            'username': current_user.username,
            'room_id': room_id
        }, room=room_id)

@socketio.on('leave')
def on_leave(data):
    """Event handler for when a user leaves a room."""
    room_id = data.get('room_id')
    if room_id:
        leave_room(room_id)
        emit('user_left', {
            'username': current_user.username,
            'room_id': room_id
        }, room=room_id)

@socketio.on('message')
def handle_message(data):
    """Event handler for new messages."""
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    content = data.get('content')
    is_question = data.get('is_question', False)
    points_offered = data.get('points_offered', 0)
    
    if not room_id or not content:
        return
        
    try:
        # Create message
        message = Message(
            content=content,
            author=current_user,
            room_id=room_id,
            is_question=is_question,
            points_offered=points_offered
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Broadcast the message
        emit('message', message.to_dict(), room=room_id)
    except Exception as e:
        print("Error saving message:", str(e))
        db.session.rollback()
        emit('error', {'message': 'Error saving message: ' + str(e)})

@socketio.on('answer')
def handle_answer(data):
    """Event handler for answers to questions."""
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    content = data.get('content')
    question_id = data.get('question_id')
    
    if not all([room_id, content, question_id]):
        emit('error', {'message': 'Missing required data for answer'})
        return
        
    try:
        # Get the question being answered
        question = Message.query.get(question_id)
        if not question or not question.is_question:
            emit('error', {'message': 'Invalid question ID'})
            return
            
        # Create answer message
        answer = Message(
            content=content,
            author=current_user,
            room_id=room_id,
            parent_id=question_id,
            is_answer=True
        )
        
        db.session.add(answer)
        db.session.commit()
        
        # Broadcast the answer
        answer_data = answer.to_dict()
        answer_data['parent_id'] = question_id
        emit('message', answer_data, room=room_id)
    except Exception as e:
        print("Error saving answer:", str(e))
        db.session.rollback()
        emit('error', {'message': 'Error saving answer: ' + str(e)})

@socketio.on('accept_answer')
def handle_accept_answer(data):
    """Event handler for accepting answers."""
    if not current_user.is_authenticated:
        return
        
    answer_id = data.get('answer_id')
    if not answer_id:
        emit('error', {'message': 'Missing answer ID'})
        return
        
    try:
        # Get the answer and its question
        answer = Message.query.get(answer_id)
        if not answer or not answer.parent_id:
            emit('error', {'message': 'Invalid answer'})
            return
            
        question = Message.query.get(answer.parent_id)
        if not question or question.author_id != current_user.id:
            emit('error', {'message': 'You can only accept answers to your own questions'})
            return
            
        if question.accepted_answer_id:
            emit('error', {'message': 'This question already has an accepted answer'})
            return
            
        # Accept the answer and transfer points
        question.accepted_answer_id = answer_id
        points_transferred = question.points_offered
        
        # Transfer points from question author to answer author
        question.author.points -= points_transferred
        answer.author.points += points_transferred
        
        db.session.commit()
        
        # Notify clients
        emit('answer_accepted', {
            'answer_id': answer_id,
            'question_id': question.id,
            'points_transferred': points_transferred
        }, room=question.room_id)
        
    except Exception as e:
        print("Error accepting answer:", str(e))
        db.session.rollback()
        emit('error', {'message': 'Error accepting answer: ' + str(e)}) 