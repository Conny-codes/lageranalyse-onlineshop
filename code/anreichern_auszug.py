"""AUSZUG aus lageranalyse/anreichern.py – Produktdaten von Herstellerseiten holen.

Gezeigt: die Quellen-Konfiguration (drei von elf), die Bestätigung über die Bestellnummer,
die Unterscheidung „gibt es nicht“ / „gesperrt“ und die Entscheidung, was neu abgefragt wird.
Nicht gezeigt: die Browser-Steuerung (Playwright + Edge) und das Auslesen der Seiten.
"""
import re

from .einlesen import normiere  # entfernt Leerzeichen, Bindestriche, Punkte, Schrägstriche; Großbuchstaben

QUELLEN = {
    "phoenix": {"url": "https://www.phoenixcontact.com/de-de/suche?q={nr}", "suffix": r"\s*\|\s*Phoenix Contact$",
                # Leitet die Suche nicht direkt weiter, steht man auf der Trefferliste -> passenden Treffer öffnen
                "trefferliste": r"/suche", "treffer_link": "a[href*='/produkte/']"},
    # Eaton: Titel nennt nur die Serie, die Typbezeichnung steht in der 2. Zeile der Überschrift (z. B. "DILM40")
    "eaton": {"url": "https://www.eaton.com/de/de-de/skuPage.{nr}.html", "suffix": r"\s*\|\s*Eaton$",
              "typ_aus_h1": True, "version": 2},
    # Lapp: Seite gehört zur Serie, die Variante steht im Text ("Artikelname: H07V-K 1X25 BK")
    "lapp": {"url": "https://www.lapp.com/de/de/p/{nr}", "suffix": r"\s*\|\s*LAPP Online Shop$", "version": 2,
             "text_name": r"Artikelname:\s*\n+\s*([^\n]+?)\s*\n", "text_variante": r"\n([^\n]{10,300})\n\s*\nArtikelname:"},
    # … acht weitere Quellen, u. a. Siemens, WAGO, Rittal, ABB, Lovato und eine Großhändler-Suche
}

# Nur eindeutige Fehlerseiten-Titel (nicht "Fehler" allein: "Fehlerstrom-Schutzschalter"!)
NICHT_GEFUNDEN = re.compile(r"seite nicht gefunden|page not found|^404\b|^fehler\s*\|", re.I)
# Sperrseiten (zu viele Anfragen): später erneut versuchen, nie als "gibt es nicht" werten
BLOCKIERT = re.compile(r"access denied|zugriff verweigert|too many requests|captcha|just a moment", re.I)


def nummer_bestaetigt(nr, text):
    """True, wenn nr als eigenständiges Wort im Text vorkommt.

    Trennzeichen innerhalb der Nummer werden ignoriert ("5ST3770-0" == "5ST37700"),
    aber "24680" passt NICHT auf "246801".
    """
    if " " in nr.strip():  # mehrteilige Nummern wie "2056 30 FT"
        teile = [re.escape(t) for t in nr.split()]
        return re.search(r"(?<![\w])" + r"[\s\-]*".join(teile) + r"(?![\w])", text, re.I) is not None
    ziel = normiere(nr)
    return any(normiere(t) == ziel for t in re.split(r"[\s,;:()\[\]\"'|<>]+", text) if t)


MAX_VERSUCHE = 3
MAX_SPERREN = 3  # so viele Sperrseiten in Folge, dann wird die Quelle für den Rest des Laufs übersprungen


def _offen(eintrag, quelle=None):
    """Noch abzufragen: nie abgefragt, mit älterer Quellenversion abgefragt,
    oder nicht gefunden ohne eindeutige 404 (z. B. Seite blockiert).

    quelle: Quelle des Artikels – ältere Cache-Einträge haben das Feld "quelle" noch nicht.
    """
    if eintrag is None:
        return True
    quelle = eintrag.get("quelle") or quelle
    if not eintrag.get("nicht_gefunden") and eintrag.get("version", 1) < QUELLEN.get(quelle, {}).get("version", 1):
        return True  # Quelle wurde verbessert -> neu abfragen
    return bool(eintrag.get("nicht_gefunden") and not eintrag.get("endgueltig")
                and eintrag.get("versuche", 1) < MAX_VERSUCHE)
