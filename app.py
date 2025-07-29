from flask import Flask, render_template, request, redirect, url_for, session
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

@app.route('/recommender', methods=['GET', 'POST'])
def recommender():
    if request.method == 'POST':
        nom = request.form.get('nom')
        email = request.form.get('email')
        preferences = request.form.get('preferences')
        # Ici, tu peux traiter les données (par ex. : enregistrer, appeler IA, etc.)
        return render_template('recommendation.html', confirmation=True)
    return render_template('recommendation.html', confirmation=False)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    return render_template('event_detail.html', event_id=event_id)

@app.route('/payment')
def payment():
    return render_template('payment.html')

# ✅ Route : Création de compte organisateur
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
        return redirect(url_for('login'))

    return render_template('register.html')

# ✅ Route : Création de compte participant
@app.route('/register_participant', methods=['GET', 'POST'])
def register_participant():
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        # À implémenter : enregistrement du participant
        return redirect(url_for('login'))

    return render_template('register_participant.html')

# ✅ Route : Connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']

        user = Organisateur.query.filter_by(email=email, mot_de_passe=mot_de_passe).first()
        if user:
            session['user'] = user.nom
            return redirect(url_for('dashboard'))
        else:
            return "Identifiants invalides. Réessayez."

    return render_template('login.html')

# ✅ Route : Déconnexion
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ✅ Tableau de bord personnel
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', nom=session['user'])

@app.route('/event_list')
def event_list():
    return render_template('event_list.html')

    if request.method == 'POST':
        titre = request.form['titre']
        date = request.form['date']
        description = request.form['description']
        # Tu peux ici enregistrer l’événement dans la base de données plus tard
        return redirect(url_for('dashboard'))

    return render_template('create_event.html')


# =========================
# Lancement de l'application
# =========================
if __name__ == '__main__':
    import os
    print("[DEBUG] Contenu du dossier static :", os.listdir('static'))
    app.run(debug=True)
