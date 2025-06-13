from models import db

# tabela pomocnicza wiele do wielu
task_categories = db.Table(
    'task_categories',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'),  primary_key=True)
)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    # relacja odwrotna - dwukierunkowa
    tasks = db.relationship(
        'Task',
        secondary=task_categories,
        backref=db.backref('categories', lazy='joined'),
        lazy='joined'
    )

    def __repr__(self):
        return f'<Category {self.name}>'
