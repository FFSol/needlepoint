from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

# Assuming Flask app is already created
login_manager = LoginManager()
login_manager.init_app(app)

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
