"""Zwei Lagerstände vergleichen: Abgänge, Zugänge, neue/entfallene Artikel, Preisänderungen.

Wichtig: Aus zwei Ständen sieht man nur die Netto-Differenz. Wird zwischen zwei
Ständen verkauft UND nachgeliefert, gleicht sich das aus. "Abgang" ist daher eine
Untergrenze der tatsächlichen Verkäufe.
"""

BEWEGUNGEN = ("abgang", "zugang", "neu", "entfallen", "unverändert", "erster Stand")


def abgleichen(alt, neu):
    """Gibt pro Artikel eine Zeile mit Bestand alt/neu, Differenz und Bewegungsart zurück."""
    neu_idx = {a["artikelnummer"]: a for a in neu}
    if alt is None:
        return [_zeile(None, a, "erster Stand") for a in neu]

    alt_idx = {a["artikelnummer"]: a for a in alt}
    zeilen = []
    for nr, a in neu_idx.items():
        v = alt_idx.get(nr)
        if v is None:
            zeilen.append(_zeile(None, a, "neu"))
        elif a["bestand"] < v["bestand"]:
            zeilen.append(_zeile(v, a, "abgang"))
        elif a["bestand"] > v["bestand"]:
            zeilen.append(_zeile(v, a, "zugang"))
        else:
            zeilen.append(_zeile(v, a, "unverändert"))
    for nr, v in alt_idx.items():
        if nr not in neu_idx:
            zeilen.append(_zeile(v, None, "entfallen"))
    return zeilen


def _zeile(alt, neu, bewegung):
    basis = neu or alt
    b_alt = alt["bestand"] if alt else 0.0
    b_neu = neu["bestand"] if neu else 0.0
    p_alt = alt["lagerpreis"] if alt else None
    p_neu = neu["lagerpreis"] if neu else None
    preis = p_neu if p_neu else (p_alt or 0.0)
    vk = (neu or {}).get("vk") or (alt or {}).get("vk") or 0.0
    delta = b_neu - b_alt if bewegung != "erster Stand" else 0.0
    return {
        "artikelnummer": basis["artikelnummer"],
        "bestellnummer": basis["bestellnummer"],
        "hersteller": basis["hersteller"] or f"Sonstige ({basis['kuerzel']})",
        "bewegung": bewegung,
        "bestand_alt": b_alt if alt else None,
        "bestand_neu": b_neu if neu else None,
        "delta": delta,
        "lagerpreis_alt": p_alt,
        "lagerpreis_neu": p_neu,
        "preis_geaendert": bool(alt and neu and p_alt != p_neu),
        "wert_delta": round(delta * preis, 2),
        "umsatz_delta": round(delta * vk, 2),
    }


def zusammenfassung(zeilen):
    """Kennzahlen eines Abgleichs."""
    z = {b: 0 for b in BEWEGUNGEN}
    for r in zeilen:
        z[r["bewegung"]] += 1
    abg = [r for r in zeilen if r["bewegung"] == "abgang"]
    zug = [r for r in zeilen if r["bewegung"] == "zugang"]
    z["abgang_stueck"] = -sum(r["delta"] for r in abg)
    z["abgang_wert"] = -sum(r["wert_delta"] for r in abg)
    z["abgang_umsatz"] = -sum(r["umsatz_delta"] for r in abg)
    z["zugang_stueck"] = sum(r["delta"] for r in zug)
    z["zugang_wert"] = sum(r["wert_delta"] for r in zug)
    z["preisaenderungen"] = sum(1 for r in zeilen if r["preis_geaendert"])
    return z
