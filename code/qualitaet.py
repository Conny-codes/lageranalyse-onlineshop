"""Qualitätssicherung: Alarm bei Quellenausfall und Stichproben gegen die Herstellerseite."""
import json
import random
from datetime import date
from pathlib import Path

MIN_ABFRAGEN = 5        # erst ab so vielen Abfragen in einem Lauf wird eine Quelle bewertet
MIN_HISTORIE = 20       # so viele Abfragen braucht die Vergleichsbasis
EINBRUCH = 0.30         # Alarm, wenn die Trefferquote um mehr als 30 Prozentpunkte fällt …
MINDESTQUOTE = 0.30     # … oder unter 30 % liegt


def _laden(pfad, standard):
    pfad = Path(pfad)
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else standard


def _speichern(pfad, daten):
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- Quellen-Überwachung

def quellen_pruefen(lauf, pfad, stichtag):
    """lauf: {quelle: {"abgefragt", "gefunden", "blockiert"}} aus diesem Anreicherungslauf.

    Vergleicht mit der bisherigen Trefferquote, speichert den Lauf und gibt Warnungen zurück.
    """
    historie = _laden(pfad, {})
    warnungen = []
    for quelle, s in lauf.items():
        h = historie.setdefault(quelle, {"abgefragt": 0, "gefunden": 0, "laeufe": []})
        if s["abgefragt"] >= MIN_ABFRAGEN:
            quote = s["gefunden"] / s["abgefragt"]
            basis = h["gefunden"] / h["abgefragt"] if h["abgefragt"] >= MIN_HISTORIE else None
            if quote < MINDESTQUOTE or (basis is not None and quote < basis - EINBRUCH):
                vergleich = f", bisher {basis:.0%}" if basis is not None else ""
                warnungen.append(f"Quelle '{quelle}': nur {quote:.0%} Treffer ({s['gefunden']}/{s['abgefragt']}{vergleich}) "
                                 f"– Webseite geändert oder gesperrt? Abfrage prüfen.")
        if s.get("blockiert", 0) >= 3:
            warnungen.append(f"Quelle '{quelle}': {s['blockiert']}× gesperrt (zu viele Anfragen) – "
                             f"betroffene Artikel werden später erneut versucht.")
        h["abgefragt"] += s["abgefragt"]
        h["gefunden"] += s["gefunden"]
        h["laeufe"].append({"datum": stichtag, **s})
        h["laeufe"] = h["laeufe"][-30:]
    _speichern(pfad, historie)
    return warnungen


def quellen_uebersicht(artikel, cache):
    """Trefferquote je Quelle über den aktuellen Cache – für das Dashboard."""
    zaehler = {}
    for a in artikel:
        if not a.get("quelle"):
            continue
        e = cache.get(a)
        z = zaehler.setdefault(a["quelle"], {"quelle": a["quelle"], "artikel": 0, "abgefragt": 0, "gefunden": 0})
        z["artikel"] += 1
        if e:
            z["abgefragt"] += 1
            z["gefunden"] += not e.get("nicht_gefunden")
    for z in zaehler.values():
        z["quote"] = round(z["gefunden"] / z["abgefragt"] * 100) if z["abgefragt"] else None
        z["quote_text"] = f"{z['quote']} %" if z["quote"] is not None else "–"
    return sorted(zaehler.values(), key=lambda z: -z["artikel"])


# ---------------------------------------------------------------- Stichproben

def stichprobe_ziehen(artikel, anzahl, pfad, seed=None):
    """Zieht zufällig 'sichere' Artikel mit Quelle, die gegen die Herstellerseite geprüft werden sollen."""
    kandidaten = [a for a in artikel if a["status"] == "sicher" and a["produkt"].get("quelle_url")]
    auswahl = random.Random(seed).sample(kandidaten, min(anzahl, len(kandidaten)))
    liste = [{"artikelnummer": a["artikelnummer"], "bestellnummer": a["bestellnummer"], "hersteller": a["hersteller"],
              "name": a["produkt"]["name"], "beschreibung": a["produkt"]["beschreibung"][:300],
              "bild_url": a["produkt"]["bild_url"], "quelle_url": a["produkt"]["quelle_url"],
              "ergebnis": None, "notiz": ""} for a in auswahl]
    _speichern(pfad, liste)
    return liste


def stichprobe_auswerten(datei, historie_pfad, gesperrt_pfad):
    """Liest geprüfte Stichprobe (ergebnis: "ok" | "fehler"), führt Historie, sperrt fehlerhafte Artikel."""
    liste = json.loads(Path(datei).read_text(encoding="utf-8"))
    geprueft = [x for x in liste if x.get("ergebnis") in ("ok", "fehler")]
    fehler = [x for x in geprueft if x["ergebnis"] == "fehler"]
    historie = _laden(historie_pfad, [])
    historie.append({"datum": date.today().isoformat(), "geprueft": len(geprueft), "fehler": len(fehler),
                     "fehlerhafte": [{"artikelnummer": x["artikelnummer"], "notiz": x.get("notiz", "")} for x in fehler]})
    _speichern(historie_pfad, historie)
    gesperrt = _laden(gesperrt_pfad, {})
    for x in fehler:
        gesperrt[x["artikelnummer"]] = f"Stichprobe {date.today().isoformat()}: {x.get('notiz') or 'Daten passen nicht'}"
    _speichern(gesperrt_pfad, gesperrt)
    return len(geprueft), len(fehler)


def stichprobe_kennzahl(historie_pfad, letzte=4):
    """Fehlerquote über die letzten Stichproben."""
    historie = _laden(historie_pfad, [])[-letzte:]
    geprueft = sum(h["geprueft"] for h in historie)
    if not geprueft:
        return None
    fehler = sum(h["fehler"] for h in historie)
    return {"geprueft": geprueft, "fehler": fehler, "quote": round(fehler / geprueft * 100, 1),
            "letzte": historie[-1]["datum"], "anzahl_proben": len(historie)}
