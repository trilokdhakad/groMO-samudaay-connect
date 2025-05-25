from app.admin import init_admin  # add this import at the top
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
import json

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO(async_mode='threading', cors_allowed_origins="*", logger=True, engineio_logger=True)
mail = Mail()

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

    # Initialize admin after everything else
    init_admin(app, db)


    return app

from app import models 