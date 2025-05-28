from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Task, GPTaskStatus, WeeklyLeaderboard, GPProfile
from app.forms import TaskCreationForm, TaskSubmissionForm
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from functools import wraps

bp = Blueprint('gp', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def gp_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_gp:
            flash('You need to be a GP to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Routes
@bp.route('/admin/tasks/create', methods=['GET', 'POST'])
@admin_required
def create_task():
    form = TaskCreationForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            points=form.points.data,
            week_number=form.week_number.data,
            year=form.year.data,
            created_by=current_user
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully!', 'success')
        return redirect(url_for('gp.admin_dashboard'))
    return render_template('gp/create_task.html', form=form)

@bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    pending_submissions = GPTaskStatus.query.filter_by(status='completed').all()
    return render_template('gp/admin_dashboard.html', tasks=tasks, pending_submissions=pending_submissions)

@bp.route('/admin/task/<int:task_id>/submissions')
@admin_required
def task_submissions(task_id):
    task = Task.query.get_or_404(task_id)
    submissions = GPTaskStatus.query.filter_by(task_id=task_id).all()
    return render_template('gp/task_submissions.html', task=task, submissions=submissions)

@bp.route('/admin/submission/<int:submission_id>/review', methods=['POST'])
@admin_required
def review_submission(submission_id):
    submission = GPTaskStatus.query.get_or_404(submission_id)
    action = request.form.get('action')
    
    if action == 'approve':
        submission.status = 'approved'
        submission.approved_by = current_user
        submission.approved_at = datetime.utcnow()
        flash('Submission approved!', 'success')
    elif action == 'reject':
        submission.status = 'rejected'
        flash('Submission rejected!', 'error')
    
    db.session.commit()
    return redirect(url_for('gp.task_submissions', task_id=submission.task_id))

@bp.route('/admin/generate-leaderboard', methods=['POST'])
@admin_required
def generate_leaderboard():
    week_number = int(request.form.get('week_number', datetime.now().isocalendar()[1]))
    year = int(request.form.get('year', datetime.now().year))
    
    # Get all GPs
    gps = User.query.filter_by(is_gp=True).all()
    
    # Clear existing leaderboard for the week
    WeeklyLeaderboard.query.filter_by(week_number=week_number, year=year).delete()
    
    # Calculate points for each GP
    gp_points = []
    for gp in gps:
        completed_tasks = GPTaskStatus.query.filter_by(
            gp_id=gp.id,
            status='approved'
        ).join(Task).filter(
            Task.week_number == week_number,
            Task.year == year
        ).all()
        
        total_points = sum(task.task.points for task in completed_tasks)
        tasks_completed = len(completed_tasks)
        
        gp_points.append({
            'gp': gp,
            'points': total_points,
            'tasks_completed': tasks_completed
        })
    
    # Sort by points and assign ranks
    gp_points.sort(key=lambda x: x['points'], reverse=True)
    current_rank = 1
    current_points = None
    skipped_ranks = 0
    
    for i, entry in enumerate(gp_points):
        if current_points != entry['points']:
            current_rank = i + 1
            current_points = entry['points']
        
        leaderboard_entry = WeeklyLeaderboard(
            gp=entry['gp'],
            week_number=week_number,
            year=year,
            total_points=entry['points'],
            rank=current_rank,
            tasks_completed=entry['tasks_completed']
        )
        db.session.add(leaderboard_entry)
    
    db.session.commit()
    flash('Leaderboard generated successfully!', 'success')
    return redirect(url_for('gp.admin_dashboard'))

# GP Routes
@bp.route('/gp/dashboard')
@gp_required
def gp_dashboard():
    current_week = datetime.now().isocalendar()[1]
    current_year = datetime.now().year
    
    # Get this week's tasks and their status for the current GP
    tasks = Task.query.filter_by(week_number=current_week, year=current_year).all()
    task_statuses = {
        status.task_id: status 
        for status in GPTaskStatus.query.filter_by(gp_id=current_user.id).all()
    }
    
    # Get current leaderboard
    leaderboard = WeeklyLeaderboard.query.filter_by(
        week_number=current_week,
        year=current_year
    ).order_by(WeeklyLeaderboard.rank).all()
    
    return render_template('gp/dashboard.html',
                         tasks=tasks,
                         task_statuses=task_statuses,
                         leaderboard=leaderboard)

@bp.route('/gp/task/<int:task_id>/submit', methods=['GET', 'POST'])
@gp_required
def submit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check if task is already submitted
    existing_submission = GPTaskStatus.query.filter_by(
        task_id=task_id,
        gp_id=current_user.id
    ).first()
    
    if existing_submission and existing_submission.status in ['completed', 'approved']:
        flash('You have already submitted this task!', 'error')
        return redirect(url_for('gp.gp_dashboard'))
    
    form = TaskSubmissionForm()
    if form.validate_on_submit():
        proof_file_path = None
        if form.proof_file.data:
            filename = secure_filename(form.proof_file.data.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.proof_file.data.save(filepath)
            proof_file_path = filename
        
        submission = GPTaskStatus(
            gp_id=current_user.id,
            task_id=task_id,
            status='completed',
            proof_text=form.proof_text.data,
            proof_file_path=proof_file_path,
            submitted_at=datetime.utcnow()
        )
        db.session.add(submission)
        db.session.commit()
        
        flash('Task submitted successfully!', 'success')
        return redirect(url_for('gp.gp_dashboard'))
    
    return render_template('gp/submit_task.html', task=task, form=form)

@bp.route('/leaderboard')
@login_required  # Only requires login, not GP status
def view_leaderboard():
    week_number = request.args.get('week', type=int, default=datetime.now().isocalendar()[1])
    year = request.args.get('year', type=int, default=datetime.now().year)
    
    # Get all users with their points and tasks
    leaderboard = WeeklyLeaderboard.query.filter_by(
        week_number=week_number,
        year=year
    ).order_by(WeeklyLeaderboard.rank).all()
    
    # Get available weeks for the dropdown
    available_weeks = db.session.query(
        WeeklyLeaderboard.week_number,
        WeeklyLeaderboard.year
    ).distinct().order_by(
        WeeklyLeaderboard.year.desc(),
        WeeklyLeaderboard.week_number.desc()
    ).all()
    
    return render_template('gp/leaderboard.html',
                         leaderboard=leaderboard,
                         week_number=week_number,
                         year=year,
                         available_weeks=available_weeks,
                         current_user=current_user)

@bp.route('/admin/update-leaderboard', methods=['POST'])
@admin_required
def update_leaderboard():
    week_number = int(request.form.get('week_number', datetime.now().isocalendar()[1]))
    year = int(request.form.get('year', datetime.now().year))
    
    try:
        # Get all users
        users = User.query.all()
        
        # Clear existing leaderboard for the week
        WeeklyLeaderboard.query.filter_by(week_number=week_number, year=year).delete()
        
        # Calculate points for each user
        user_points = []
        for user in users:
            completed_tasks = GPTaskStatus.query.filter_by(
                gp_id=user.id,
                status='approved'
            ).join(Task).filter(
                Task.week_number == week_number,
                Task.year == year
            ).all()
            
            total_points = sum(task.task.points for task in completed_tasks)
            tasks_completed = len(completed_tasks)
            
            user_points.append({
                'user': user,
                'points': total_points,
                'tasks_completed': tasks_completed
            })
        
        # Sort by points and assign ranks
        user_points.sort(key=lambda x: x['points'], reverse=True)
        current_rank = 1
        current_points = None
        
        for i, entry in enumerate(user_points):
            if current_points != entry['points']:
                current_rank = i + 1
                current_points = entry['points']
            
            leaderboard_entry = WeeklyLeaderboard(
                gp=entry['user'],
                week_number=week_number,
                year=year,
                total_points=entry['points'],
                rank=current_rank,
                tasks_completed=entry['tasks_completed']
            )
            db.session.add(leaderboard_entry)
        
        db.session.commit()
        flash('Leaderboard updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating leaderboard: {str(e)}', 'error')
    
    return redirect(url_for('gp.view_leaderboard', week=week_number, year=year)) 