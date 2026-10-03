# Datenqualität

## Status je Artikel

| Status | Bedeutung | Typische Gründe |
|---|---|---|
| ✓ **sicher** | geht in den WooCommerce-Import | Herstellerseite gefunden, Nummer bestätigt, Bild vorhanden; oder von Mensch/KI auf der Herstellerseite bestätigt |
| ! **prüfen** | Daten da, bitte kurz ansehen | Serienbild statt Produktbild, Beschreibung beschreibt nur die Serie, Daten nur vom Großhändler, Hersteller nur vermutet, Vorschlag der KI-Recherche |
| ✕ **manuell** | Daten fehlen | Hersteller unbekannt, Bestellnummer ist Platzhalter oder Freitext, auf der Herstellerseite nicht gefunden |

Jeder Artikel trägt seine Gründe mit. Sie stehen in der Prüfliste und, zusammengefasst, im Dashboard.

## Rückfluss von Korrekturen

```
Prüfliste (Excel)                 KI-Recherche
  blaue Spalten ausfüllen           Funde mit Quelle und Notiz
  Freigabe = ja                     bestaetigt = true nur bei Nummer auf Herstellerseite
        │                                   │
        └──────────► data/korrekturen/ ◄────┘
                           │
                           ▼  nächster Lauf
                 Name/Beschreibung/Bild/Hersteller überschreiben
                 Freigabe → sicher, sonst Vorschlag → prüfen
```

## Kontrollen

**Quellen-Alarm.** Nach jeder Anreicherung wird die Trefferquote je Quelle mit ihrem bisherigen Schnitt verglichen.
Eine Warnung gibt es, wenn sie unter 30 % liegt oder um mehr als 30 Prozentpunkte fällt (ab 5 Abfragen im Lauf und
20 in der Historie), oder bei drei und mehr Sperren.

**Stichprobe.** Wöchentlich werden 10 zufällige „sichere“ Artikel gegen die Herstellerseite geprüft: Nummer, Produkt,
Name und Bild. Fehlerhafte Artikel kommen auf eine Sperrliste und stehen beim nächsten Lauf wieder auf „prüfen“, bis
jemand sie erneut freigibt. Die Fehlerquote der letzten vier Stichproben steht im Dashboard.

## Ergebnisse bisher

| Messung | Ergebnis |
|---|---|
| Machbarkeitstest, 20 Artikel aus 11 Herstellern | 18 eindeutig gefunden |
| Lapp nach Einbau der Variantenerkennung | 130 von 139 |
| KI-Recherche, 40 schwierige Fälle | 23 sicher, 11 prüfen, 6 Rückfragen an den Lieferanten |
| Stichproben | 20 von 20 korrekt; ein Schönheitsfehler (Name nur Serie) wurde im Programm behoben |
