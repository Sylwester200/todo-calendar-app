import os

basedir = os.path.abspath(os.path.dirname(__file__)) # ścieżka do folderu z projektem

class Config:
    SECRET_KEY = "klucz" 
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db") # /// - ścieżka bezwzględna do pliku na dysku
    SQLALCHEMY_TRACK_MODIFICATIONS = False # wyłączenie powiadomienia o zmianach w modelach