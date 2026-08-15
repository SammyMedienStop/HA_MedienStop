# Ansagen für MedienStop.de

Diese Dateien werden vor dem Ausschalten des Fernsehers abgespielt. Es gibt drei
Fälle, jeweils als **Video** (`.mp4`, für Fernseher/Chromecast) und als **Audio**
(`.mp3`, zusätzlich **Alexa/Echo-tauglich**):

| Fall (Feld im Setup) | Wann | Video | Audio |
|---|---|---|---|
| **Zeit/Budget abgelaufen** (timeup) | Tages-Guthaben des Kindes ist aufgebraucht | `timeup_fernsehzeit-vorbei.mp4` | `timeup_fernsehzeit-vorbei.mp3` |
| **Zeitfenster-Ende** (limit) | erlaubte Uhrzeit erreicht, z. B. 20 Uhr | `limit_schlaft-gut.mp4` | `limit_schlaft-gut.mp3` |
| **Kein Timer / außerhalb Zeit** (notimer) | TV ohne aktiven Timer eingeschaltet | `notimer_keine-tv-zeit.mp4` | `notimer_keine-tv-zeit.mp3` |

> [!TIP]
> **Du musst diese Dateien nicht selbst herunterladen.** In *MedienStop.de →
> Konfigurieren* stehen sie als fertige **Vorlagen** im Auswahlfeld – sie werden
> direkt aus diesem GitHub-Repository geladen. Nur wer **eigene** Ansagen nutzen
> will, braucht die Anleitung weiter unten.

---

## 🔊 Eigene Audios für Alexa/Echo vorbereiten

Ein Echo kann **nicht** einfach jede beliebige MP3 abspielen. Amazon holt die Datei
selbst aus dem Internet und prüft dabei **streng** ihr Format. Passt etwas nicht,
bleibt der Lautsprecher **stumm – ohne jede Fehlermeldung** in Home Assistant. Genau
deshalb müssen eigene Dateien konvertiert werden.

### Amazons Anforderungen (alle Punkte müssen stimmen)

| Anforderung | Wert | Warum |
|---|---|---|
| **Dateiformat** | MP3, **MPEG Version 2** | **WAV, OGG, M4A und FLAC funktionieren nicht.** MPEG Version 2 ergibt sich automatisch aus der Samplerate (siehe unten). |
| **Bitrate** | genau **48 kbps**, konstant (CBR) | Variable Bitrate (VBR) wird abgelehnt. |
| **Samplerate** | **16000, 22050 oder 24000 Hz** | Nur diese drei. Üblich sind 44100/48000 Hz – die gehen **nicht**. |
| **Länge** | höchstens **240 Sekunden** | Pro Ansage. |
| **Erreichbarkeit** | öffentliches **HTTPS** mit gültigem Zertifikat | Amazons Server lädt die Datei selbst. Selbstsignierte Zertifikate werden abgelehnt. |

### Womit konvertieren?

