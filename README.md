# Cookbook Companion

## Überblick

"CookBook Companion" verwandelt die endlose Suche nach dem perfekten Rezept in ein Kinderspiel. Diese Anwendung holt passende Rezepte aus dem Internet, speichert sie lokal und ermöglicht die Suche nach Ihren Vorräten und Vorlieben. Als mehr als nur ein digitales Kochbuch, dient sie als Ihr persönlicher Assistent in der Küche, der Inspiration und Kreativität in die Zubereitung jeder Mahlzeit bringt. Schnell, benutzerfreundlich und inspirierend – "CookBook Companion" ist der Schlüssel zu kreativen und schmackhaften Gerichten, angepasst an Ihre persönliche Ausgangslage.

## Funktionen

- **Rezeptverwaltung**: Benutzer können Rezepte aus dem Internet abrufen und sie in die lokale Datenbank speichern.
- **Suchfunktionalität**: Ermöglicht das Durchsuchen der Rezeptdatenbank nach Zutaten, Rezeptnamen oder Kategorien.

## Technologie-Stack

- **Frontend**: HTML, CSS
- **Backend**: Flask (Python)
- **Datenbank**: MySQL
- **Deployment**: Docker, Docker Compose

## Voraussetzungen

- Docker
- Docker Compose

## Installation und Ausführung

1. **Docker Compose file abrufen**

    Rufen sie die Datei `docker-compose.yml` von folgendem Link auf und speichern sie sie: https://github.com/Quovadis1212/Cookbook-Companion/blob/main/docker/docker-compose.yml

2. **Docker Compose verwenden**

    Stellen Sie sicher, dass Docker und Docker Compose auf Ihrem System installiert sind. Führen Sie dann den folgenden Befehl im Verzeichnis aus, das die `docker-compose.yml`-Datei enthält, um die Anwendung und die dazugehörige Datenbank zu starten:

    ```bash
    docker-compose up -d
    ```

    Dieser Befehl startet die Container im Hintergrund. Um die Logs anzusehen, verwenden Sie:

    ```bash
    docker-compose logs -f
    ```

3. **Zugriff auf die Anwendung**

    Nachdem die Container erfolgreich gestartet wurden, ist die Anwendung unter `http://localhost:5000` von Ihrem Webbrowser aus erreichbar.
