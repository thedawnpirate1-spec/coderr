# Coderr Backend

REST-API-Backend für die Freelancer-Plattform Coderr auf Basis von Django und Django REST Framework.

## Funktionen und Apps

- `profiles_app`: Registrierung, Token-Login sowie Verwaltung von Kunden- und Anbieter-Profilen.
- `offers_app`: Erstellen, Filtern, Durchsuchen und Verwalten von Angeboten inklusive der drei Paketstufen (`basic`, `standard`, `premium`).
- `orders_app`: Buchung von Angebotsstufen durch Kunden, Statusverwaltung durch Anbieter und Auftragszähler.
- `reviews_app`: Kundenbewertungen für Anbieter sowie allgemeine Plattform-Statistiken (`/api/base-info/`).

## Voraussetzungen

- Python 3.12+
- Git

## Installation

1. Repository klonen und in das Projektverzeichnis wechseln:
   ```bash
   git clone <repository-url>
   cd coderr
   ```

2. Virtuelle Umgebung erstellen und aktivieren:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux:
   source .venv/bin/activate
   ```

3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

4. Umgebungsvariablen einrichten:
   ```bash
   cp .env.example .env
   # Windows (PowerShell): Copy-Item .env.example .env
   ```
   Öffne anschließend die neue `.env`-Datei und trage die Werte ein:

   | Variable | Pflicht | Beschreibung |
   | :--- | :--- | :--- |
   | `SECRET_KEY` | **ja** | Geheimer Schlüssel von Django. Es gibt keinen Standardwert, ohne diese Variable startet die Anwendung nicht (`ImproperlyConfigured`). |
   | `DEBUG` | nein | `True` für die Entwicklung (Standard), `False` für den Produktivbetrieb. |
   | `ALLOWED_HOSTS` | nein | Kommagetrennte Liste erlaubter Hosts (Standard: `127.0.0.1,localhost`). |

   Einen neuen `SECRET_KEY` erzeugst du mit:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
   Die `.env`-Datei ist in `.gitignore` eingetragen und darf nie committet werden.

5. Datenbankmigrationen ausführen und Server starten:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

Die API ist anschließend unter `http://127.0.0.1:8000/api/` erreichbar.

## Tests ausführen

Alle automatisierten Tests über sämtliche Apps starten:

```bash
python manage.py test --settings=core.test_settings
```

`core/test_settings.py` erweitert die normalen Einstellungen um einen schnellen
Passwort-Hasher (`MD5PasswordHasher`) und benötigt keine `.env`-Datei. Dadurch sinkt
die Laufzeit der Testsuite von über einer Minute auf unter eine Sekunde.
Verwende diese Einstellungen niemals außerhalb von Tests.

## Wichtigste API-Endpunkte

| Methode | Endpunkt | Beschreibung |
| :--- | :--- | :--- |
| `POST` | `/api/registration/` | Neuen Nutzer (`customer` oder `business`) registrieren |
| `POST` | `/api/login/` | Anmeldung mit Rückgabe von Token und `user_id` |
| `GET, PATCH` | `/api/profile/<int:pk>/` | Einzelprofil abrufen oder eigenes Profil aktualisieren |
| `GET` | `/api/profiles/business/` | Liste aller Business-Profile |
| `GET` | `/api/profiles/customer/` | Liste aller Kunden-Profile |
| `GET, POST` | `/api/offers/` | Angebote auflisten (Suche, Filter, Pagination) oder erstellen |
| `GET, PATCH, DELETE` | `/api/offers/<int:pk>/` | Einzelnes Angebot abrufen, bearbeiten oder löschen |
| `GET` | `/api/offerdetails/<int:pk>/` | Einzelne Angebotsstufe abrufen |
| `GET, POST` | `/api/orders/` | Eigene Bestellungen auflisten oder neue Bestellung anlegen |
| `PATCH, DELETE` | `/api/orders/<int:pk>/` | Bestellstatus ändern (Business) oder löschen (Staff) |
| `GET` | `/api/order-count/<int:business_user_id>/` | Anzahl laufender Bestellungen eines Anbieters |
| `GET` | `/api/completed-order-count/<int:business_user_id>/` | Anzahl abgeschlossener Bestellungen eines Anbieters |
| `GET, POST` | `/api/reviews/` | Bewertungen auflisten/filtern oder neue Bewertung abgeben |
| `PATCH, DELETE` | `/api/reviews/<int:pk>/` | Eigene Bewertung bearbeiten oder löschen |
| `GET` | `/api/base-info/` | Öffentliche Gesamtstatistik der Plattform |

