# bApp - die Berichtsheft App

Auszubildende haben Nachweise oder Berichte zu führen, in welchen sie beschreiben, was sie in einem Zeitabschnitt gelernt haben. Diese kleine Anwendung soll Auszubildenden dabei helfen, diese Nachweise zu schreiben und zu organisieren.

## Installation

### Installation via Docker

Voraussetzungen:
- [Docker](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/install/)
    
Repository clonen:

```sh
git clone https://github.com/Actionb/berichtsheft
```

Root CA Zertifikat kopieren:
```sh
mkdir .secrets; cp /pfad/zu/root/ca.crt .secrets/ca_certificates.crt
```

Dann im Repository Ordner die Docker Container bauen und starten:

```sh
docker compose up -d
```

Datenbankmigrationen ausführen:

```sh
docker exec -it bapp-web python manage.py migrate
```

Schreibrechte für Datenbankdatei und Datenbankordner für Apache einrichten:

```sh
docker exec -i bapp-web chown -R www-data:www-data /bapp/db
```

Datenbank wiederherstellen (optional):

```sh
cat backup.json | docker exec -i bapp-web python manage.py loaddata --format=json -
```

Oder unter Windows:

```sh
type backup.json | docker exec -i bapp-web python manage.py loaddata --format=json -
```

Die Anwendung sollte nun unter [http://127.0.0.1:8001/bapp/](http://127.0.0.1:8001/bapp/) laufen.

## Development

### Installation 

#### Repository clonen

```
git clone https://github.com/Actionb/berichtsheft; cd berichtsheft
```

#### Virtuelle Umgebung erzeugen

```
python manage.py -m venv .venv
```

Umgebung aktivieren (Windows Powershell):
```
& .venv/Scripts/Activate.ps1
```

#### Abhängigkeiten installieren

Die direkten Abhängigkeiten für das Projekt sind in `requirements.txt` festgehalten. Darüber hinaus werden für die Entwicklung weitere Abhängigkeiten benötigt, welche in der Datei `pyproject.toml` festgelegt sind.

```
pip install -r requirements.txt; pip install --group dev
```

#### Datenbank Verzeichnis erzeugen

Die Dateien für die sqlite Datenbank sollten in einem Unterordner abgelegt werden. Dazu ein neues Verzeichnis anlegen:

```
mkdir db
```

#### Datenbank Migrationen ausführen

```
python manage.py migrate
```

#### Admin Superuser erstellen

```
python manage.py createsuperuser
```

#### Development Server starten

```
python manage.py runserver
```

### Tests

Tests mit coverage ausführen:

```shell
pytest --cov --cov-branch --cov-report=html
```