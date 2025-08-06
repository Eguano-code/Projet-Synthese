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
        # 🔁 Ajoute ici la logique pour enregistrer le compte...

        # 🔐 Exemple d’identifiant : l’email (ou une valeur retournée depuis MySQL)
        identifiant = email

        return render_template('confirmation.html', identifiant=identifiant)

    return render_template('register.html')

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

# ✅ Mot de pass oublié

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        cursor.execute("SELECT * FROM organisateurs WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user:
            return redirect(url_for('reset_password', email=email))
        else:
            return "Email non trouvé."
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email') or request.form.get('email')
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return "Les mots de passe ne correspondent pas."

        cursor.execute("UPDATE organisateurs SET mot_de_passe=%s WHERE email=%s", (new_password, email))
        conn.commit()
        return redirect(url_for('login'))

    return render_template('reset_password.html', email=email)

# ✅ Création d'événement
@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        # Tu récupères les données ici
        code = request.form['code']
        titre = request.form['titre']
        photo = request.files['photo']
        nb_places = request.form['nb_places']
        debut = request.form['debut']
        fin = request.form['fin']
        lien = request.form['lien']
        statut = request.form['statut']
        description = request.form['description']

        # Logique d'enregistrement à la BDD ou en local
        # ➕ à implémenter : stockage image, insertion SQL

        return render_template('create_event.html', success=True)

    return render_template('create_event.html', success=False)

@app.route('/participant/tickets')
def participant_tickets():
    return render_template('participant_tickets.html')

@app.route('/participant/invoices')
def participant_invoices():
    return render_template('participant_invoices.html')

@app.route('/participant/events')
def participant_events():
    return render_template('participant_events.html')

# Page pour entrer le code de l'événement à gérer
@app.route('/gestion_event', methods=['GET', 'POST'])
def gestion_event():
    if request.method == 'POST':
        code = request.form['event_code']
        action = request.form['action']

        if action == 'modifier':
            return redirect(url_for('modifier_event', code=code))
        elif action == 'valider':
            return "Événement validé avec succès !"

    return render_template('event_management.html')

# Page pour modifier les détails d’un événement
@app.route('/modifier_event/<code>', methods=['GET', 'POST'])
def modifier_event(code):
    if request.method == 'POST':
        # Récupération des champs du formulaire
        titre = request.form['titre']
        date = request.form['date']
        nb_places = request.form['nb_places']
        lieu = request.form['lieu']
        statut = request.form['statut']
        description = request.form['description']
        action = request.form['action']

        if action == 'modifier':
            # Mettre à jour l'événement dans la BDD
            # Exemple : db.update_event(code, ...)
            return "Événement modifié avec succès !"

        elif action == 'supprimer':
            # Supprimer l'événement de la BDD
            # Exemple : db.delete_event(code)
            return "Événement supprimé avec succès !"

        elif action == 'valider':
            return "Action validée pour l'événement."

    # GET : afficher les infos actuelles
    return render_template('modifier_event.html', code=code)

@app.context_processor
def inject_navigation_links():
    return dict(gestion_event_link=url_for('gestion_event'))




# =========================
# Lancement de l'application
# =========================
if __name__ == '__main__':
    import os
    print("[DEBUG] Contenu du dossier static :", os.listdir('static'))
    app.run(debug=True)
