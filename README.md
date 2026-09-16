🇩🇪 Deutsch · 🇬🇧 [English version](README_EN.md)

<div align="center">

# 📺 MedienStop.de
### Bildschirmzeit-Steuerung für Home Assistant

**Ein Zusatzprojekt von [MedienStop.de](https://medienstop.de) – der Kindersicherung, die Eltern wirklich verstehen.**

[![Home Assistant][ha-badge]][ha] [![HACS][hacs-badge]][hacs] [![Release][release-badge]][releases] [![License: MIT][mit-badge]][mit] [![Website][web-badge]][website] [![Spenden][donate-badge]][donate]

[Website](https://medienstop.de) · [Installation](#-installation) · [Einrichtung](#-einrichtung) · [Dashboard](#-dashboard-einrichten) · [Ansagen](#-abschalt-ansagen) · [Alexa/Echo](#️-ansagen-über-alexaecho) · [Hooks](#-hooks-für-eigene-automatisierungen) · [Fehlersuche](#-fehlersuche) · [❤️ Spenden][donate]

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
- **Webhooks (Hooks)** je Kind und für den Elternmodus – für eigene Automatisierungen
  (siehe [Hooks](#-hooks-für-eigene-automatisierungen)).
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
   und entpacken. Darin liegt **ein** Ordner namens `medienstop`.
2. Diesen Ordner `medienstop` in den Ordner `custom_components` deiner
   Home-Assistant-Konfiguration kopieren, sodass genau dieser Pfad entsteht:

   ```
   config/custom_components/medienstop/manifest.json
   ```

   Den Ordner `custom_components` ggf. vorher selbst anlegen. Er liegt neben deiner
   `configuration.yaml` – erreichbar z. B. über das Add-on *Samba share*, *Studio Code
   Server* oder *File editor*.
3. Home Assistant **neu starten**.

> [!TIP]
> Ob es geklappt hat, siehst du unter *Einstellungen → Geräte & Dienste →
> **Integration hinzufügen***: Dort muss „MedienStop.de" jetzt auftauchen. Erscheint
> es nicht, stimmt meist der Pfad nicht – häufigster Fehler ist ein Ordner zu tief,
> also `custom_components/medienstop/medienstop/`.

## 🚀 Einrichtung

*Einstellungen → Geräte & Dienste → **Integration hinzufügen** → „MedienStop.de".*

Der Assistent fragt dich Schritt für Schritt:
1. **Anzahl Kinder & Profile**, optional **Fernseher-** und **Video-Player-Entität**.
2. **Namen** für Kinder und Profile.
3. **Sichtbarkeit**: welche/r HA-Benutzer die Eltern-Tabs bzw. den jeweiligen
   Kinder-Tab sieht.
4. **Dashboard-Variante**.

Die Ansagen vor dem Ausschalten wählst du danach unter *MedienStop.de →
**Konfigurieren*** – dort gibt es je einen Menüpunkt pro Fall
(siehe [Abschalt-Ansagen](#-abschalt-ansagen)).

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
> Einrichtungs-Assistenten unter **Sichtbarkeit** festgelegt. Die Zuordnung wirkt
> außerdem als **Schutz**: Ein Benutzer, der einem Kind zugeordnet ist, kann nur den
> eigenen Timer starten und pausieren – nicht die Timer der Geschwister, nicht die
> Elternzeit und keine anderen Eltern-Funktionen. Auch dann nicht, wenn er einen
> versteckten Tab per Adresse aufruft.

### 👨‍👩‍👧 Der Tab „Kinder" für Eltern

Neben dem Eltern-Tab gibt es einen Tab **„Kinder"**, der die Steuerung **aller** Kinder
untereinander zeigt – mit demselben **Play**-Knopf, den auch das Kind sieht. Praktisch,
wenn du zwischendurch Zeit freigeben willst, ohne dich als Kind anzumelden.

Der Tab ist **nur für die Eltern-Benutzer** sichtbar; die einzelnen Kinder-Tabs bleiben
weiterhin dem jeweiligen Kind vorbehalten. Abschalten kannst du ihn unter
*Konfigurieren → **Sichtbarkeit*** – danach das Dashboard einmal neu erzeugen.

## 🎬 Abschalt-Ansagen

Kurz vor dem Ausschalten wird eine Ansage abgespielt. Es gibt drei Fälle, jeweils
mit eigener Quelle und eigener Verzögerung:

| Fall | Wann | Mitgelieferte Vorlage |
|---|---|---|
| **Zeit abgelaufen** | Tages-Guthaben aufgebraucht | „Fernsehzeit vorbei" |
| **Schlafenszeit** | erlaubte Endzeit erreicht (z. B. 20 Uhr) | „Schlaft gut" |
| **Keine TV-Zeit** | TV außerhalb der Zeit / ohne Timer gestartet | „Keine TV-Zeit" |

### ✅ Einfachster Weg: „Mitgelieferte Ansage" stehen lassen

Du musst **nichts herunterladen, nichts kopieren und nichts über Dateiformate wissen**:

1. *Einstellungen → Geräte & Dienste → **MedienStop.de** → **Konfigurieren***.
2. Den Punkt für den gewünschten Fall wählen, z. B. **„Ansage: Zeit/Budget
   abgelaufen"**.
3. Unter **„Quelle der Ansage"** steht bereits **„Mitgelieferte Ansage – passend zum
   Gerät"**. Das ist die Voreinstellung und in aller Regel genau richtig.
4. Häkchen bei **„Jetzt testen – noch nicht speichern"** setzen und absenden: Die
   Ansage wird sofort abgespielt, **ohne** etwas zu speichern. Der Dialog schreibt dir
   danach, was passiert ist – und bei einem Problem auch, **woran** es lag. Passt
   alles, das Häkchen entfernen und erneut absenden; erst dann wird gespeichert.

> [!TIP]
> **Warum „passend zum Gerät"?** MedienStop.de sucht die Datei selbst aus: ein
> **Video** für den Fernseher, eine **Audiodatei** für einen Echo – und dazu die zum
> Anlass passende Ansage. Wechselst du später das Zielgerät, zieht die Ansage von
> allein nach. Du kannst eine bestimmte Vorlage auch weiterhin fest auswählen.

Es werden dir außerdem **nur Quellen angeboten, die auf deinem Gerät funktionieren**:
An einem Echo tauchen die Video-Vorlagen gar nicht erst auf, an einem Fernseher keine
Text-Ansage. Eine unmögliche Kombination lässt sich also nicht einstellen.

Jeder Fall wird **einzeln** gespeichert; die beiden anderen Ansagen und alle übrigen
Einstellungen bleiben dabei unberührt.

### 📥 Eigene Dateien verwenden

Statt der Vorlagen kannst du auch eigene Ansagen nutzen. Wählst du eine dieser
Quellen, fragt der Dialog **im nächsten Schritt genau die eine passende Angabe** ab –
du siehst nie Felder, die du nicht brauchst.

| Quelle | Wofür |
|---|---|
| **Eigene Datei aus dem Media-Browser** | Fernseher/Chromecast. Datei nach `…/config/media/` kopieren und im Browser auswählen. **Für Alexa nicht möglich** (wird dort auch nicht angeboten). |
| **Eigene Datei aus dem Ordner `www/`** | Auch für **Alexa** – Datei nach `…/config/www/` legen, die Internet-Adresse bildet MedienStop.de selbst. Ausgewählt wird aus einer Liste der vorhandenen Dateien, damit kein Tippfehler möglich ist. |
| **Eigene URL** | Beliebige Adresse im Internet. |
| **Text-Ansage** | Alexa liest einen frei eingegebenen Satz vor (nur an einem Echo). |
| **Eingebauter Alexa-Klang** | Glocke, Türgong usw. direkt von Amazon (nur an einem Echo). |
| **Keine Ansage** | Fernseher geht sofort aus. |

> [!IMPORTANT]
> **Eigene Audios für Alexa müssen konvertiert werden.** Amazon akzeptiert nur MP3 in
> einem ganz bestimmten Format – passt es nicht, bleibt der Echo **stumm, ohne
> Fehlermeldung**. Die vollständige Anleitung mit fertigem Befehl steht in
> **[`media/README.md`](media/README.md)**. Die mitgelieferten Audio-Vorlagen sind
> bereits passend aufbereitet.

**Testen:** Am Hub-Gerät gibt es für **jeden der drei Fälle** einen eigenen
Test-Knopf. Alternativ die Aktion `medienstop.test_video`
(Entwicklerwerkzeuge → Aktionen).

> [!WARNING]
> **Bleibt der Bildschirm schwarz oder öffnet sich der Browser?** (Panasonic, Samsung,
> LG, Android-TV) → Diese Fernseher nehmen den Abspiel-Befehl zwar an, streamen aber
> nicht. Wähle als **„Video-Player"** einen **Cast/Chromecast** oder den
> **DLNA-Renderer** deines Fernsehers. Achtung: Der DLNA-Eintrag erscheint in Home
> Assistant oft **erst, wenn der Fernseher eingeschaltet ist**. Für reine
> **Audio**-Ansagen genügt auch ein Lautsprecher als Ziel.

> [!NOTE]
> **Warum liegen Videos in `config/www/medienstop/`?** Viele Fernseher und
> DLNA-Empfänger kommen mit `https://`-Adressen nicht zurecht und bleiben dann stumm.
> MedienStop.de holt die mitgelieferten Vorlagen deshalb **einmalig** beim Start von
> Home Assistant in dein Heimnetz (rund 30 MB für die drei Videos) und spielt sie von
> dort per `http://` ab. Das läuft im Hintergrund und verzögert den Start nicht. Für
> **Alexa** wird nichts geladen – dort holt Amazon die Datei selbst und braucht dafür
> gerade die öffentliche Adresse.

## 🗣️ Ansagen über Alexa/Echo

Ein **Echo** kann als Ziel für die Ansagen dienen – entweder als **gesprochener
Text**, als **Audiodatei** oder als **eingebauter Alexa-Klang**.

1. **Voraussetzung:** Die (kostenlose, per HACS installierbare) Integration
   **[Alexa Media Player](https://github.com/alandtse/alexa_media_player)** muss
   eingerichtet sein und deinen Echo als `media_player`-Entity bereitstellen.
2. Diese Entity unter *MedienStop.de → Konfigurieren → Grundeinstellungen* als
   **„Video-Player"** auswählen (genau wie einen Chromecast).
3. Beim gewünschten Fall genügt **„Mitgelieferte Ansage – passend zum Gerät"**:
   MedienStop.de nimmt dann automatisch die Alexa-taugliche MP3. Alternativ:
   * **Text-Ansage** – ein frei eingegebener Satz, den Alexa vorliest.
   * **Eingebauter Alexa-Klang** – z. B. Glocke oder Türgong.
   * **Eigene Datei aus dem Ordner `www/`** – siehe
     [`media/README.md`](media/README.md) für die nötige Konvertierung.
4. Für gesprochene Ansagen muss in der Alexa-App bei diesem Gerät
   **„Communications"** aktiviert sein – sonst bleibt der Lautsprecher stumm, ohne
   Fehlermeldung in Home Assistant.

> [!NOTE]
> **Videos und Dateien aus dem Media-Browser kann ein Echo grundsätzlich nicht
> abspielen** – das liegt an Amazon, nicht an MedienStop.de. Diese Quellen werden an
> einem Echo deshalb gar nicht erst zur Auswahl gestellt.

> [!IMPORTANT]
> **Das Zielgerät muss erreichbar sein.** Steht als Fernseher oder Video-Player eine
> Entität, die gerade `unavailable` ist oder gar nicht mehr existiert, nimmt Home
> Assistant den Abspiel-Befehl klaglos entgegen – es passiert nur nichts. Der
> Test-Knopf sagt dir das seit Version 2.5.1 im Klartext. Ein bloß **ausgeschalteter**
> Fernseher ist dagegen kein Problem, den kann Home Assistant aufwecken.

## 🪝 Hooks für eigene Automatisierungen

Je Kind (und für den Elternmodus) kannst du zwei Adressen hinterlegen: eine wird
aufgerufen, sobald das Kind **anfängt** zu schauen, die andere, sobald es **aufhört**.
Damit lassen sich eigene Automatisierungen anstoßen (Licht dimmen, Nachricht aufs
Handy …).

**Mit einem Home-Assistant-Webhook verbinden:**
1. *Einstellungen → Automatisierungen → **Automatisierung erstellen*** → als Auslöser
   **Webhook** wählen. Home Assistant zeigt dir eine Adresse der Form
   `https://<deine-ha-adresse>/api/webhook/<lange-id>`.
2. Diese Adresse in MedienStop.de beim gewünschten Kind ins Feld **„Hook aktiv"**
   bzw. **„Hook inaktiv"** eintragen (am Kind-Gerät unter *Einstellungen → Geräte &
   Dienste → MedienStop.de*).

> [!NOTE]
> MedienStop.de ruft die Adresse per **POST** auf – genau das erwartet ein
> Home-Assistant-Webhook. Nur wenn das Ziel kein POST annimmt (z. B. IFTTT), wird
> automatisch auf `GET` zurückgefallen. Ob ein Aufruf geklappt hat, steht im
> Protokoll (*Einstellungen → System → Protokolle*, Filter `MedienStop.de`).

> [!WARNING]
> Die Adressen dürfen **höchstens 255 Zeichen** lang sein – das ist eine feste
> Grenze von Home Assistant. Webhook-Adressen liegen normalerweise weit darunter.

## 🩺 Fehlersuche

- **Es kommt keine Ansage?** Der schnellste Weg: *Konfigurieren → den betroffenen Fall
  wählen → Häkchen bei **„Jetzt testen"** → absenden*. Der Dialog nennt dir dann die
  Ursache im Klartext – etwa ein nicht erreichbares Zielgerät oder eine fehlende
  Alexa-Integration. (Bis Version 2.5.0 meldete der Test immer Erfolg, auch wenn nichts
  zu hören war.)
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
