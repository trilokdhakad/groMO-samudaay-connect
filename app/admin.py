from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, request
from flask_login import current_user

admin = Admin(name='Samudaay Connect Admin', template_mode='bootstrap4')

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated  # Temporarily removed is_admin check

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))

class UserModelView(SecureModelView):
    column_list = ['id', 'username', 'email', 'points', 'rating', 'total_ratings']
    form_columns = ['username', 'email', 'points', 'rating', 'total_ratings']
    column_searchable_list = ['username', 'email']
    column_filters = ['points', 'rating', 'total_ratings']
    form_widget_args = {
        'password_hash': {'disabled': True}
    }

def init_admin(app, db):
    # ❗ Delay model import to avoid circular import
    from app.models import User, UserProfile, Room, RoomTopic, RoomMembership, Message, UserInterest

    admin.init_app(app)
    admin.add_view(UserModelView(User, db.session))
    admin.add_view(SecureModelView(UserProfile, db.session))
    admin.add_view(SecureModelView(UserInterest, db.session))
    admin.add_view(SecureModelView(Room, db.session))
    admin.add_view(SecureModelView(RoomTopic, db.session))
    admin.add_view(SecureModelView(RoomMembership, db.session))
    admin.add_view(SecureModelView(Message, db.session))
