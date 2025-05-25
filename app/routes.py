from flask import render_template, jsonify
from flask_login import login_required, current_user
from app import app
from app.recommendations import get_similar_users, get_recommended_rooms, update_user_profile, update_room_profile

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