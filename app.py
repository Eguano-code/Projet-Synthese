from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from models import db, Organisateur

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evenements.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'ma_clé_secrète_pour_la_session'

db.init_app(app)

@app.route('/')
def home():
    events = [
        {"title": "Conférence IA", "date": "2025-07-20", "description": "Conférence sur l'IA"},
        {"title": "Salon Tech", "date": "2025-08-05", "description": "Technologies de demain"}
    ]
    return render_template('home.html', events=events)

@app.route('/recommender')
def recommender():
    return render_template('recommendation.html')

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    return render_template('event_detail.html', event_id=event_id)

@app.route('/payment')
def payment():
    return render_template('payment.html')

# ✅ Route pour créer un compte organisateur
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']

        existing = Organisateur.query.filter_by(email=email).first()
        if existing:
            return "Un compte avec cet email existe déjà."

        new_org = Organisateur(nom=nom, email=email, mot_de_passe=mot_de_passe)
        db.session.add(new_org)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('register.html')

# ✅ Route pour créer un compte participant
@app.route('/register_participant', methods=['GET', 'POST'])
def register_participant():
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        # Ici, tu peux ajouter la logique de création d’un compte participant
        return redirect(url_for('home'))

    return render_template('register_participant.html')

if __name__ == '__main__':
    import os
    print("[DEBUG] Contenu du dossier static :", os.listdir('static'))
    app.run(debug=True)
