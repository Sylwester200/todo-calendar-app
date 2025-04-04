from datetime import datetime
from app import db

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, default=None)
    priority = db.Column(db.String(10), nullable=True)  # high, medium, low
    completed = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now()) # lambda aby wywoływać datetime gdy tworzy sie nowy rekord

    def __repr__(self):
        return f"<Task {self.title}>"
