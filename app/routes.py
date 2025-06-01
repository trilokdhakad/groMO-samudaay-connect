from flask import render_template, jsonify, request, url_for
from flask_login import login_required, current_user
from app import app, db, socketio
from app.models import User, Room, Message, Rating
from app.recommendations import get_similar_users, get_recommended_rooms, update_user_profile, update_room_profile
from flask_socketio import emit, join_room
from app.moderation import check_message
from sqlalchemy import func, desc, asc
from datetime import datetime

@app.route('/')
@app.route('/index')
@login_required
def index():
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

@app.route('/chat/<int:room_id>')
@login_required
def chat_room(room_id):
    room = Room.query.get_or_404(room_id)
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.asc()).all()
    return render_template('chat/room.html', room=room, messages=messages)

@socketio.on('message')
def handle_message(data):
    """Handle new messages and questions"""
    if not current_user.is_authenticated:
        return
        
    content = data.get('content')
    room_id = data.get('room_id')
    is_question = data.get('is_question', False)
    points_offered = int(data.get('points_offered', 0))
    
    # Check message content first
    is_appropriate, warning = check_message(content)
    if not is_appropriate:
        emit('error', {'message': warning}, room=request.sid)
        return
    
    if is_question:
        # Check if user has enough points
        if not current_user.can_afford_question(points_offered):
            emit('error', {'message': 'Not enough points to ask this question'})
            return
            
        # Deduct points
        if not current_user.deduct_points(points_offered):
            emit('error', {'message': 'Failed to deduct points'})
            return
    
    message = Message(
        content=content,
        author=current_user,
        room_id=room_id,
        is_question=is_question,
        points_offered=points_offered if is_question else 0
    )
    
    db.session.add(message)
    db.session.commit()
    
    # Broadcast the message to all users in the room
    emit('message', {
        'id': message.id,
        'content': message.content,
        'username': current_user.username,
        'timestamp': message.timestamp.strftime('%H:%M'),
        'is_question': message.is_question,
        'points_offered': message.points_offered,
        'user_id': current_user.id,
        'parent_id': message.parent_id,
        'accepted_answer_id': message.accepted_answer_id if hasattr(message, 'accepted_answer_id') else None
    }, broadcast=True, room=room_id)

@socketio.on('answer')
def handle_answer(data):
    """Handle answers to questions"""
    if not current_user.is_authenticated:
        return
        
    content = data.get('content')
    question_id = data.get('question_id')
    room_id = data.get('room_id')
    
    question = Message.query.get(question_id)
    if not question or not question.is_question:
        emit('error', {'message': 'Invalid question'})
        return
        
    answer = Message(
        content=content,
        author=current_user,
        room_id=room_id,
        parent_id=question_id
    )
    
    db.session.add(answer)
    db.session.commit()
    
    emit('message', {
        'id': answer.id,
        'content': answer.content,
        'username': current_user.username,
        'timestamp': answer.timestamp.strftime('%H:%M'),
        'is_answer': True,
        'parent_id': question_id,
        'user_id': current_user.id
    }, broadcast=True, room=room_id)

@socketio.on('accept_answer')
def handle_accept_answer(data):
    """Handle accepting an answer"""
    if not current_user.is_authenticated:
        return
        
    answer_id = data.get('answer_id')
    answer = Message.query.get(answer_id)
    
    if not answer or not answer.parent_id:
        emit('error', {'message': 'Invalid answer'})
        return
        
    question = answer.parent_message
    if question.user_id != current_user.id:
        emit('error', {'message': 'Only the question author can accept answers'})
        return
        
    if question.accepted_answer_id:
        emit('error', {'message': 'An answer has already been accepted'})
        return
        
    # Accept the answer and transfer points
    if question.accept_answer(answer_id, db.session):
        emit('answer_accepted', {
            'answer_id': answer_id,
            'question_id': question.id
        }, room=question.room_id)
    else:
        emit('error', {'message': 'Failed to accept answer'})

@socketio.on('rate_answer')
def handle_rating(data):
    """Handle rating an accepted answer"""
    if not current_user.is_authenticated:
        return
        
    message_id = data.get('message_id')
    rating_value = data.get('rating')
    
    message = Message.query.get(message_id)
    if not message:
        emit('error', {'message': 'Invalid message'})
        return
        
    # Create or update rating
    rating = Rating(
        rater_id=current_user.id,
        rated_user_id=message.user_id,
        message_id=message_id,
        rating=rating_value
    )
    
    if not rating.can_rate():
        emit('error', {'message': 'Cannot rate this answer'})
        return
        
    try:
        db.session.add(rating)
        message.author.update_rating(rating_value)
        db.session.commit()
        
        emit('rating_updated', {
            'message_id': message_id,
            'new_rating': message.author.rating
        }, room=message.room_id)
    except Exception as e:
        db.session.rollback()
        emit('error', {'message': 'Failed to submit rating'})

@app.route('/recommendations')
@login_required
def get_recommendations():
    """Get personalized recommendations for the current user"""
    # Update profiles first
    update_user_profile(current_user)
    
    # Get recommendations
    similar_users = get_similar_users(current_user, n=5)
    recommended_rooms = get_recommended_rooms(current_user, n=5)
    
    return render_template('recommendations.html',
                         similar_users=similar_users,
                         recommended_rooms=recommended_rooms)

@app.route('/api/recommendations')
@login_required
def get_recommendations_api():
    """API endpoint for getting recommendations"""
    # Update profiles
    update_user_profile(current_user)
    
    # Get recommendations
    similar_users = [(user.username, score) for user, score in get_similar_users(current_user, n=5)]
    recommended_rooms = [(room.name, score) for room, score in get_recommended_rooms(current_user, n=5)]
    
    return jsonify({
        'similar_users': similar_users,
        'recommended_rooms': recommended_rooms
    })

@socketio.on('join')
def on_join(data):
    """Handle user joining a room"""
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    if room_id:
        join_room(room_id)
        emit('user_joined', {
            'username': current_user.username,
            'user_id': current_user.id
        }, room=room_id) 