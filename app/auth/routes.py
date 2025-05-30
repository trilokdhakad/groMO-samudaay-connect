from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.models import User, UserProfile, UserMetrics, UserInterest
from app.auth.forms import LoginForm, RegistrationForm

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create user
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()  # This will assign the user.id

            # Create user profile
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)

            # Create user metrics
            metrics = UserMetrics(user_id=user.id)
            db.session.add(metrics)

            # Create user interests from selected categories
            for category in form.categories.data:
                interest = UserInterest(user_id=user.id, topic=category)
                db.session.add(interest)

            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {str(e)}', 'error')
            return redirect(url_for('auth.register'))
    return render_template('auth/register.html', title='Register', form=form, categories=UserInterest.CATEGORIES)

@bp.route('/make_gp/<username>')
def make_gp(username):
    user = User.query.filter_by(username=username).first_or_404()
    user.is_gp = True
    db.session.commit()
    flash(f'User {username} is now a GP!', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/make_all_gp')
def make_all_gp():
    users = User.query.all()
    count = 0
    for user in users:
        if not user.is_gp:
            user.is_gp = True
            count += 1
    db.session.commit()
    flash(f'Made {count} users GPs!', 'success')
    return redirect(url_for('auth.login')) 