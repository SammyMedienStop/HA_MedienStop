# MedienStop.de – Home Assistant Integration

[![hacs][hacs-badge]][hacs] ![version][version-badge] ![license][license-badge]

Bildschirmzeit-/Fernseh-Steuerung für Kinder als Home-Assistant-Integration.
Verwaltet pro Kind ein Tagesbudget und Zeitfenster, schaltet den Fernseher nach
Ablauf automatisch aus (optional mit „Abschiedsvideo") und bietet Eltern ein
Dashboard mit Profilen, Statistik, Elternmodus, Essenspause u. v. m.

> Domain: `medienstop` · Anzeigename: **MedienStop.de** · Typ: local_push · Config-Flow: ja

---

## Funktionen

- **Profile** mit Budget (Minuten) und erlaubtem Zeitfenster je Tagtyp
  **Werktag / Wochenende / Ferien**. Kinder werden Profilen zugewiesen.
- **Schulnacht-Logik**: Wochenende = Freitag + Samstag; Sonntag zählt als Werktag.
- **Nächtlicher Reset (0 Uhr)**: Restzeit = Budget des heutigen Tagtyps des
  zugewiesenen Profils.
- **Zeitschleife**: zählt laufende Timer minütlich herunter; zusätzlich alle 15 s
  Prüfung, ob der Fernseher an ist, obwohl niemand berechtigt ist → schaltet aus.
- **Play/Pause/Stop** pro Kind. Nur ein Kind gleichzeitig; Start bei Restzeit 0
  gesperrt. Kinder können nicht stoppen.
- **Elternmodus** (Override, übersteht Neustart), **Essenspause** (Hart-Aus),
  **Ferien-Schalter**, **Elternzeit-Auto-Aus** zu einstellbarer Uhrzeit.
- **Videos vor dem Ausschalten**: eigenes Video/Bild für „Zeit abgelaufen",
  „Zeitfenster-Ende" und „kein Timer" – je mit eigener Abschalt-Verzögerung.
  Auswahl bequem über den **Media-Browser**. Getrennter **Video-Player** (Cast/DLNA)
  möglich, falls der TV `play_media` in den Browser öffnet.
- **Statistik** je Kind: heute / diese Woche / dieser Monat / dieses Jahr geschaut.
- **Webhooks** pro Kind (aktiv/inaktiv) und für den Elternmodus – für eigene
  Automatisierungen.
- **Tab-Sichtbarkeit** pro Benutzer (Kinder sehen nur ihren Tab), persistent in
  der Integration und damit update-fest.
- **Dashboard-Generator** (Knopf/Service) erzeugt ein fertiges Lovelace-YAML.
- **Diagnose-Knopf** und **Heartbeat-Sensor „Letzte Prüfung"** zur Fehlersuche.

## Voraussetzungen

- Home Assistant 2024.4 oder neuer.
- Für das Abschalten/Streamen: eine schaltbare Entität (Steckdose/`switch`,
  `media_player`, …) bzw. für Videos ein **streamfähiger** `media_player`
  (Chromecast/Cast oder DLNA Digital Media Renderer).

## Installation

### HACS (empfohlen)
1. HACS → drei Punkte → **Benutzerdefinierte Repositories**.
2. URL `https://github.com/familiekairies-cmd/ha-medienstop`, Kategorie **Integration**.
3. „MedienStop.de" installieren, Home Assistant neu starten.

### Manuell
1. Ordner `custom_components/medienstop/` aus diesem Repo nach
   `<config>/custom_components/` kopieren.
2. Home Assistant neu starten.

## Einrichtung
*Einstellungen → Geräte & Dienste → Integration hinzufügen → „MedienStop.de".*
Der Assistent fragt: Anzahl Kinder/Profile, Fernseher- und optional Video-Player-
Entität, Namen, Sichtbarkeit (Eltern/Kinder je Benutzer), Dashboard-Variante.
Videos werden später über *Konfigurieren → Videos* per Media-Browser gewählt.

## Dashboard
Am Hub-Gerät den Knopf **„Dashboard-Vorlage erstellen"** drücken → das erzeugte
YAML aus der Benachrichtigung in ein neues Dashboard (Raw-Editor) einfügen.
Bausteine, Beispiele und ein Generator liegen im Ordner [`dashboards/`](dashboards).

## Videos / Streaming – Hinweis (Panasonic, Samsung, LG, Android-TV)
Manche TV-Integrationen öffnen bei `play_media` den **TV-Browser** statt zu streamen.
Lösung: einen **Cast**- oder **DLNA-Renderer**-`media_player` als **„Video-Player"**
wählen (Feld im Setup/Konfigurieren). Details siehe
[`brand/`](brand) und die Hinweise in der README der Integration.

## Fehlersuche
- **Diagnose-Knopf** am Hub → Benachrichtigung mit komplettem Zustand (inkl. Ziel).
- Sensor **„Letzte Prüfung"** muss ~alle 15 s ticken (sonst läuft die Logik nicht).
- Diagnose-Logzeilen erscheinen als **WARNING** im HA-Protokoll (Filter: `MedienStop.de`).

## Lizenz
[MIT](LICENSE)

[hacs]: https://hacs.xyz
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[version-badge]: https://img.shields.io/badge/version-2.0.0-blue.svg
[license-badge]: https://img.shields.io/badge/license-MIT-green.svg


## Für Entwickler / KIs (LLMs)
Wiedereinstieg ins Projekt: zuerst [`AGENTS.md`](AGENTS.md) lesen, dann
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (Aufbau/Logik),
[`docs/PATCHLOG.md`](docs/PATCHLOG.md) (Fixes + Ursachen) und
[`docs/REFERENCE.md`](docs/REFERENCE.md) (Services/Entities/Config).


## Videos für andere bereitstellen
Die drei „Abschalt-Videos" liegen im Ordner [`media/`](media) (mit Zuordnung und
Installations-Anleitung in [`media/README.md`](media/README.md)). Sie sind **nicht**
Teil der HACS-Installation – jede/r Nutzer/in muss sie einmal in den eigenen
Home-Assistant-Ordner `config/media/` kopieren und in *MedienStop.de → Konfigurieren
→ Videos* auswählen.

Zum Teilen am einfachsten: das gebündelte **`medienstop-media.zip`** (Release-Anhang
oder direkt als Datei) an die Person geben – entpacken, die drei `.mp4` nach
`config/media/` legen, fertig.
