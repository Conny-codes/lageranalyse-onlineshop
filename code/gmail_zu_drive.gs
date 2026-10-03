/**
 * Google Apps Script: Lagerlisten aus Gmail automatisch in Google Drive ablegen.
 *
 * Einrichtung (einmalig):
 *   1. https://script.google.com -> "Neues Projekt", diesen Code einfügen, speichern.
 *   2. ABSENDER unten auf die E-Mail-Adresse des Lieferanten setzen.
 *   3. Oben die Funktion "einrichten" auswählen und auf "Ausführen" klicken.
 *      Google fragt einmal nach Berechtigungen für Gmail und Drive -> erlauben.
 *   Danach läuft "abholen" automatisch jede Stunde.
 *
 * Was passiert:
 *   - Sucht Mails von ABSENDER mit Excel-Anhang, die noch nicht verarbeitet sind.
 *   - Speichert jeden .xlsx-Anhang im Drive-Ordner ORDNER als "JJJJ-MM-TT_<Dateiname>.xlsx"
 *     (Datum = Eingangsdatum der Mail = Stichtag des Lagerstands).
 *   - Markiert die Mail mit dem Label LABEL, damit sie nicht doppelt verarbeitet wird.
 */
const ABSENDER = "lieferant@example.com";   // Absender der Lagerlisten
const ORDNER = "Lagereingang";
const LABEL = "Lagerliste-verarbeitet";  // ohne Leer-/Schrägstriche, damit die Gmail-Suche zuverlässig greift

function abholen() {
  const ordner = ordnerHolen_(ORDNER);
  const label = GmailApp.getUserLabelByName(LABEL) || GmailApp.createLabel(LABEL);
  const suche = `from:(${ABSENDER}) has:attachment filename:xlsx -label:${LABEL} newer_than:30d`;
  const threads = GmailApp.search(suche, 0, 20);

  threads.forEach(thread => {
    thread.getMessages().forEach(mail => {
      const datum = Utilities.formatDate(mail.getDate(), Session.getScriptTimeZone(), "yyyy-MM-dd");
      mail.getAttachments({ includeInlineImages: false }).forEach(anhang => {
        if (!/\.xlsx$/i.test(anhang.getName())) return;
        const name = `${datum}_${anhang.getName()}`;
        if (ordner.getFilesByName(name).hasNext()) return;  // schon abgelegt
        ordner.createFile(anhang.copyBlob().setName(name));
        console.log(`Abgelegt: ${name}`);
      });
    });
    thread.addLabel(label);
  });
}

function einrichten() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === "abholen")
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("abholen").timeBased().everyHours(1).create();
  abholen();  // einmal sofort ausführen
  console.log(`Eingerichtet. Ablage in Google Drive: ${ORDNER}`);
}

function ordnerHolen_(name) {
  const treffer = DriveApp.getFoldersByName(name);
  return treffer.hasNext() ? treffer.next() : DriveApp.createFolder(name);
}
