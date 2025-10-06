# bApp - die Berichtsheft App

Auszubildende haben Nachweise oder Berichte zu führen, in welchen sie beschreiben, was sie in einem Zeitabschnitt gelernt haben. Diese kleine Anwendung soll Auszubildenden dabei helfen, diese Nachweise zu schreiben und zu organisieren.

## Development

### Repository clonen

```
git clone https://github.com/Actionb/berichtsheft; cd berichtsheft
```

### Virtuelle Umgebung erzeugen

```
python manage.py -m venv .venv
```

Umgebung aktivieren (Windows Powershell):
```
& .venv/Scripts/Activate.ps1
```

### Abhängigkeiten installieren

Die direkten Abhängigkeiten für das Projekt sind in `requirements.txt` festgehalten. Darüber hinaus werden für die Entwicklung weitere Abhängigkeiten benötigt, welche in der Datei `pyproject.toml` festgelegt sind.

```
pip install -r requirements.txt; pip install --group dev
```
