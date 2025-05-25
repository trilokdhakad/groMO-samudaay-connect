from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.main import bp
from app.models import User, UserProfile, Message
from app import db

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    return render_template('main/index.html', title='Home')

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