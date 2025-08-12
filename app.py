from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from models import db, Organisateur
from datetime import datetime, timedelta
from flask import flash  # tu peux déjà l’avoir importé
from uuid import uuid4
from io import BytesIO
from flask import send_file
from collections import Counter
import io, base64
import qrcode
import re
# Petit “cache” en mémoire pour les événements
EVENTS = {}  # EVENTS[code] = {...}
# Petit stockage en mémoire pour les billets créés (démo)
TICKETS = {}
COMMENTS = []  # optionnel: liste de commentaires [{"event":"...", "auteur":"...", "texte"

TICKETS = getattr(globals(), "TICKETS", {})

def make_qr_base64(text: str) -> str:
    """Retourne une data-URI PNG base64 pour un QR code du texte donné."""
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64}"

def create_ticket_for_event(event, owner_name=""):
    """Crée un billet pour l'événement donné (dict) et le stocke dans TICKETS."""
    ticket_id = str(uuid.uuid4())[:8].upper()
    ticket = {
        "id": ticket_id,
        "code": event["code"],
        "titre": event["titre"],
        "debut": event["debut"],
        "fin": event["fin"],
        "lien": event.get("lien") or "",
        "statut": "Valide",
        "tarif_type": event.get("tarif_type", "gratuit"),
        "tarif_montant": event.get("tarif_montant", "0"),
        "owner": owner_name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    TICKETS[ticket_id] = ticket
    return ticket

   
  

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
    suggestions = []
    confirmation = False
    prefs_text = ""

    if request.method == 'POST':
        confirmation = True
        prefs_text = request.form.get('preferences', '')
        # Ici on pourrait aussi utiliser nom/email si tu veux
        suggestions = recommend_events(prefs_text)

    # on envoie les suggestions (liste [(event, score), ...]) au template
    return render_template(
        'recommendation.html',
        confirmation=confirmation,
        prefs_text=prefs_text,
        suggestions=suggestions,

        
    )




@app.route('/event/<int:event_id>')
def event_detail(event_id):
    return render_template('event_detail.html', event_id=event_id)

# Formulaire public (participants)
@app.route('/commentaires', methods=['GET', 'POST'])
def comments_form():
    if request.method == 'POST':
        data = {
            "event": (request.form.get('event_code') or "").strip(),
            "satisfaction": int(request.form.get('satisfaction') or 0),
            "q1": request.form.get('q1', '').strip(),
            "q2": request.form.get('q2', '').strip(),  # Oui / Non
            "q3": request.form.get('q3', '').strip(),
            "q4": request.form.get('q4', '').strip(),
            "auteur": session.get('user') or "Anonyme",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        COMMENTS.append(data)
        flash("Merci pour votre commentaire !", "success")
        return redirect(url_for('comments_form'))
    return render_template('comments_form.html')


# Liste des commentaires (organisateur uniquement)
@app.route('/organisateur/commentaires')
def comments_admin():
    if 'user' not in session or session.get('user_type') != 'Organisateur':
        # si tu veux, redirige vers login ou dashboard avec un message
        flash("Accès réservé aux organisateurs.", "info")
        return redirect(url_for('dashboard'))
    return render_template('comments_admin.html', comments=COMMENTS)

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
    
    user_type = session.get('user_type', 'Participant')

   
# ✅ Recommendation intelligent 


def _tokenize(text: str):
    """Renvoie des mots en minuscules sans ponctuation (très simple)."""
    if not text:
        return []
    return re.findall(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9]+", text.lower())

def recommend_events(preferences: str, k: int = 5):
    """
    Score les événements existants (EVENTS) en fonction des mots-clés saisis.
    Retourne une liste triée de tuples (event_dict, score).
    """
    prefs = _tokenize(preferences)
    if not prefs:
        return []

    scores = []
    for ev in EVENTS.values():
        haystack = " ".join([
            ev.get("titre",""),
            ev.get("description",""),
            ev.get("tags",""),   
            ev.get("lien",""),
            str(ev.get("statut","")),
        ])
        words = _tokenize(haystack)
        # simple score = nb de mots prefs trouvés
        score = sum(1 for w in words if w in prefs)
        # petit bonus si l’événement est "Disponible"
        if ev.get("statut") == "Disponible":
            score += 0.25
        if score > 0:
            scores.append((ev, score))

    scores.sort(key=lambda t: t[1], reverse=True)
    return scores[:k]


# --- Mise à jour du profil organisateur ---
@app.route('/organizer/profile', methods=['POST'])
def organizer_profile_update():
    if 'user' not in session or session.get('user_type') != 'Organisateur':
        return redirect(url_for('login'))

    org_id = session.get('organizer_id')
    organizer = Organisateur.query.get(org_id)
    if not organizer:
        flash("Organisateur introuvable.", "danger")
        return redirect(url_for('dashboard'))

    # Champs du formulaire
    new_name  = request.form.get('nom', '').strip()
    new_email = request.form.get('email', '').strip()
    new_pwd   = request.form.get('mot_de_passe', '').strip()

    if new_name:  organizer.nom = new_name
    if new_email: organizer.email = new_email
    if new_pwd:   organizer.mot_de_passe = new_pwd   # (hash à prévoir en prod)

    db.session.commit()

    # Mettre la session à jour pour refléter les changements visibles dans la navbar
    if new_name:  session['user']  = new_name
    if new_email: session['email'] = new_email

    flash("Profil mis à jour avec succès.", "success")
    return redirect(url_for('dashboard'))

# --- Suppression du compte organisateur ---
@app.route('/organizer/delete', methods=['POST'])
def organizer_delete():
    if 'user' not in session or session.get('user_type') != 'Organisateur':
        return redirect(url_for('login'))

    org_id = session.get('organizer_id')
    organizer = Organisateur.query.get(org_id)
    if not organizer:
        flash("Organisateur introuvable.", "danger")
        return redirect(url_for('dashboard'))

    # (option) Vérifier un champ caché "confirm" == "OUI"
    if request.form.get('confirm') != 'OUI':
        flash("Suppression annulée.", "info")
        return redirect(url_for('dashboard'))

    db.session.delete(organizer)
    db.session.commit()
    session.clear()
    flash("Compte supprimé. Désolé de vous voir partir.", "success")
    return redirect(url_for('home'))


    if user_type == 'Organisateur':
        # Stats participants par événement
        counts = Counter(t['code'] for t in TICKETS.values())
        labels = []
        participants = []
        revenue = []

        for code, ev in EVENTS.items():
            labels.append(ev.get('titre', code))
            nb = counts.get(code, 0)
            participants.append(nb)
            price = float(ev.get('tarif_montant', 0) or 0)
            revenue.append(round(nb * price, 2))

        latest_comments = COMMENTS[-8:]  # derniers commentaires
        return render_template(
            'dashboard_organizer.html',
            labels=labels,
            participants=participants,
            revenue=revenue,
            comments=latest_comments
        )

    # === Participant ===
    user = session['user']
    my_tickets = [t for t in TICKETS.values() if t.get('owner') == user]

    # Historique transactions (tickets payants uniquement)
    transactions = []
    for t in my_tickets:
        ev = EVENTS.get(t['code'], {})
        amount = float(ev.get('tarif_montant', 0) or 0)
        if amount > 0:
            transactions.append({
                "ticket_id": t['id'],
                "event": ev.get('titre', t['code']),
                "amount": amount,
                "date": t.get('created_at', '')
            })

    # Exemple d'infos profil (à remplacer par tes vraies données)
    profile = {
        "nom": session.get('user', ''),
        "email": session.get('email', 'non.defini@example.com'),
    }

    return render_template(
        'dashboard_participant.html',
        profile=profile,
        tickets=my_tickets,
        transactions=transactions
    )
    # (optionnel) Mise à jour du profil participant (démo)
@app.route('/participant/profile', methods=['POST'])
def participant_profile_update():
    if 'user' not in session:
        return redirect(url_for('login'))
    # Ici tu mettrais l'UPDATE DB; pour la démo on met à jour dans la session
    session['user'] = request.form.get('nom', session['user'])
    session['email'] = request.form.get('email', session.get('email', ''))
    return redirect(url_for('dashboard'))

# Désactivation du compte (démo : clear session)
@app.route('/participant/deactivate', methods=['POST'])
def participant_deactivate():
    if 'user' not in session:
        return redirect(url_for('login'))
    session.clear()
    return render_template('confirmation.html')  # ou redirige vers home avec message

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
        code = request.form['code']
        titre = request.form['titre']
        photo = request.files.get('photo')  # (tu gèreras l’upload plus tard)
        nb_places = request.form['nb_places']
        debut = request.form['debut']
        fin = request.form['fin']
        lien = request.form.get('lien')
        statut = request.form['statut']
        tags = request.form.get('tags', '')
        description = request.form.get('description', '')
        EVENTS[code] = {
    "code": code,
    "titre": titre,
    "nb_places": nb_places,
    "debut": debut,          # format ISO “YYYY-MM-DD” ou “YYYY-MM-DDTHH:MM”
    "fin": fin,
    "lien": lien,
    "statut": statut,
    "description": description,
    "tags": tags,
    
        # champs tarif que tu as ajoutés
    "tarif_type": request.form.get("tarif_type", "gratuit"),  # 'gratuit' | 'payant'
    "tarif_montant": request.form.get("tarif_montant", "0") or "0",

    }
        # Nouveaux champs tarif
        tarif_type = request.form.get('tarif_type')     # 'gratuit' | 'payant'
        tarif_montant = request.form.get('tarif_montant') or None
    
        # TODO: enregistrer l’événement en BDD ici si besoin…

        # ====== Génération d’un billet (démo) ======
        ticket_id = str(uuid4())
        ticket = {
            "id": ticket_id,
            "code": code,
            "titre": titre,
            "nb_places": nb_places,
            "debut": debut,
            "fin": fin,
            "lien": lien,
            "statut": statut,
            "description": description,
            "tarif_type": tarif_type,
            "tarif_montant": tarif_montant,
            # Optionnel: propriétaire du billet (si user connecté)
            "nom_participant": session.get('user')
        }
        TICKETS[ticket_id] = ticket

        # URL de vérification encodée dans le QR
        verify_url = url_for('ticket_verify', ticket_id=ticket_id, _external=True)
        qr_data_uri = make_qr_base64(verify_url)

        # On affiche la page billet tout de suite (message + QR + détails)
        return render_template('ticket.html',
                               ticket=ticket,
                               qr_data_uri=qr_data_uri,
                               verify_url=verify_url)

    # GET: formulaire
    return render_template('create_event.html', success=False)

 # Verification de Billet

@app.route('/ticket/verify/<ticket_id>')
def ticket_verify(ticket_id):
    ticket = TICKETS.get(ticket_id)
    if not ticket:
        return "Billet introuvable ou invalide.", 404
    # Tu peux ajouter plus de logique (statut, contrôle, horodatage…)
    return f"Billet valide pour l’événement « {ticket['titre']} » (code: {ticket['code']})."

 # Reconsultation de Billet
@app.route('/ticket/<ticket_id>')
def ticket_view(ticket_id):
    ticket = TICKETS.get(ticket_id)
    if not ticket:
        return "Billet introuvable.", 404
    verify_url = url_for('ticket_verify', ticket_id=ticket_id, _external=True)
    qr_data_uri = make_qr_base64(verify_url)
    return render_template('ticket.html', ticket=ticket, qr_data_uri=qr_data_uri, verify_url=verify_url)


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

# Page pour la politique de confidentialité

@app.route('/politique-confidentialite')
def privacy():
    return render_template('privacy.html')

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

# --- Saisie du code billet ---
@app.route('/billet', methods=['GET', 'POST'])
def ticket_lookup():
    if request.method == 'POST':
        code = (request.form.get('ticket_code') or '').strip()

        # On cherche le billet par "id" (le code généré) ou autre champ si tu en crées un
        ticket = next((t for t in TICKETS.values()
                       if t['id'] == code or t.get('code_billet') == code), None)

        if not ticket:
            # message simple ; si tu utilises flash, affiche-le dans le template
            return render_template('ticket_lookup.html', error="Billet introuvable. Vérifie le code.")

        # Besoin de connexion pour voir le détail
        session['pending_ticket'] = ticket['id']
        if 'user' not in session:
            # après login on revient ici
            return redirect(url_for('login', next=url_for('ticket_view_secure')))

        return redirect(url_for('ticket_view_secure'))

    return render_template('ticket_lookup.html')


# --- Affichage sécurisé d’un billet (après login) ---
@app.route('/billet/afficher')
def ticket_view_secure():
    if 'user' not in session:
        return redirect(url_for('login', next=url_for('ticket_view_secure')))

    ticket_id = session.get('pending_ticket')  # on le garde le temps de la session
    if not ticket_id or ticket_id not in TICKETS:
        return "Billet introuvable.", 404

    ticket = TICKETS[ticket_id]

    # QR pour vérification
    verify_url = url_for('ticket_verify', ticket_id=ticket_id, _external=True)
    qr_data_uri = make_qr_base64(verify_url)

    # Règle d’annulation : ≥ 48h avant début
    can_cancel = True
    try:
        dt_debut = datetime.fromisoformat(ticket['debut'])  # 'YYYY-MM-DD' ou 'YYYY-MM-DDTHH:MM'
        can_cancel = (dt_debut - datetime.now()) >= timedelta(hours=48)
    except Exception:
        # si parsing impossible, on autorise l’annulation par défaut
        can_cancel = True

    return render_template('ticket_view.html',
                           ticket=ticket,
                           qr_data_uri=qr_data_uri,
                           verify_url=verify_url,
                           can_cancel=can_cancel)


# --- Annulation du billet ---
@app.route('/billet/annuler/<ticket_id>', methods=['POST'])
def ticket_cancel(ticket_id):
    if 'user' not in session:
        return redirect(url_for('login', next=url_for('ticket_view_secure')))

    ticket = TICKETS.get(ticket_id)
    if not ticket:
        return "Billet introuvable.", 404

    # Vérifier la règle des 48h
    try:
        dt_debut = datetime.fromisoformat(ticket['debut'])
        if dt_debut - datetime.now() < timedelta(hours=48):
            # trop tard
            return redirect(url_for('ticket_view_secure'))
    except Exception:
        pass  # si on ne peut pas parser, on laisse annuler

    ticket['statut'] = 'Annulé'
    return redirect(url_for('ticket_view_secure'))

@app.route('/a-propos')
def about():
    return render_template('about.html')

@app.route('/conditions-utilisation')
def terms():
    return render_template('terms.html')

@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}

@app.context_processor
def inject_navigation_links():
    return dict(gestion_event_link=url_for('gestion_event'))

# 1) Page de saisie du code
@app.route('/vente', methods=['GET', 'POST'])
def vente():
    # on impose la connexion
    if 'user' not in session:
        return redirect(url_for('login', next=url_for('vente')))

    # Option : restreindre aux participants si tu as session['user_type']
    if session.get('user_type') and session.get('user_type') != 'Participant':
        return render_template('sales_code.html', error="Cette section est réservée aux participants.")

    if request.method == 'POST':
        code = (request.form.get('event_code') or '').strip()
        event = EVENTS.get(code)
        if not event:
            return render_template('sales_code.html', error="Événement introuvable. Vérifie le code.")

        # Gratuit -> on crée le billet et on affiche
        is_free = (event.get('tarif_type') == 'gratuit') or (str(event.get('tarif_montant', '0')) in ('0', '0.0', ''))
        if is_free:
            ticket = create_ticket_for_event(event, owner_name=session.get('user', ''))
            session['pending_ticket'] = ticket['id']
            # message d’info affiché sur la page billet
            return redirect(url_for('ticket_view_secure'))

        # Payant -> redirige vers la page paiement
        return redirect(url_for('vente_paiement', code=code))

    return render_template('sales_code.html')


# 2) Page de paiement (simulé)
@app.route('/vente/paiement/<code>', methods=['GET', 'POST'])
def vente_paiement(code):
    if 'user' not in session:
        return redirect(url_for('login', next=url_for('vente_paiement', code=code)))
    

    event = EVENTS.get(code)
    if not event:
        return "Événement introuvable.", 404

    # si jamais l'événement est gratuit, on ne doit pas se retrouver ici
    is_free = (event.get('tarif_type') == 'gratuit') or (str(event.get('tarif_montant', '0')) in ('0', '0.0', ''))
    if is_free:
        return redirect(url_for('vente'))

    if request.method == 'POST':
        # on “valide” le paiement sans gateway réel
        card_brand = request.form.get('brand')  # visa / mc / paypal
        card_holder = request.form.get('holder')
        card_number = request.form.get('number')
        exp = request.form.get('exp')
        cvc = request.form.get('cvc')

        # (tu peux ajouter de la validation)
        ticket = create_ticket_for_event(event, owner_name=session.get('user', ''))
        session['pending_ticket'] = ticket['id']
        return redirect(url_for('ticket_view_secure'))

    return render_template('sales_payment.html', event=event)




# =========================
# Lancement de l'application
# =========================
if __name__ == '__main__':
    import os
    print("[DEBUG] Contenu du dossier static :", os.listdir('static'))
    app.run(debug=True)
