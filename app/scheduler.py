from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.models import User, Task, GPTaskStatus, WeeklyLeaderboard
from app import db

def generate_weekly_leaderboard():
    with current_app.app_context():
        current_week = datetime.now().isocalendar()[1]
        current_year = datetime.now().year
        
        # Get all GPs
        gps = User.query.filter_by(is_gp=True).all()
        
        # Clear existing leaderboard for the week
        WeeklyLeaderboard.query.filter_by(week_number=current_week, year=current_year).delete()
        
        # Calculate points for each GP
        for gp in gps:
            completed_tasks = GPTaskStatus.query.filter_by(
                gp_id=gp.id,
                status='approved'
            ).join(Task).filter(
                Task.week_number == current_week,
                Task.year == current_year
            ).all()
            
            total_points = sum(task.task.points for task in completed_tasks)
            tasks_completed = len(completed_tasks)
            
            leaderboard_entry = WeeklyLeaderboard(
                gp=gp,
                week_number=current_week,
                year=current_year,
                total_points=total_points,
                tasks_completed=tasks_completed
            )
            db.session.add(leaderboard_entry)
        
        # Commit all changes
        db.session.commit()
        
        # Update ranks
        entries = WeeklyLeaderboard.query.filter_by(
            week_number=current_week,
            year=current_year
        ).order_by(WeeklyLeaderboard.total_points.desc()).all()
        
        current_rank = 1
        current_points = None
        
        for i, entry in enumerate(entries):
            if current_points != entry.total_points:
                current_rank = i + 1
                current_points = entry.total_points
            entry.rank = current_rank
        
        db.session.commit()

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    
    # Schedule the job to run every Sunday at midnight
    trigger = CronTrigger(
        day_of_week='sun',
        hour=0,
        minute=0
    )
    
    scheduler.add_job(
        generate_weekly_leaderboard,
        trigger=trigger,
        id='weekly_leaderboard',
        name='Generate Weekly Leaderboard',
        replace_existing=True
    )
    
    scheduler.start()
    return scheduler 