| Werkzeug | Für wen | Bemerkung |
|---|---|---|
| **ffmpeg** (empfohlen) | alle, die einen Befehl eintippen können | Trifft **alle** Vorgaben in einem Rutsch, auch die heiklen (keine ID3-Daten, kein Xing-Header). Anleitung direkt unten. |
| **Audacity** | wer lieber klickt | Kostenloses Programm mit Oberfläche. Funktioniert, erfordert aber drei Einstellungen von Hand – siehe [weiter unten](#alternative-ohne-kommandozeile-audacity). |
| Online-Konverter | – | **Nicht empfohlen.** Die meisten liefern variable Bitrate oder 44100 Hz und schreiben ID3-Daten hinein; das Ergebnis bleibt dann stumm, ohne dass man den Grund sieht. |

**ffmpeg installieren:**

```bash
# Windows (PowerShell)
winget install Gyan.FFmpeg

# macOS
brew install ffmpeg

# Debian/Ubuntu, auch im HA-Terminal-Add-on
sudo apt install ffmpeg
```

### Konvertieren mit ffmpeg

[ffmpeg](https://ffmpeg.org/) ist kostenlos und für Windows, macOS und Linux
verfügbar. Ein Befehl je Datei:

```bash
ffmpeg -i meine-ansage.mp3 -map_metadata -1 -id3v2_version 0 \
       -codec:a libmp3lame -b:a 48k -ar 24000 -ac 1 -write_xing 0 \
       fertig.mp3
```

Was die einzelnen Angaben bewirken:

| Angabe | Bedeutung |
|---|---|
| `-ar 24000` | Samplerate 24 kHz. **Dadurch entsteht automatisch MPEG Version 2** – LAME schaltet bei 16/22,05/24 kHz selbst um. |
| `-b:a 48k` | konstante Bitrate von 48 kbps. |
| `-ac 1` | Mono. Bei 48 kbps klingt Stereo matschig; Amazons eigene Beispiele sind mono. |
| `-map_metadata -1` und `-id3v2_version 0` | entfernt alle Titel-/Cover-Informationen (ID3). Ein ID3-Block vor dem ersten Ton ist eine bekannte Fehlerquelle beim Abruf durch Amazon. |
| `-write_xing 0` | schreibt keinen zusätzlichen Info-Block an den Dateianfang. |

Läuft es rückwärts? Also aus einem **Video** eine Ansage machen: derselbe Befehl
funktioniert auch mit einer `.mp4` als Eingabedatei – die Tonspur wird übernommen.

### Ergebnis prüfen

```bash
ffprobe -v error -show_entries stream=sample_rate,channels,bit_rate \
        -show_entries format=duration -of default=noprint_wrappers=1 fertig.mp3
```

Erwartet: `sample_rate=24000`, `channels=1`, `bit_rate=48000`, `duration` ≤ 240.

> [!NOTE]
> Die mitgelieferten `.mp3` in diesem Ordner sind bereits exakt so konvertiert
> (MPEG 2 · 48 kbps · 24000 Hz · Mono · ohne ID3) und damit sofort Alexa-tauglich.

### Alternative ohne Kommandozeile: Audacity

[Audacity](https://www.audacityteam.org/) ist kostenlos und hat eine normale
Programmoberfläche. Es sind drei Schritte nötig – die Voreinstellungen des Programms
erfüllen Amazons Vorgaben **nicht**:

1. Datei öffnen. Unten links **Projektfrequenz** auf **24000** stellen.
2. Menü **Spuren → Mix → Stereo in Mono umwandeln** (falls die Aufnahme stereo ist).
3. **Datei → Exportieren → Als MP3 exportieren.** Im Export-Fenster:
   * **Bitratenmodus: Konstant**
   * **Qualität: 48 kbps**
   * **Kanäle: Mono**
   * Die Felder für **Titel, Künstler, Album** allesamt **leer** lassen (das sind die
     ID3-Daten, die beim Abruf durch Amazon Ärger machen).

Danach mit dem `ffprobe`-Befehl von oben gegenprüfen – oder einfach im Ansage-Dialog
auf **„Jetzt testen"** klicken. Bleibt es stumm, stimmt am Format noch etwas nicht.

---

## 📍 Wo muss die eigene Datei liegen?

Amazons Server lädt die Datei **selbst aus dem Internet**. Sie muss deshalb von
außen über **HTTPS** erreichbar sein – eine Datei, die nur im Heimnetz liegt,
funktioniert nicht.

**Der richtige Ort ist der Ordner `www` in deiner Home-Assistant-Konfiguration:**

1. Datei nach `config/www/` kopieren (Ordner ggf. anlegen), z. B.
   `config/www/meine-ansage.mp3`.
2. Sie ist dann unter `https://<deine-ha-adresse>/local/meine-ansage.mp3` abrufbar.
3. In *MedienStop.de → Konfigurieren* die Quelle **„Eigene Datei aus www/"** wählen –
   die vollständige Adresse wird automatisch gebildet.

Voraussetzung ist ein **öffentlich erreichbarer HTTPS-Zugang** mit gültigem
Zertifikat, z. B. **Nabu Casa** (Home Assistant Cloud) oder eine eigene Domain mit
Let's-Encrypt-Zertifikat.

> [!WARNING]
> **Der Media-Browser funktioniert für Alexa nicht.** Dateien aus `config/media/`
> werden nur mit einem Zugangs-Token ausgeliefert, das Amazons Server nicht hat.
> Für Alexa führt der Weg deshalb ausschließlich über `config/www/` (oder eine
> eigene öffentliche URL). Für **Fernseher und Chromecast** ist der Media-Browser
> weiterhin der richtige und bequemste Weg.

> [!CAUTION]
> Alles in `config/www/` ist **ohne Passwort** aus dem Internet abrufbar, sobald
> jemand die Adresse kennt. Dort also nur Dateien ablegen, die unbedenklich sind –
> Sprachansagen für Kinder sind das typischerweise.

---

## 🖥️ Für Fernseher und Chromecast

Damit die **Videos** auf dem Fernseher laufen (und nicht im TV-Browser landen),
sollte als **Video-Player** ein streamfähiger `media_player` gewählt sein –
Chromecast/Cast oder ein DLNA Digital Media Renderer. Details im
[Haupt-README](../README.md).

---

## ⚠️ Für Entwickler: Dateinamen nicht ändern

Die Dateinamen und Pfade in diesem Ordner sind in
`custom_components/medienstop/const.py` fest verdrahtet und werden über
`raw.githubusercontent.com` **direkt von Amazons Servern abgerufen**. Eine Umbenennung
oder Verschiebung bricht die Vorlagen-Auswahl in allen bestehenden Installationen.
Die URLs zeigen bewusst auf den Branch `main`, damit spätere Korrekturen an den
Ansagen auch ältere Installationen erreichen.
