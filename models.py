from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Organisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    mot_de_passe = db.Column(db.String(100))

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    mot_de_passe = db.Column(db.String(100))

class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.String(50))

class Inscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'))

    participant = db.relationship('Participant', backref='inscriptions')
    evenement = db.relationship('Evenement', backref='inscriptions')
