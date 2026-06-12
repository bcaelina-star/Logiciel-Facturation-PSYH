import random
import string
from datetime import date

def generer_reference(date_emission=None):
    if date_emission is None:
        d = date.today()
    else:
        d = date_emission
    partie_date = d.strftime("%d%m%Y")  # JJMMAAAA
    lettre = random.choice(string.ascii_uppercase)
    return f"{partie_date}{lettre}"

def format_prix(montant):
    return f"{montant:,.2f} €".replace(",", " ").replace(".", ",")
