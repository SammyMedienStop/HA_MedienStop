<div align="center">

# 📺 MedienStop.de – Bildschirmzeit-Steuerung für Home Assistant

**Faire Fernsehzeit für Kinder – automatisch, kindgerecht und elternfreundlich.**

[![Home Assistant][ha-badge]][ha] [![HACS][hacs-badge]][hacs] [![Release][release-badge]][releases] [![License: MIT][mit-badge]][mit] [![Website][web-badge]][website]

[Website](https://medienstop.de) · [Installation](#-installation) · [Einrichtung](#-einrichtung) · [Videos](#-abschalt-videos) · [Fehlersuche](#-fehlersuche)

</div>

---

## Was ist MedienStop.de?

**MedienStop.de** ist eine Home-Assistant-Integration, die die **Fernsehzeit von
Kindern** verwaltet: pro Kind ein Tagesbudget und erlaubte Zeitfenster, ein
automatischer Timer, und – wenn die Zeit vorbei ist – schaltet der Fernseher
sich von selbst aus. Optional wird vorher ein kurzes **Abschieds-Video**
eingeblendet („Deine Zeit ist um" / „Schlaf gut" / „Jetzt ist keine Fernsehzeit").

Mehr rund um Medienerziehung, Jugendschutz und Familien-Technik findest du auf
**👉 [MedienStop.de](https://medienstop.de)**.

## ✨ Funktionen

- **Profile** mit Budget (Minuten) und Zeitfenster je Tagtyp **Werktag /
  Wochenende / Ferien**. Kinder werden Profilen zugewiesen.
- **„Schulnacht"-Logik**: Wochenende = Freitag + Samstag; Sonntag zählt als Werktag.
- **Nächtlicher Reset (0 Uhr)** auf das Tagesbudget – neustartfest.
- **Automatische TV-Abschaltung**: prüft alle 15 s, ob geschaut wird, obwohl keine
  Zeit/kein Timer aktiv ist – und schaltet dann aus.
- **Play / Pause / Stop** je Kind, nur ein Kind gleichzeitig, kein Start bei 0 Minuten.
- **Elternmodus** (Override, neustartfest), **Essenspause** (Hart-Aus),
  **Ferien-Schalter**, **Elternzeit-Auto-Aus** zu fester Uhrzeit.
- **Abschalt-Videos** für „Zeit abgelaufen", „Schlafenszeit" und „keine TV-Zeit" –
  je mit eigener Verzögerung, Auswahl per Media-Browser, streambar via Cast/DLNA.
- **Statistik** je Kind: heute / Woche / Monat / Jahr geschaut.
- **Webhooks** je Kind und für den Elternmodus – für eigene Automatisierungen.
- **Tab-Sichtbarkeit je Benutzer** (Kinder sehen nur ihren Tab), update-fest.
- **Dashboard-Generator** auf Knopfdruck + **Diagnose-Tools**.

## ✅ Voraussetzungen

- Home Assistant **2024.4** oder neuer.
- Eine schaltbare Entität als „Fernseher" (Steckdose/`switch`, `media_player` …).
- Für Videos: ein **streamfähiger** `media_player` (Chromecast/Cast **oder**
  DLNA Digital Media Renderer).

## 📦 Installation

### Variante A – HACS (empfohlen)
1. In HACS oben rechts auf **⋮ → Benutzerdefinierte Repositories**.
2. Repository: `https://github.com/SammyMedienStop/HA_MedienStop`
   – Kategorie: **Integration**. Hinzufügen.
3. „MedienStop.de" suchen, **installieren**, Home Assistant **neu starten**.

### Variante B – Manuell
1. Im [neuesten Release][releases] die Datei `medienstop-x.y.z.zip` herunterladen.
2. Den Ordner `custom_components/medienstop/` nach `<config>/custom_components/`
   kopieren.
3. Home Assistant **neu starten**.

## 🚀 Einrichtung

*Einstellungen → Geräte & Dienste → **Integration hinzufügen** → „MedienStop.de".*

Der Assistent fragt Schritt für Schritt:
1. **Anzahl Kinder & Profile**, optional **Fernseher-** und **Video-Player-Entität**.
2. **Namen** für Kinder und Profile.
3. **Sichtbarkeit**: welche/r HA-Benutzer die Eltern-Tabs bzw. den jeweiligen
   Kinder-Tab sieht.
4. **Dashboard-Variante**.

Videos wählst du danach unter *MedienStop.de → **Konfigurieren** → Videos*.
Ein fertiges **Dashboard** erzeugt der Knopf **„Dashboard-Vorlage erstellen"** am
Hub-Gerät (Text kopieren, in ein neues Dashboard einfügen).

## 🎬 Abschalt-Videos

Drei kurze Clips werden vor dem Ausschalten eingeblendet:

| Fall | Wann | Datei (Beispiel) |
|---|---|---|
| **Zeit abgelaufen** | Tages-Guthaben aufgebraucht | `timeup_*.mp4` |
| **Schlafenszeit** | erlaubte Endzeit erreicht (z. B. 20 Uhr) | `limit_*.mp4` |
| **Keine TV-Zeit** | TV außerhalb der Zeit / ohne Timer gestartet | `notimer_*.mp4` |

Die Videos sind **nicht** Teil der Integration – lege sie in deinen HA-Ordner
`config/media/` und wähle sie im Setup aus. Fertige Beispiel-Videos hängen als
`medienstop-media.zip` an den [Releases][releases].

> **Streamt der TV nicht, sondern öffnet den Browser?** (Panasonic, Samsung, LG,
> Android-TV) → wähle einen **Cast/Chromecast**- oder **DLNA-Renderer**-`media_player`
> als „Video-Player". Details in der Doku.

## 🩺 Fehlersuche

- **Diagnose-Knopf** am Hub → Benachrichtigung mit komplettem Zustand.
- Sensor **„Letzte Prüfung"** muss ~alle 15 s ticken (sonst läuft die Logik nicht →
  HA neu starten).
- Diagnose-Zeilen stehen als **WARNING** im Protokoll (Filter: `MedienStop.de`).

## 🤝 Mitmachen & Support

Ideen, Fehler oder Wünsche? Gern als [Issue][issues] melden.
Rund um Medienerziehung & Jugendschutz: **[MedienStop.de](https://medienstop.de)**.

## 📄 Lizenz

Veröffentlicht unter der **[MIT-Lizenz](LICENSE)**.

---

<div align="center">
Mit ❤️ für entspanntere Fernsehabende · <a href="https://medienstop.de">MedienStop.de</a>
</div>

[ha]: https://www.home-assistant.io/
[hacs]: https://hacs.xyz/
[website]: https://medienstop.de
[releases]: https://github.com/SammyMedienStop/HA_MedienStop/releases
[issues]: https://github.com/SammyMedienStop/HA_MedienStop/issues
[mit]: LICENSE
[ha-badge]: https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=homeassistant&logoColor=white
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[release-badge]: https://img.shields.io/github/v/release/SammyMedienStop/HA_MedienStop?display_name=tag
[mit-badge]: https://img.shields.io/badge/License-MIT-green.svg
[web-badge]: https://img.shields.io/badge/Web-MedienStop.de-ff7f0e
