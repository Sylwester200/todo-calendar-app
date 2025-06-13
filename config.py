import os

basedir = os.path.abspath(os.path.dirname(__file__)) # ścieżka do folderu z projektem

class Config:
    SECRET_KEY = "klucz" 
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db") # /// - ścieżka bezwzględna do pliku na dysku
    SQLALCHEMY_TRACK_MODIFICATIONS = False # wyłączenie powiadomienia o zmianach w modelach
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = ('Todo-App', MAIL_USERNAME)
