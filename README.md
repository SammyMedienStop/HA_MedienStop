<div align="center">

# 📺 MedienStop.de
### Bildschirmzeit-Steuerung für Home Assistant

**Ein Zusatzprojekt von [MedienStop.de](https://medienstop.de) – der Kindersicherung, die Eltern wirklich verstehen.**

[![Home Assistant][ha-badge]][ha] [![HACS][hacs-badge]][hacs] [![Release][release-badge]][releases] [![License: MIT][mit-badge]][mit] [![Website][web-badge]][website] [![Spenden][donate-badge]][donate]

[Website](https://medienstop.de) · [Installation](#-installation) · [Einrichtung](#-einrichtung) · [Dashboard](#-dashboard-einrichten) · [Videos](#-abschalt-videos) · [Audio](#-audio-ansagen-zum-download) · [Fehlersuche](#-fehlersuche) · [❤️ Spenden][donate]

</div>

---

## Über MedienStop.de

**[MedienStop.de](https://medienstop.de)** hilft Eltern, das **digitale Zuhause
ihrer Kinder Schritt für Schritt sicher zu machen** – verständlich erklärt, ohne
Technik-Kauderwelsch, „wie bei einem Kaffee im Wohnzimmer". Dazu gehören über 20
kostenlose **Schritt-für-Schritt-Anleitungen** (FRITZ!Box & WLAN, Handy & Tablet,
Konsolen, Computer, Fernseher & Streaming, Apps & Spiele) – alle **auch zum
Anhören** –, das geführte Eltern-Dashboard **Eltern-SOC** und das Workbook
**Familien-Fahrplan**.

## Was ist dieses Projekt?

Diese **Home-Assistant-Integration** ist ein **Zusatzprojekt** von MedienStop.de –
für Familien, die zuhause **Home Assistant** nutzen und die **Bildschirmzeit ihrer
Kinder automatisieren** möchten. Sie verwaltet pro Kind ein Tagesbudget und
erlaubte Zeitfenster, zählt die Zeit herunter und schaltet den Fernseher
automatisch aus, wenn die Zeit vorbei ist – optional mit einer kurzen
**Abschieds-Ansage** als Video oder Ton („Deine Zeit ist um" / „Schlaf gut" /
„Jetzt ist keine Fernsehzeit"). Ein kleiner, technischer Baustein der großen
MedienStop-Idee.

> [!NOTE]
> **Neu bei Home Assistant?** Home Assistant ist eine kostenlose Smart-Home-Zentrale,
> die du selbst betreibst. Diese Integration ist eine Erweiterung dafür. Wenn du
> Home Assistant (noch) nicht nutzt, schau am besten direkt auf
> [MedienStop.de](https://medienstop.de) vorbei – dort brauchst du keine Technik.

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
- **Abschalt-Ansagen als Video _oder_ Audio** für „Zeit abgelaufen",
  „Schlafenszeit" und „keine TV-Zeit" – je mit eigener Verzögerung, Auswahl per
  Media-Browser, streambar via Cast/DLNA.
- **Statistik** je Kind: heute / Woche / Monat / Jahr geschaut.
- **Statistik zurücksetzen** – pro Kind oder für alle (Knopf am Gerät/Hub oder
  Service `medienstop.reset_statistics`).
- **Webhooks** je Kind und für den Elternmodus – für eigene Automatisierungen.
- **Tab-Sichtbarkeit je Benutzer** (Kinder sehen nur ihren Tab), update-fest.
- **Dashboard-Generator** auf Knopfdruck + **Diagnose-Tools**.

## 📸 Screenshots

![Überblick: Integration, Budgets, Steuerung und Abschalt-Ansagen](https://raw.githubusercontent.com/SammyMedienStop/HA_MedienStop/main/docs/screenshots/00_uebersicht.png)

| Budgets & Zeitfenster | Video-/Audio-Ansagen |
|---|---|
| ![Budgets & Zeitfenster](https://raw.githubusercontent.com/SammyMedienStop/HA_MedienStop/main/docs/screenshots/01_budgets-zeitfenster.png) | ![Video-/Audio-Ansagen](https://raw.githubusercontent.com/SammyMedienStop/HA_MedienStop/main/docs/screenshots/10_videos-audio.png) |

Mehr Screenshots im Ordner [`docs/screenshots/`](docs/screenshots/).

## ✅ Voraussetzungen

- Home Assistant **2024.4** oder neuer.
- Eine schaltbare Entität als „Fernseher" (Steckdose/`switch`, `media_player` …).
- Für Videos/Audio: ein **streamfähiger** `media_player` (Chromecast/Cast **oder**
  DLNA Digital Media Renderer). Für reine **Audio**-Ansagen genügt auch ein
  **Lautsprecher** (z. B. Google-Nest-/Cast-Lautsprecher).

## 📦 Installation

> [!TIP]
> **Was ist HACS?** Der [Home Assistant Community Store (HACS)](https://hacs.xyz/)
> ist ein „App-Store" für Erweiterungen. Damit installierst du MedienStop.de mit
> wenigen Klicks und bekommst Updates angezeigt. Die einmalige HACS-Einrichtung
> ist auf [hacs.xyz](https://hacs.xyz/) beschrieben.

### Variante A – HACS (empfohlen)
1. In HACS oben rechts auf **⋮ → Benutzerdefinierte Repositories**.
2. Repository: `https://github.com/SammyMedienStop/HA_MedienStop`
   – Kategorie: **Integration**. Auf **Hinzufügen**.
3. „MedienStop.de" suchen, **installieren**, Home Assistant **neu starten**.

### Variante B – Manuell (ohne HACS)
1. Im [neuesten Release][releases] die Datei `medienstop-x.y.z.zip` herunterladen
   und entpacken.
2. Den Ordner `custom_components/medienstop/` in deinen Home-Assistant-Konfigurations-
   ordner kopieren, sodass `…/config/custom_components/medienstop/` entsteht.
   (Den Ordner `custom_components` ggf. selbst anlegen.)
3. Home Assistant **neu starten**.

## 🚀 Einrichtung

*Einstellungen → Geräte & Dienste → **Integration hinzufügen** → „MedienStop.de".*

Der Assistent fragt dich Schritt für Schritt:
1. **Anzahl Kinder & Profile**, optional **Fernseher-** und **Video-Player-Entität**.
2. **Namen** für Kinder und Profile.
3. **Sichtbarkeit**: welche/r HA-Benutzer die Eltern-Tabs bzw. den jeweiligen
   Kinder-Tab sieht.
4. **Dashboard-Variante**.

Videos und Audio wählst du danach unter *MedienStop.de → **Konfigurieren** → Videos*
(siehe [Videos](#-abschalt-videos) und [Audio](#-audio-ansagen-zum-download)).

## 🖥️ Dashboard einrichten

Die Integration erzeugt dir ein **fertiges Dashboard** als Vorlage – du musst nichts
von Hand bauen. So geht's, auch für Einsteiger:

1. **Vorlage erzeugen:** Öffne *Einstellungen → Geräte & Dienste → **MedienStop.de***
   und dort das Hub-Gerät. Drücke den Knopf **„Dashboard-Vorlage erstellen"**.
   *(Alternativ: Entwicklerwerkzeuge → Aktionen → `medienstop.create_dashboard`
   → **Aktion ausführen**.)*
2. **Vorlage öffnen:** Es erscheint eine **Benachrichtigung**. Klicke unten links in
   Home Assistant auf **„Benachrichtigungen"** und öffne den Eintrag
   **„MedienStop.de – Dashboard-Vorlage"**.
3. **Text kopieren:** Markiere den kompletten Text im grauen **Code-Feld** (das ist
   das YAML) und kopiere ihn (**Strg + C**).
4. **Neues Dashboard anlegen:** *Einstellungen → **Dashboards** → oben rechts
   **„Dashboard hinzufügen"** → **„Neues Dashboard von Grund auf"** → Name
   (z. B. „MedienStop") und Symbol wählen → **„Erstellen"***.
5. **Rohcode-Editor öffnen:** Öffne das neue Dashboard. Klicke oben rechts auf das
   **Stift-Symbol (Bearbeiten)** und bestätige den Hinweis. Dann oben rechts auf das
   **⋮-Menü → „Rohkonfigurationseditor"**.
6. **Einfügen & speichern:** Lösche den vorhandenen Inhalt komplett, füge den
   kopierten Text ein (**Strg + V**) und klicke **„Speichern"**. Schließe den Editor
   über das **✕** oben links.
7. **Fertig!** Deine Tabs (Eltern, Kinder, ggf. Statistik) sind da. Benennst du
   später Kinder oder Profile um, drücke einfach erneut **„Dashboard-Vorlage
   erstellen"** und wiederhole die Schritte.

> [!NOTE]
> Wer welchen Tab sieht, steckt bereits in der Vorlage – das hast du im
> Einrichtungs-Assistenten unter **Sichtbarkeit** festgelegt.

## 🎬 Abschalt-Videos

Kurz vor dem Ausschalten wird eine Ansage abgespielt. Es gibt drei Fälle:

| Fall | Wann | Datei (Beispiel) |
|---|---|---|
| **Zeit abgelaufen** | Tages-Guthaben aufgebraucht | `timeup_*.mp4` |
| **Schlafenszeit** | erlaubte Endzeit erreicht (z. B. 20 Uhr) | `limit_*.mp4` |
| **Keine TV-Zeit** | TV außerhalb der Zeit / ohne Timer gestartet | `notimer_*.mp4` |

### 📥 So fügst du die Medien hinzu

1. **Herunterladen:** Fertige Dateien hängen am [neuesten Release][releases]:
   **Videos** = `medienstop-media.zip`, **Audio** = `medienstop-audio.zip`.
   Entpacke das ZIP auf deinem Computer.
2. **In den Medien-Ordner legen:** Kopiere die Dateien in den Ordner **`media`** deiner
   Home-Assistant-Konfiguration (also `…/config/media/`). Gibt es den Ordner noch
   nicht, lege ihn an. *(Zugriff z. B. über das Samba-/Dateizugriff-Add-on.)*
3. **Auswählen:** In *MedienStop.de → **Konfigurieren** → Videos* öffnest du je Fall
   den **Media-Browser** und wählst die Datei unter **„Meine Medien"** aus. Für jede
   Ansage kannst du eine eigene **Abschalt-Verzögerung** einstellen.
4. **Testen:** Mit der Aktion `medienstop.test_video` (Entwicklerwerkzeuge → Aktionen)
   spielst du eine Ansage sofort ab.

## 🎧 Audio-Ansagen zum Download

> [!TIP]
> **Lieber nur Ton statt Video?** Es gibt alle drei Ansagen auch als **Audio-Dateien
> (MP3)** zum Download: **`medienstop-audio.zip`** am [neuesten Release][releases].
> Ideal, wenn dein Fernseher keine Videos direkt abspielt – oder wenn du die Ansage
> lieber über einen **Lautsprecher** (z. B. Google Nest / Chromecast) ausgeben willst.

| Fall | Audio-Datei |
|---|---|
| **Zeit abgelaufen** | `timeup_*.mp3` |
| **Schlafenszeit** | `limit_*.mp3` |
| **Keine TV-Zeit** | `notimer_*.mp3` |

**Hinzufügen:** genau wie bei den Videos (siehe
[📥 So fügst du die Medien hinzu](#-so-fügst-du-die-medien-hinzu)) – du wählst im
Media-Browser einfach die **`.mp3`**-Datei statt der `.mp4`. Als Ziel kannst du dann
auch einen reinen **Lautsprecher** als „Video-Player" eintragen.

> [!WARNING]
> **Öffnet sich der Browser statt des Videos?** (Panasonic, Samsung, LG, Android-TV)
> → wähle einen **Cast/Chromecast**- oder **DLNA-Renderer**-`media_player` als
> „Video-Player". Für reine **Audio**-Ansagen kannst du auch einen Lautsprecher als
> Ziel nehmen.

## 🗣️ Alternative: Text-Ansage über Alexa/Echo

Statt einer Video-/Audiodatei kann jede der drei Ansagen auch als **gesprochener
Text** ausgegeben werden – ideal für einen **Alexa/Echo-Lautsprecher** als
Video-Player, da der nicht ohne Weiteres eigene Mediendateien abspielen kann.

1. **Voraussetzung:** Die (kostenlose, per HACS installierbare) Integration
   **[Alexa Media Player](https://github.com/alandtse/alexa_media_player)** muss
   eingerichtet sein und deinen Echo als `media_player`-Entity bereitstellen.
2. Diese Entity unter *MedienStop.de → Konfigurieren* als **„Video-Player"**
   auswählen (genau wie einen Chromecast).
3. Unter *MedienStop.de → Konfigurieren → Videos* im Feld **„…oder Text-Ansage"**
   den gewünschten Satz eintragen (z. B. „Deine Zeit ist um, mach den Fernseher
   aus."). Ist ein Text eingetragen, wird er beim Abschalten **statt** eines
   eventuell zusätzlich gesetzten Videos vorgelesen.
4. Für Ansagen muss in der Alexa-App bei diesem Gerät **„Communications"**
   aktiviert sein – sonst bleibt der Lautsprecher stumm, ohne Fehlermeldung in
   Home Assistant.

> [!NOTE]
> Öffnest du den **Media-Browser** im Video-Feld für ein Alexa-Gerät, meldet
> Home Assistant „Mediaplayer unterstützt kein Auswählen aus Medienquellen" – das
> ist eine Einschränkung der Alexa-Integration selbst (sie kann keine Dateien
> durchsuchen), keine Einschränkung von MedienStop.de. Für Alexa/Echo einfach die
> **Text-Ansage** statt des Media-Browsers nutzen.

## 🩺 Fehlersuche

- **Diagnose-Knopf** am Hub → Benachrichtigung mit komplettem Zustand.
- Sensor **„Letzte Prüfung"** muss ~alle 15 s ticken (sonst läuft die Logik nicht →
  Home Assistant neu starten).
- Diagnose-Zeilen stehen als **WARNING** im Protokoll (*Einstellungen → System →
  Protokolle*, Filter: `MedienStop.de`).

## 🤝 Mitmachen & Support

Ideen, Fehler oder Wünsche? Gern als [Issue][issues] melden.
Rund um Medienerziehung & Jugendschutz: **[MedienStop.de](https://medienstop.de)**.

## ❤️ Unterstützen

Wenn dir MedienStop.de hilft, freue ich mich über eine kleine Spende – das hält das
Projekt am Leben:

👉 **[Per PayPal spenden](https://www.paypal.com/donate/?hosted_button_id=JN23TQFMSX5EU)**

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
[donate]: https://www.paypal.com/donate/?hosted_button_id=JN23TQFMSX5EU
[donate-badge]: https://img.shields.io/badge/PayPal-Spenden-00457C?logo=paypal&logoColor=white
