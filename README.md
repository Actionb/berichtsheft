# bApp - die Berichtsheft App

Auszubildende haben Nachweise oder Berichte zu führen, in welchen sie beschreiben, was sie in einem Zeitabschnitt gelernt haben. Diese kleine Anwendung soll Auszubildenden dabei helfen, diese Nachweise zu schreiben und zu organisieren.

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