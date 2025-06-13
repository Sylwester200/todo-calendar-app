from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from models.category import Category

def get_category_choices(): # pobieranie aktualnych kategorii z bazy
    return [(c.id, c.name) for c in Category.query.order_by(Category.name).all()] # all zwraca listę wyników

class RegistrationForm(FlaskForm):
    username = StringField("Nazwa użytkownika", validators=[DataRequired(), Length(3, 64)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Hasło", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField("Powtórz hasło", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Zarejestruj się")

class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Hasło", validators=[DataRequired()])
    remember_me = BooleanField("Zapamiętaj mnie")
    submit = SubmitField("Zaloguj się")

class TaskForm(FlaskForm):
    title = StringField("Tytuł", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Opis", validators=[Optional(), Length(max=500)])
    due_date = DateField("Termin", validators=[Optional()])
    priority = SelectField(
        "Priorytet",
        choices=[("Wysoki","Wysoki"),("Średni","Średni"),("Niski","Niski")],
        validators=[Optional()],
    )
    categories = SelectMultipleField("Kategorie", coerce=int, choices=[], validators=[Optional()],)
    submit = SubmitField("Zapisz zadanie")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories.choices = get_category_choices()
