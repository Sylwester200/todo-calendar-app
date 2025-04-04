from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy() # obiekt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    return app

if __name__ == '__main__':
    my_app = create_app()
    my_app.run(debug=True)