from flask import render_template, flash, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from app.main import bp
from app.models import User, UserProfile, Message, Room
from app import db
from app.chat.routes import INDIAN_STATES, PRODUCT_CATEGORIES  # Import product categories
from datetime import datetime, timedelta
from sqlalchemy import func, desc, asc

# Define intent colors
INTENT_COLORS = {
    'exploration': 'primary',
    'interested': 'purple',
    'engaging': 'success',
    'problematic': 'danger',
    'insightful': 'warning',
    'progress_oriented': 'success',
    'supportive': 'dark',
    'reflective': 'info'
}

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    return render_template('main/index.html', 
                         title='Home',
                         states=INDIAN_STATES,
                         products=PRODUCT_CATEGORIES,
                         intent_colors=INTENT_COLORS,
                         user_state=current_user.state)

@bp.route('/api/state_analysis/<state>')
@login_required
def state_analysis(state):
    """API endpoint to get product-wise intent analysis for a state"""
    # Get all rooms for the state
    rooms = Room.query.filter(Room.name.like(f'{state} - %')).all()
    
    # Initialize product-wise analysis
    product_analysis = {}
    for product in PRODUCT_CATEGORIES:
        product_analysis[product] = {
            'current_intent': 'exploring',
            'total_rooms': 0,
            'active_rooms': 0,
            'intent_distribution': {}
        }
    
    # Analyze each room
    for room in rooms:
        # Extract product from room name (format: "State - Product")
        try:
            product = room.name.split(' - ')[1]
        except IndexError:
            continue
            
        if product in product_analysis:
            product_analysis[product]['total_rooms'] += 1
            
            # Check for recent activity
            recent_messages = Message.query.filter_by(room_id=room.id)\
                .filter(Message.timestamp >= datetime.utcnow() - timedelta(days=1))\
                .count()
            if recent_messages > 0:
                product_analysis[product]['active_rooms'] += 1
            
            # Update intent data
            if room.current_intent:
                product_analysis[product]['current_intent'] = room.current_intent
                
                # Add to intent distribution
                intent_dist = room.get_intent_distribution()
                for intent, weight in intent_dist.items():
                    if intent not in product_analysis[product]['intent_distribution']:
                        product_analysis[product]['intent_distribution'][intent] = 0
                    product_analysis[product]['intent_distribution'][intent] += weight
    
    # Normalize intent distributions
    for product_data in product_analysis.values():
        if product_data['intent_distribution']:
            total = sum(product_data['intent_distribution'].values())
            product_data['intent_distribution'] = {
                intent: (weight / total) 
                for intent, weight in product_data['intent_distribution'].items()
            }
    
    return jsonify({
        'success': True,
        'data': product_analysis
    })

@bp.route('/profile')
@login_required
def profile():
    # Get or create user profile
    if not current_user.profile:
        profile = UserProfile(user=current_user)
        db.session.add(profile)
        db.session.commit()
    
    return render_template('main/profile.html', 
                         title='Profile',
                         user=current_user,
                         Message=Message)

@bp.route('/message-leaderboard')
@login_required
def message_leaderboard():
    """Display leaderboard based on message likes/dislikes for specific rooms"""
    # Get selected state and room from query parameters
    selected_state = request.args.get('state', '')
    selected_room_id = request.args.get('room_id', type=int)

    # Get all states and their rooms
    states_and_rooms = {}
    for state in INDIAN_STATES:
        rooms = Room.query.filter(Room.name.like(f'{state} - %')).all()
        if rooms:
            states_and_rooms[state] = rooms

    # If state is selected but no room, use the first room of that state
    if selected_state and not selected_room_id and selected_state in states_and_rooms:
        selected_room_id = states_and_rooms[selected_state][0].id

    if selected_room_id:
        # Subquery to get the latest activity timestamp for each user in the room
        latest_activity = db.session.query(
            Message.user_id,
            func.max(Message.timestamp).label('last_activity')
        ).filter(Message.room_id == selected_room_id)\
        .group_by(Message.user_id).subquery()

        # Query to get user stats with their latest activity for the selected room
        user_stats = db.session.query(
            User,
            func.sum(Message.likes).label('total_likes'),
            func.sum(Message.dislikes).label('total_dislikes'),
            latest_activity.c.last_activity
        ).join(Message, User.id == Message.user_id)\
        .filter(Message.room_id == selected_room_id)\
        .join(latest_activity, User.id == latest_activity.c.user_id)\
        .group_by(User)\
        .order_by(
            desc('total_likes'),  # Most likes first
            asc('total_dislikes'),  # Fewer dislikes as tiebreaker
            desc(latest_activity.c.last_activity)  # Most recent activity as second tiebreaker
        ).limit(10).all()

        # Format the data for the template
        leaderboard_data = [{
            'user': user,
            'total_likes': total_likes or 0,
            'total_dislikes': total_dislikes or 0,
            'last_activity': last_activity
        } for user, total_likes, total_dislikes, last_activity in user_stats]

        selected_room = Room.query.get(selected_room_id) if selected_room_id else None
    else:
        leaderboard_data = []
        selected_room = None

    return render_template('main/message_leaderboard.html', 
                         leaderboard=leaderboard_data,
                         states_and_rooms=states_and_rooms,
                         selected_state=selected_state,
                         selected_room=selected_room,
                         current_user=current_user) 