from app import app, db
from models import Organisateur, Evenement

with app.app_context():
    db.create_all()
    print("Base de données créée.")
