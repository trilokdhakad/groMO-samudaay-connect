"""
Chat room intent analysis package
"""
from app.admin import init_admin  # add this import at the top
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
import json
import os
import threading
from datetime import datetime, UTC

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO(async_mode='threading', cors_allowed_origins="*", logger=True, engineio_logger=True)
mail = Mail()

def start_intent_updater():
    """Start the sales intent updater in a background thread"""
    from app.sales_analysis import sales_analyzer
    import time
    import sqlite3
    from datetime import timedelta
    
    def update_intents():
        try:
            # Connect to the database
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # Get messages from the last 5 minutes
            cutoff_time = (datetime.now(UTC) - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT id, content
                FROM message
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff_time,))
            
            messages = cursor.fetchall()

            # Update intents
            for msg_id, content in messages:
                intent = sales_analyzer.analyze(content)
                cursor.execute("""
                    UPDATE message
                    SET sales_intent = ?
                    WHERE id = ?
                """, (intent, msg_id))

            # Commit changes
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error updating intents: {e}")
    
    def run_updater():
        while True:
            update_intents()
            time.sleep(120)  # Wait for 2 minutes
    
    # Start the updater in a daemon thread
    updater_thread = threading.Thread(target=run_updater, daemon=True)
    updater_thread.start()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    socketio.init_app(app, async_mode='threading', cors_allowed_origins="*", logger=True, engineio_logger=True)
    mail.init_app(app)

    # Register custom Jinja2 filters
    app.jinja_env.filters['from_json'] = lambda x: json.loads(x) if x else []

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.chat import bp as chat_bp
    app.register_blueprint(chat_bp)

    # Import GP blueprint
    from app.gp import bp as gp_bp
    app.register_blueprint(gp_bp, url_prefix='/gp')

    # Create upload folder for task submissions
    UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Initialize admin after everything else
    init_admin(app, db)

    # Initialize scheduler
    from app.scheduler import init_scheduler
    scheduler = init_scheduler(app)

    # Import socket event handlers
    with app.app_context():
        from app import events

    # Start the intent updater when the app starts
    start_intent_updater()

    return app

from app import models 