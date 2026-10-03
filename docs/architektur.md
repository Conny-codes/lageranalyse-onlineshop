# Architektur

## Wege durch das System

```
┌─ Google (Cloud) ───────────────────────────────────────────────────────────┐
│  Gmail ──► Apps Script „abholen“ (stündlich) ──► Drive/Lagereingang/        │
│                                                   2026-07-09_Lager.xlsx     │
└──────────────────────────────────────────────┬──────────────────────────────┘
                                               │ Google Drive für Desktop
┌─ PC: Windows-Aufgabe (täglich + nach Anmeldung) ▼ ──────────────────────────┐
│  eingang.py   neue Datei? → Kopie nach data/eingang, Stichtag aus Dateiname │
│     │                                                                       │
│     ▼                                                                       │
│  run.py                                                                     │
│   1 einlesen      Kopfzeile finden, Hersteller aus Kürzel, Nummern prüfen   │
│   2 archivieren   data/archiv/lager_<Stichtag>.xlsx                         │
│   3 abgleich      gegen den vorherigen Archivstand                          │
│   4 anreichern    nur Artikel ohne gültigen Cache-Eintrag (Sperre per Lock) │
│   5 bewerten      Cache + Korrekturen + Stichproben-Sperren → Status        │
│   6 qualitaet     Trefferquote je Quelle → Warnungen                        │
│   7 export        CSV, Prüfliste, Auswertung, Dashboard                     │
└──────────────────────────────────────────────┬──────────────────────────────┘
                                               ▼
┌─ Claude-App (geplante Aufgaben) ────────────────────────────────────────────┐
│  täglich   recherche.py offen → recherchieren → recherche.py uebernehmen    │
│            → data/korrekturen/claude_<Datum>.xlsx → run.py neu              │
│  montags   stichprobe.py ziehen → gegen Herstellerseite prüfen → auswerten  │
│            → data/gesperrt.json → run.py neu                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module

| Modul | Aufgabe | Zeilen |
|---|---|---|
| `einlesen.py` | Lagerdatei lesen, Spalten erkennen, Hersteller und Suchnummern ableiten, Platzhalter erkennen | 110 |
| `abgleich.py` | Zwei Stände vergleichen, Kennzahlen | 70 |
| `anreichern.py` | Browser-Steuerung, Quellen, Bestätigung, Cache, Sperren | 290 |
| `bewertung.py` | Statuslogik, Korrekturen einlesen | 100 |
| `qualitaet.py` | Quellen-Alarm, Stichproben | 110 |
| `export.py` | WooCommerce-CSV, Prüfliste, Auswertung (Excel) | 130 |
| `dashboard.py` + Vorlage | eigenständige HTML-Seite, SVG-Diagramme | 360 |
| `run.py` | Ablauf eines Laufs, Verlauf über alle Stände | 220 |
| `eingang.py`, `recherche.py`, `stichprobe.py` | Einstiegspunkte für Aufgabenplanung und KI-Stufe | 220 |

## Datenhaltung

Bewusst einfach, alles als Dateien:

| Ort | Inhalt |
|---|---|
| `data/archiv/` | jeder Lagerstand als Excel, die Basis für Abgleich und Verlauf |
| `data/cache/produktdaten.json` | gefundene Produktdaten je Hersteller + Bestellnummer, mit Quellenversion |
| `data/korrekturen/` | ausgefüllte Prüflisten und Funde der KI-Recherche, gleiches Format |
| `data/gesperrt.json` | Artikel, die in der Stichprobe durchgefallen sind |
| `data/quellen_statistik.json` | Trefferquote je Quelle und Lauf |
| `output/<Stichtag>/` | alle Ausgaben eines Laufs |

## Was ich heute anders machen würde

- **Tests von Anfang an.** Die Prüfung der Nummern und die Statuslogik wurden mit Einzeltests abgesichert, aber nicht als
  Testsuite im Repository. Die Fehler, die in der Fallstudie stehen, hätten Tests mit echten Grenzfällen früher gefunden.
- **`run.py` aufteilen.** Der Ablauf und das Zusammenstellen der Dashboard-Daten stecken in einer Datei, die auf
  220 Zeilen gewachsen ist.
- **Quellen als Plugins.** Jede Herstellerquelle ist ein Eintrag in einem Dictionary mit Schaltern (`typ_aus_h1`,
  `name_umdrehen`, …). Bei elf Quellen geht das noch. Bei mehr wäre eine kleine Klasse je Quelle übersichtlicher.
- **Cache in SQLite statt JSON.** Bei 2.000 Einträgen reicht JSON. Bei mehreren Lieferanten wäre eine Datenbank robuster,
  vor allem wenn zwei Läufe gleichzeitig schreiben wollen. Heute verhindert das eine Sperrdatei.
- **Plattformunabhängig.** Die Automatisierung hängt an der Windows-Aufgabenplanung und einem angemeldeten Benutzer, weil
  der Browser ein Fenster braucht.
