# Coderr mit Postman testen

1. Backend starten: `.\.venv\Scripts\python.exe manage.py runserver`
2. In Postman **Import** auswaehlen und `Coderr.postman_collection.json` importieren.
3. Die Collection-Variable `base_url` bei Bedarf anpassen (Standard: `http://127.0.0.1:8000`).
4. Die gesamte Collection ueber **Run collection** in unveraenderter Reihenfolge mit einer Iteration starten.

Tokens und IDs werden automatisch gespeichert. Ein Environment ist nicht erforderlich.
Die Collection erstellt pro Durchlauf zwei neue Testnutzer und eine abgeschlossene
Bestellung. Angebot und Bewertung werden am Ende geloescht. Nur gegen eine lokale
Testinstanz ausfuehren; Nutzer und Bestellung bleiben bei einem Postman-Lauf bestehen.

## Isolierter lokaler Test

```powershell
.\.venv\Scripts\python.exe postman/run_tests.py
```

Benoetigt die vorhandene Python-Umgebung und Node.js. Erstellt eine temporaere
Datenbank, fuehrt dieselben 33 Requests ueber Djangos Test-Client aus und wertet
die JavaScript-Pruefungen der Collection mit einem kleinen lokalen Runner aus.
Die bestehende Datenbank wird nicht verwendet. Das Ergebnis steht in
`test-results.json`, ohne Tokens oder Passwoerter.

Dieser Runner unterstuetzt nur die in dieser Collection verwendeten Postman-Funktionen.
Ein Test im echten Postman-/Newman-Runtime ist damit nicht abgedeckt, ebenso wenig
Netzwerk, HTTP-Server oder CORS. In der Ausfuehrungsumgebung waren npm und lokale
HTTP-Verbindungen gesperrt; deshalb wurde dieser Testweg verwendet.
