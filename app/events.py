from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import Message, Room, User, Rating
from app.text_analyzer import TextAnalyzer

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False
    print(f'Client connected: {current_user.username}')

@socketio.on('disconnect')
def handle_disconnect():
    if not current_user.is_authenticated:
        return
    print(f'Client disconnected: {current_user.username}')

@socketio.on('join')
def handle_join(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    if not room_id:
        return
    
    room = Room.query.get(room_id)
    if not room:
        return
    
    join_room(room_id)
    membership = room.get_member(current_user)
    if membership:
        membership.is_active = True
        db.session.commit()
    
    active_members = [m.user.username for m in room.memberships if m.is_active]
    emit('user_joined', {
        'username': current_user.username,
        'active_members': active_members
    }, room=room_id)

@socketio.on('leave')
def handle_leave(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    if not room_id:
        return
    
    room = Room.query.get(room_id)
    if not room:
        return
    
    leave_room(room_id)
    membership = room.get_member(current_user)
    if membership:
        membership.is_active = False
        db.session.commit()
    
    active_members = [m.user.username for m in room.memberships if m.is_active]
    emit('user_left', {
        'username': current_user.username,
        'active_members': active_members
    }, room=room_id)

@socketio.on('message')
def handle_message(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    content = data.get('content')
    is_question = data.get('is_question', False)
    points_offered = data.get('points_offered', 0)
    parent_id = data.get('parent_id')
    
    if not room_id or not content:
        return
    
    room = Room.query.get(room_id)
    if not room:
        return
    
    # If this is an answer, check if the question is closed
    if parent_id:
        parent_message = Message.query.get(parent_id)
        if not parent_message:
            emit('error', {'message': 'Invalid question'})
            return
        if parent_message.is_closed():
            emit('error', {'message': 'This question already has an accepted answer'})
            return
    
    # Check if user has enough points for the question
    if is_question and points_offered > 0:
        if not current_user.can_afford_question(points_offered):
            emit('error', {
                'message': 'Not enough points to offer for this question'
            })
            return
        current_user.deduct_points(points_offered)
    
    # Create and analyze message
    message = Message(
        content=content,
        author=current_user,
        room_id=room_id,
        is_question=is_question,
        points_offered=points_offered,
        parent_id=parent_id
    )
    
    # Analyze message content
    analyzer = TextAnalyzer()
    message.update_analysis(analyzer)
    
    db.session.add(message)
    db.session.commit()
    
    # Prepare response data
    response_data = message.to_dict()
    
    # If this is an answer, also emit to parent question's thread
    if parent_id:
        emit('new_answer', response_data, room=f'question_{parent_id}')
    
    emit('message', response_data, room=room_id)

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
        return
    
    print(f"[DEBUG] Accepting answer {answer_id}")
    
    answer = Message.query.get(answer_id)
    if not answer or not answer.parent_id:
        emit('error', {'message': 'Invalid answer'})
        return
    
    question = Message.query.get(answer.parent_id)
    if not question or question.user_id != current_user.id:
        print(f"[DEBUG] Permission denied. Question user: {question.user_id}, Current user: {current_user.id}")
        emit('error', {'message': 'Only the question asker can select the best answer'})
        return
    
    if question.accept_answer(answer_id, db.session):
        print(f"[DEBUG] Successfully accepted answer {answer_id} for question {question.id}")
        # Emit to both the room and the question thread
        response_data = {
            'answer_id': answer_id,
            'question_id': question.id,
            'points_transferred': question.points_offered
        }
        emit('answer_accepted', response_data, room=question.room_id)
        emit('answer_accepted', response_data, room=f'question_{question.id}')
    else:
        print("[DEBUG] Failed to accept answer")
        emit('error', {'message': 'Failed to accept answer'}) 