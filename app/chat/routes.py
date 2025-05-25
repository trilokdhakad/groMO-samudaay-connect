from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.chat import bp
from app.models import Room, Message, RoomMembership
from app.forms import CreateRoomForm
from app.text_analysis import text_analyzer
from datetime import datetime, timedelta
import json
from collections import defaultdict

@bp.route('/rooms')
@login_required
def rooms():
    rooms = Room.query.all()
    return render_template('chat/rooms.html', rooms=rooms)

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

@bp.route('/create_room', methods=['GET', 'POST'])
@login_required
def create_room():
    form = CreateRoomForm()
    if form.validate_on_submit():
        room = Room(name=form.name.data, description=form.description.data)
        db.session.add(room)
        
        # Create room membership for creator
        membership = RoomMembership(user=current_user, room=room)
        db.session.add(membership)
        
        db.session.commit()
        flash('Room created successfully!', 'success')
        return redirect(url_for('chat.room', room_id=room.id))
    return render_template('chat/create_room.html', form=form)

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