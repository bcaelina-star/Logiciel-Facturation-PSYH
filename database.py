import sqlite3
from config import DATABASE

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS factures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE NOT NULL,
            date_emission TEXT NOT NULL,
            client_nom TEXT NOT NULL,
            client_adresse TEXT,
            client_type_tarif TEXT CHECK(client_type_tarif IN ('adulte','etudiant')) NOT NULL,
            statut TEXT CHECK(statut IN ('Payée','En attente','Annulée')) DEFAULT 'En attente',
            note TEXT
        );
        CREATE TABLE IF NOT EXISTS lignes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facture_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            quantite REAL NOT NULL DEFAULT 1,
            prix_unitaire REAL NOT NULL,
            total_ligne REAL NOT NULL,
            FOREIGN KEY(facture_id) REFERENCES factures(id)
        );
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de données initialisée.")
