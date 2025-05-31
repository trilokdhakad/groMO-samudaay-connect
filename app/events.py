from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import Message, Room, User, Rating, RoomMembership
from app.moderation import check_message
from datetime import datetime
import json
import os

def load_vulgar_words():
    """Load vulgar words directly from JSON file."""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'vulgar_words.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except Exception as e:
        print(f"Error loading vulgar words: {str(e)}")
        return set()

def contains_vulgar_words(content):
    """Check if content contains any vulgar words."""
    vulgar_words = load_vulgar_words()
    if not vulgar_words:
        return False
        
    # Convert content to lowercase and split into words
    words = content.lower().split()
    
    # Strip punctuation from each word
    words = [word.strip('.,!?()[]{}":;') for word in words]
    
    # Check if any word matches vulgar words
    return any(word in vulgar_words for word in words)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if not current_user.is_authenticated:
        return False  # reject connection if user not authenticated
    print(f"Client connected: {current_user.username}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        print(f"Client disconnected: {current_user.username}")

@socketio.on('join')
def handle_join(data):
    """Handle user joining a room"""
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    if not room_id:
        return
        
    join_room(str(room_id))
    print(f"User {current_user.username} joined room {room_id}")
    
    # Update room membership
    try:
        membership = RoomMembership.query.filter_by(
            user_id=current_user.id,
            room_id=room_id
        ).first()
        
        if not membership:
            membership = RoomMembership(user=current_user, room_id=room_id)
            db.session.add(membership)
            
        membership.is_active = True
        membership.last_active = datetime.utcnow()
        db.session.commit()
        
        # Get active members
        room = Room.query.get(room_id)
        active_members = [m.user.username for m in room.memberships.filter_by(is_active=True).all()] if room else []
        
        # Notify room
        emit('user_joined', {
            'username': current_user.username,
            'user_id': current_user.id,
            'active_members': active_members
        }, room=str(room_id))
    except Exception as e:
        print(f"Error in handle_join: {str(e)}")
        db.session.rollback()

@socketio.on('leave')
def handle_leave(data):
    """Handle user leaving a room"""
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    if room_id:
        leave_room(str(room_id))
        print(f"User {current_user.username} left room {room_id}")
        
        try:
            # Update membership
            membership = RoomMembership.query.filter_by(
                user_id=current_user.id,
                room_id=room_id
            ).first()
            
            if membership:
                membership.is_active = False
                membership.last_active = datetime.utcnow()
                db.session.commit()
                
                # Get active members after user left
                room = Room.query.get(room_id)
                active_members = [m.user.username for m in room.memberships.filter_by(is_active=True).all()] if room else []
                
                # Notify room
                emit('user_left', {
                    'username': current_user.username,
                    'user_id': current_user.id,
                    'active_members': active_members
                }, room=str(room_id))
        except Exception as e:
            print(f"Error in handle_leave: {str(e)}")
            db.session.rollback()

@socketio.on('message')
def handle_message(data):
    """Handle new messages and questions"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'You must be logged in to send messages'}, room=request.sid)
        return
        
    room_id = data.get('room_id')
    content = data.get('content', '').strip()
    is_question = data.get('is_question', False)
    points_offered = int(data.get('points_offered', 0))
    
    if not room_id or not content:
        emit('error', {'message': 'Invalid message data'}, room=request.sid)
        return
    
    # STRICT WORD CHECK - Do this before any other processing
    if contains_vulgar_words(content):
        print(f"BLOCKED INAPPROPRIATE MESSAGE from {current_user.username} in room {room_id}: {content}")
        emit('error', {'message': 'Your message contains inappropriate language and cannot be sent.'}, room=request.sid)
        return
        
    try:
        # STRICT MODERATION CHECK
        is_appropriate, warning = check_message(content)
        if not is_appropriate:
            print(f"BLOCKED MESSAGE from {current_user.username} in room {room_id}: {content}")
            emit('error', {'message': warning}, room=request.sid)
            return
            
        # Points check for questions
        if is_question and points_offered > 0:
            if not current_user.can_afford_question(points_offered):
                emit('error', {'message': 'Not enough points to ask this question'}, room=request.sid)
                return
                
            if not current_user.deduct_points(points_offered):
                emit('error', {'message': 'Failed to deduct points'}, room=request.sid)
                return
        
        # Create and save message
        message = Message(
            content=content,
            author=current_user,
            room_id=room_id,
            is_question=is_question,
            points_offered=points_offered if is_question else 0
        )
        
        db.session.add(message)
        db.session.commit()
        print(f"Message saved from {current_user.username} in room {room_id}")
        
        # Broadcast the message
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
        }, room=str(room_id))
        
    except Exception as e:
        print(f"Error in handle_message: {str(e)}")
        db.session.rollback()
        emit('error', {'message': 'Error saving message'}, room=request.sid)

@socketio.on('answer')
def handle_answer(data):
    """Handle answers to questions"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'You must be logged in to answer questions'}, room=request.sid)
        return
        
    room_id = data.get('room_id')
    content = data.get('content', '').strip()
    question_id = data.get('question_id')
    
    if not all([room_id, content, question_id]):
        emit('error', {'message': 'Missing required data for answer'}, room=request.sid)
        return
        
    # STRICT WORD CHECK - Do this before any other processing
    if contains_vulgar_words(content):
        print(f"BLOCKED INAPPROPRIATE ANSWER from {current_user.username} in room {room_id}: {content}")
        emit('error', {'message': 'Your answer contains inappropriate language and cannot be sent.'}, room=request.sid)
        return
        
    try:
        # STRICT MODERATION CHECK
        is_appropriate, warning = check_message(content)
        if not is_appropriate:
            print(f"BLOCKED ANSWER from {current_user.username} in room {room_id}: {content}")
            emit('error', {'message': warning}, room=request.sid)
            return
            
        # Get the question being answered
        question = Message.query.get(question_id)
        if not question or not question.is_question:
            emit('error', {'message': 'Invalid question ID'}, room=request.sid)
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
        print(f"Answer saved from {current_user.username} in room {room_id}")
        
        # Broadcast the answer
        emit('message', {
            'id': answer.id,
            'content': answer.content,
            'username': current_user.username,
            'timestamp': answer.timestamp.strftime('%H:%M'),
            'is_answer': True,
            'parent_id': question_id,
            'user_id': current_user.id,
            'room_id': room_id
        }, room=str(room_id))
        
    except Exception as e:
        print(f"Error in handle_answer: {str(e)}")
        db.session.rollback()
        emit('error', {'message': 'Error saving answer'}, room=request.sid)

@socketio.on('start_answer')
def handle_start_answer(data):
    """Handle when a user starts answering a question"""
    if not current_user.is_authenticated:
        return
        
    question_id = data.get('question_id')
    if not question_id:
        return
        
    question = Message.query.get(question_id)
    if not question or not question.is_question:
        emit('error', {'message': 'Invalid question'})
        return
        
    # Join the question's room to receive updates
    join_room(f'question_{question_id}')
    
    emit('answer_started', {
        'question_id': question_id,
        'username': current_user.username
    }, room=question.room_id)

@socketio.on('cancel_answer')
def handle_cancel_answer(data):
    """Handle when a user cancels answering a question"""
    if not current_user.is_authenticated:
        return
        
    question_id = data.get('question_id')
    if not question_id:
        return
        
    question = Message.query.get(question_id)
    if not question:
        return
        
    # Leave the question's room
    leave_room(f'question_{question_id}')
    
    emit('answer_cancelled', {
        'question_id': question_id,
        'username': current_user.username
    }, room=question.room_id)

@socketio.on('get_answers')
def handle_get_answers(data):
    """Get all answers for a question, with optional sorting"""
    if not current_user.is_authenticated:
        return
        
    question_id = data.get('question_id')
    sort_by = data.get('sort_by', 'timestamp')  # Default to timestamp sorting
    
    if not question_id:
        return
        
    question = Message.query.get(question_id)
    if not question or not question.is_question:
        emit('error', {'message': 'Invalid question'})
        return
        
    answers = question.get_answers(sort_by=sort_by)
    answer_data = [answer.to_dict() for answer in answers]
    
    emit('answers_list', {
        'question_id': question_id,
        'answers': answer_data
    })

@socketio.on('get_question_details')
def handle_get_question_details(data):
    """Get question details including all answers and their states"""
    if not current_user.is_authenticated:
        return
        
    question_id = data.get('question_id')
    if not question_id:
        return
        
    question = Message.query.get(question_id)
    if not question or not question.is_question:
        emit('error', {'message': 'Invalid question'})
        return
        
    # Get all answers sorted by rating
    answers = question.get_answers(sort_by='rating')
    answer_data = [answer.to_dict() for answer in answers]
    
    # Add permissions data
    response_data = {
        'question': question.to_dict(),
        'answers': answer_data,
        'permissions': {
            'can_rate': question.user_id == current_user.id,
            'can_select_best': question.user_id == current_user.id and not question.is_closed()
        }
    }
    
    emit('question_details', response_data)

@socketio.on('rate_answer')
def handle_rate_answer(data):
    """Handle rating an answer"""
    print(f"[DEBUG] Rate answer event received: {data}")
    if not current_user.is_authenticated:
        print("[DEBUG] User not authenticated")
        return
    
    message_id = data.get('message_id')
    rating_value = data.get('rating')
    
    print(f"[DEBUG] Rating answer {message_id} with value {rating_value}")
    
    if not message_id or not rating_value:
        emit('error', {'message': 'Invalid rating data'})
        return
    
    message = Message.query.get(message_id)
    if not message or not message.parent_id:
        emit('error', {'message': 'Invalid answer'})
        return
    
    question = Message.query.get(message.parent_id)
    if not question or question.user_id != current_user.id:
        print(f"[DEBUG] Permission denied. Question user: {question.user_id}, Current user: {current_user.id}")
        emit('error', {'message': 'Only the question asker can rate answers'})
        return
    
    # Check for existing rating
    existing_rating = Rating.query.filter_by(
        rater_id=current_user.id,
        message_id=message_id
    ).first()
    
    if existing_rating:
        emit('error', {'message': 'You have already rated this answer'})
        return
    
    try:
        # Create new rating
        rating = Rating(
            rater_id=current_user.id,
            rated_user_id=message.user_id,
            message_id=message_id,
            rating=rating_value
        )
        
        if not rating.can_rate():
            emit('error', {'message': 'Cannot rate your own answer'})
            return
            
        # Add rating to message
        avg_rating = message.add_rating(rating_value)
        
        # Add rating to user's profile
        message.author.update_rating(rating_value)
        
        db.session.add(rating)
        db.session.commit()
        
        print(f"[DEBUG] Successfully rated answer. New average: {avg_rating}")
        
        # Emit to both the room and the question thread
        response_data = {
            'message_id': message_id,
            'rating': rating_value,
            'avg_rating': avg_rating,
            'rating_count': message.rating_count
        }
        emit('answer_rated', response_data, room=question.room_id)
        emit('answer_rated', response_data, room=f'question_{question.id}')
        
    except Exception as e:
        print(f"[DEBUG] Error rating answer: {str(e)}")
        emit('error', {'message': str(e)})
        return

@socketio.on('accept_answer')
def handle_accept_answer(data):
    """Handle selecting the best answer"""
    print(f"[DEBUG] Accept answer event received: {data}")
    if not current_user.is_authenticated:
        print("[DEBUG] User not authenticated")
        return
    
    answer_id = data.get('answer_id')
    if not answer_id:
        emit('error', {'message': 'Missing answer ID'}, room=request.sid)
        return
    
    print(f"[DEBUG] Accepting answer {answer_id}")
    
    try:
        answer = Message.query.get(answer_id)
        if not answer or not answer.parent_id:
            emit('error', {'message': 'Invalid answer'}, room=request.sid)
            return
        
        question = Message.query.get(answer.parent_id)
        if not question:
            emit('error', {'message': 'Question not found'}, room=request.sid)
            return
            
        if question.user_id != current_user.id:
            print(f"[DEBUG] Permission denied. Question user: {question.user_id}, Current user: {current_user.id}")
            emit('error', {'message': 'Only the question asker can select the best answer'}, room=request.sid)
            return
        
        if question.is_closed():
            emit('error', {'message': 'This question already has an accepted answer'}, room=request.sid)
            return
        
        success = question.accept_answer(answer_id, db.session)
        if success:
            print(f"[DEBUG] Successfully accepted answer {answer_id} for question {question.id}")
            # Emit to both the room and the question thread
            response_data = {
                'answer_id': answer_id,
                'question_id': question.id,
                'points_transferred': question.points_offered
            }
            emit('answer_accepted', response_data, room=str(question.room_id))
            emit('answer_accepted', response_data, room=f'question_{question.id}')
            
            # Notify the answer author about points received
            if question.points_offered > 0:
                emit('points_update', {
                    'points': answer.author.points
                }, room=str(answer.author.id))
        else:
            print("[DEBUG] Failed to accept answer")
            emit('error', {'message': 'Failed to accept answer'}, room=request.sid)
            
    except Exception as e:
        print(f"[DEBUG] Error accepting answer: {str(e)}")
        db.session.rollback()
        emit('error', {'message': f'Error accepting answer: {str(e)}'}, room=request.sid)

@socketio.on('vote_message')
def handle_vote(data):
    """Handle message votes (likes/dislikes)"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'You must be logged in to vote'}, room=request.sid)
        return

    message_id = data.get('message_id')
    vote_type = data.get('vote_type')  # 'like' or 'dislike'

    if not message_id or vote_type not in ['like', 'dislike']:
        emit('error', {'message': 'Invalid vote data'}, room=request.sid)
        return

    try:
        message = Message.query.get(message_id)
        if not message:
            emit('error', {'message': 'Message not found'}, room=request.sid)
            return

        # Process the vote
        new_likes, new_dislikes = message.vote(current_user.id, vote_type)

        # Broadcast vote update to all users in the room
        emit('vote_updated', {
            'message_id': message_id,
            'likes': new_likes,
            'dislikes': new_dislikes
        }, room=str(message.room_id))

    except Exception as e:
        print(f"Error in handle_vote: {str(e)}")
        db.session.rollback()
        emit('error', {'message': 'Error processing vote'}, room=request.sid) 