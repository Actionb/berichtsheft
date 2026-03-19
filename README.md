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

### Installation (dev container)

Installation mittels [VS Code Dev Container](https://code.visualstudio.com/docs/devcontainers/containers#_dev-container-features).

#### Systemvoraussetzungen

- [Git](https://git-scm.com/install/)
- [WSL 2](https://learn.microsoft.com/de-de/windows/wsl/install)
- [Docker in WSL](https://docs.docker.com/engine/install/ubuntu/)
- [VS Code Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

#### Repository clonen

```sh
git clone https://github.com/Actionb/berichtsheft; cd berichtsheft
```

#### CA Zertifikat bereitstellen:

Root CA Zertifikat kopieren:
```sh
mkdir .secrets; cp /pfad/zu/root/ca.crt .secrets/ca_certificates.crt
```

#### Dev Container bauen

Zunächst VS Code starten:

```sh
code .
```

Dann mit `Ctrl+Shift+P` oder `F1` die VS Code Command Palette anzeigen lassen und Dev Container bauen und starten. Alle nötigen Abhängigkeiten und VS Code Extensions werden nun in den Container installiert, welcher dann als Remote Codespace zur Verfügung steht.

#### Datenbank Migrationen ausführen

```sh
python manage.py migrate
```

#### Admin Superuser erstellen

```sh
python manage.py createsuperuser
```

#### Development Server starten

```sh
python manage.py runserver 0.0.0.0:8000
```

### Installation (Windows)

#### Systemvoraussetzungen

- [Git](https://git-scm.com/install/)
- [Apache](https://httpd.apache.org/download.cgi)
  
#### Repository clonen

```sh
git clone https://github.com/Actionb/berichtsheft; cd berichtsheft
```

#### Virtuelle Umgebung erzeugen

```sh
python manage.py -m venv .venv
```

Umgebung aktivieren (Windows Powershell):

```sh
& .venv/Scripts/Activate.ps1
```

#### Abhängigkeiten installieren

Die direkten Abhängigkeiten für das Projekt sind in `requirements.txt` festgehalten. Darüber hinaus werden für die Entwicklung weitere Abhängigkeiten benötigt, welche in der Datei `pyproject.toml` festgelegt sind.

```sh
pip install -r requirements.txt; pip install --group dev
```

#### Datenbank Verzeichnis erzeugen

Die Dateien für die sqlite Datenbank sollten in einem Unterordner abgelegt werden. Dazu ein neues Verzeichnis anlegen:

```sh
mkdir db
```

#### Datenbank Migrationen ausführen

```sh
python manage.py migrate
```

#### Admin Superuser erstellen

```sh
python manage.py createsuperuser
```

#### Development Server starten

```sh
python manage.py runserver
```

### Tests

Tests mit coverage ausführen:

```shell
pytest --cov --cov-branch --cov-report=html
```