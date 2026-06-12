import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from datetime import date
from database import get_db, init_db
from config import MENTIONS, TARIFS, DUREE_REFERENCE
from utils import generer_reference, format_prix
import weasyprint
import io

app = Flask(__name__)
app.secret_key = "changez-moi-en-production"

init_db()

@app.route('/')
def index():
    conn = get_db()
    factures = conn.execute("""
        SELECT id, reference, date_emission, statut, client_nom
        FROM factures
        ORDER BY date_emission DESC, id DESC
    """).fetchall()
    conn.close()
    return render_template("index.html", factures=factures)

@app.route('/facture/nouveau', methods=['GET', 'POST'])
def nouvelle_facture():
    if request.method == 'POST':
        # Récupération des données du formulaire
        client_nom = request.form['client_nom']
        client_adresse = request.form.get('client_adresse', '')
        client_type_tarif = request.form['client_type_tarif']
        quantite = float(request.form['quantite'])
        statut = request.form['statut']
        note = request.form.get('note', '')

        # Prix unitaire selon le type de client
        prix = TARIFS.get(client_type_tarif, 70.0)
        total_ligne = round(prix * quantite, 2)

        # Génération de la référence unique
        reference = generer_reference()
        conn = get_db()
        exist = conn.execute("SELECT id FROM factures WHERE reference=?", (reference,)).fetchone()
        while exist:
            reference = generer_reference()
            exist = conn.execute("SELECT id FROM factures WHERE reference=?", (reference,)).fetchone()

        date_emission = date.today().isoformat()

        cur = conn.execute(
            "INSERT INTO factures (reference, date_emission, client_nom, client_adresse, client_type_tarif, statut, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (reference, date_emission, client_nom, client_adresse, client_type_tarif, statut, note)
        )
        facture_id = cur.lastrowid

        service = f"Consultation de psychologie ({client_type_tarif}) - {DUREE_REFERENCE}"
        conn.execute(
            "INSERT INTO lignes (facture_id, service, quantite, prix_unitaire, total_ligne) VALUES (?, ?, ?, ?, ?)",
            (facture_id, service, quantite, prix, total_ligne)
        )
        conn.commit()
        conn.close()

        # Redirection directe vers le PDF (téléchargement automatique)
        return redirect(url_for('telecharger_pdf', id=facture_id))

    # GET -> affichage du formulaire
    return render_template("facture_form.html", tarifs=TARIFS, duree=DUREE_REFERENCE)

@app.route('/facture/<int:id>/pdf')
def telecharger_pdf(id):
    conn = get_db()
    facture = conn.execute("SELECT * FROM factures WHERE id = ?", (id,)).fetchone()
    if not facture:
        conn.close()
        return "Facture introuvable", 404

    lignes = conn.execute("SELECT * FROM lignes WHERE facture_id = ?", (id,)).fetchall()
    conn.close()

    total = sum(l['total_ligne'] for l in lignes)

    html = render_template("facture_template.html",
                           facture=facture,
                           lignes=lignes,
                           total=total,
                           mentions=MENTIONS,
                           format_prix=format_prix,
                           logo_path=os.path.join(app.static_folder, MENTIONS.get('logo',
                               'Logo PSYH Celine Bourbon psychologue Bordeaux - Psychologie Humaniste.png')))
    pdf = weasyprint.HTML(string=html).write_pdf()
    return send_file(
        io.BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"facture_{facture['reference']}.pdf"
    )

@app.route('/facture/<int:id>/supprimer', methods=['POST'])
def supprimer_facture(id):
    conn = get_db()
    conn.execute("DELETE FROM lignes WHERE facture_id=?", (id,))
    conn.execute("DELETE FROM factures WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Facture supprimée.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
