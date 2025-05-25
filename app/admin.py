from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, request
from flask_login import current_user

admin = Admin(name='GroMo Admin', template_mode='bootstrap4')

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))

def init_admin(app, db):
    # ❗ Delay model import to avoid circular import
    from app.models import User, UserProfile, Room, RoomTopic, RoomMembership, Message, UserInterest

    admin.init_app(app)
    admin.add_view(SecureModelView(User, db.session))
    admin.add_view(SecureModelView(UserProfile, db.session))
    admin.add_view(SecureModelView(UserInterest, db.session))
    admin.add_view(SecureModelView(Room, db.session))
    admin.add_view(SecureModelView(RoomTopic, db.session))
    admin.add_view(SecureModelView(RoomMembership, db.session))
    admin.add_view(SecureModelView(Message, db.session))
