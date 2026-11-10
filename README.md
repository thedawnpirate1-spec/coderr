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
   Kopiere `.env.example` zu `.env` und passe bei Bedarf `SECRET_KEY`, `DEBUG` und `ALLOWED_HOSTS` an.

5. Datenbankmigrationen ausführen und Server starten:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

Die API ist anschließend unter `http://127.0.0.1:8000/api/` erreichbar.

## Tests ausführen

Alle automatisierten Tests über sämtliche Apps starten:

```bash
python manage.py test
```

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

