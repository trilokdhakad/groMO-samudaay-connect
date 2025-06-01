from flask import render_template, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.main import bp
from app.models import User, UserProfile, Message, Room
from app import db
from app.chat.routes import INDIAN_STATES, PRODUCT_CATEGORIES  # Import product categories
from datetime import datetime, timedelta

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