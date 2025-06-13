from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from models import db

class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    tasks = db.relationship("Task", backref="user", lazy=True) # relacja jeden do wielu; lazy=True - pobiera zadania natychmiast, dołączając je do użytkownika

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def __repr__(self):
        return f"<User {self.username}>"
