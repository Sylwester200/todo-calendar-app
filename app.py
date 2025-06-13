from flask import Flask, render_template, redirect, url_for, flash, abort, request, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import date, datetime, timedelta
import calendar
import csv
from io import StringIO
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from models import db
from models.user import User
from models.task import Task
from models.category import Category
from forms import RegistrationForm, LoginForm, TaskForm

login_manager = LoginManager()

class ImportForm(FlaskForm):
    file = FileField(
        "Plik CSV",
        validators=[
            FileRequired(),
            FileAllowed(["csv"], "Tylko pliki .csv")
        ]
    )
    submit = SubmitField("Importuj")

mail = Mail()

def send_task_reminder(user, tasks):
    msg = Message(
        subject="Przypomnienie o zadaniach na jutro",
        recipients=[user.email]
    )
    lines = ["Masz zadania do zrobienia jutro:"]
    for t in tasks:
        due = t.due_date.strftime('%Y-%m-%d') if t.due_date else "brak terminu"
        lines.append(f"- {t.title} (termin: {due})")
    msg.body = "\n".join(lines)
    mail.send(msg)

def daily_reminder(app):
    with app.app_context():
        tomorrow = date.today() + timedelta(days=1)
        for user in User.query.all():
            tasks = Task.query.filter_by(user_id=user.id, due_date=tomorrow).all()
            if tasks:
                send_task_reminder(user, tasks)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mail.init_app(app)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("index.html")          

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = RegistrationForm()
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data.lower()).first():
                flash("E-mail jest już zajęty", "warning")
            else:
                user = User(
                    username=form.username.data,
                    email=form.email.data.lower(),
                )
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit() # zapisanie danych
                flash("Konto utworzone! Możesz się teraz zalogować.", "success")
                return redirect(url_for("login"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember_me.data)
                flash("Zalogowano pomyślnie!", "success")
                return redirect(url_for("dashboard"))
            flash("Nieprawidłowy e-mail lub hasło", "danger")
        return render_template("login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Wylogowano", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        cat_id = request.args.get('category', type=int)
        q_text = request.args.get('q', type=str, default="")

        task_query = Task.query.filter_by(user_id=current_user.id)
        task_query = task_query.order_by(Task.due_date.asc().nulls_last())

        if cat_id:
            task_query = task_query.filter(Task.categories.any(id=cat_id))
        if q_text:
            task_query = task_query.filter(Task.title.ilike(f"%{q_text}%"))
        tasks = task_query.all()
        all_categories = Category.query.order_by(Category.name).all()
        return render_template(
            "dashboard.html",
            tasks=tasks,
            categories=all_categories,
            selected_category=cat_id,
            search_query=q_text,
        )
    
    @app.route("/export_tasks")
    @login_required
    def export_tasks():
        tasks = Task.query.filter_by(user_id=current_user.id).all()

        si = StringIO()
        writer = csv.writer(si)
        writer.writerow([
            "title","description","due_date",
            "priority","completed","categories"
        ])
        for t in tasks:
            cats = ";".join([c.name for c in t.categories])
            writer.writerow([
                t.title,
                t.description or "",
                t.due_date.isoformat() if t.due_date else "",
                t.priority or "",
                "1" if t.completed else "0",
                cats
            ])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=tasks.csv"
        output.headers["Content-Type"] = "text/csv; charset=utf-8"
        return output
    
    @app.route("/import_tasks", methods=["GET", "POST"])
    @login_required
    def import_tasks():
        form = ImportForm()
        if form.validate_on_submit():
            data = form.file.data.stream.read().decode("utf-8")
            reader = csv.DictReader(StringIO(data))
            for row in reader:
                task = Task(
                    title=row["title"],
                    description=row["description"] or None,
                    due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
                    priority=row["priority"] or None,
                    completed=(row["completed"] == "1"),
                    user_id=current_user.id
                )
                task.categories = []
                for name in row["categories"].split(";"):
                    name = name.strip()
                    if not name:
                        continue
                    cat = Category.query.filter_by(name=name).first()
                    if not cat:
                        cat = Category(name=name)
                        db.session.add(cat)
                        db.session.flush()
                    task.categories.append(cat)
                db.session.add(task)
            db.session.commit()
            flash("Zaimportowano zadania z CSV", "success")
            return redirect(url_for("dashboard"))
        return render_template("import.html", form=form)
    
    @app.route("/tasks/new", methods=["GET", "POST"])
    @login_required
    def new_task():
        form = TaskForm()
        if form.validate_on_submit():
            task = Task(
                title=form.title.data,
                description=form.description.data,
                due_date=form.due_date.data,
                priority=form.priority.data,
                user_id=current_user.id
            )
            task.categories = Category.query.filter(Category.id.in_(form.categories.data)).all()
            db.session.add(task)
            db.session.commit()
            flash("Zadanie dodane", "success")
            return redirect(url_for("dashboard"))
        return render_template("task_form.html", form=form, action="Nowe zadanie")


    @app.route("/tasks/<int:id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_task(id):
        task = Task.query.get_or_404(id)
        if task.user_id != current_user.id:
            abort(403)
        form = TaskForm(obj=task)
        if form.validate_on_submit():
            task.title = form.title.data
            task.description = form.description.data
            task.due_date = form.due_date.data
            task.priority = form.priority.data
            task.categories = Category.query.filter(Category.id.in_(form.categories.data)).all()
            db.session.commit()
            flash("Zadanie zaktualizowane", "success")
            return redirect(url_for("dashboard"))
        return render_template("task_form.html", form=form, action="Edytuj zadanie")


    @app.route("/tasks/<int:id>/delete", methods=["POST"])
    @login_required
    def delete_task(id):
        task = Task.query.get_or_404(id)
        if task.user_id != current_user.id:
            abort(403)
        db.session.delete(task)
        db.session.commit()
        flash("Zadanie usunięte", "info")
        return redirect(url_for("dashboard"))
    
    @app.route("/tasks/<int:id>/toggle", methods=["POST"])
    @login_required
    def toggle_task(id):
        task = Task.query.get_or_404(id)
        if task.user_id != current_user.id:
            abort(403)
        task.completed = not task.completed
        db.session.commit()
        flash(
        "Zadanie oznaczone jako ukończone" 
        if task.completed else 
        "Zadanie oznaczone jako nieukończone",
        "info"
        )
        return redirect(url_for("dashboard"))
    
    @app.route("/calendar")
    @login_required
    def calendar_view():
        today = date.today()
        year  = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(year, month)

        tasks = Task.query.filter_by(user_id=current_user.id).all()
        tasks_by_day = {}
        for t in tasks:
            if t.due_date and t.due_date.year == year and t.due_date.month == month:
                tasks_by_day.setdefault(t.due_date.day, []).append(t)

        return render_template(
            "calendar.html",
            year=year,
            month=month,
            weeks=weeks,
            tasks_by_day=tasks_by_day,
        )

    return app

if __name__ == '__main__':
    app = create_app()
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: daily_reminder(app), 'cron', hour=8, minute=0)
    scheduler.start()
    app.run(debug=True)
