# Videos für MedienStop.de

Diese drei Videos werden vor dem Ausschalten des Fernsehers eingeblendet.
Ordne sie in *MedienStop.de → Konfigurieren → Videos* zu:

| Datei | Fall (Feld im Setup) | Wann |
|---|---|---|
| `timeup_fernsehzeit-vorbei.mp4` | **Zeit/Budget abgelaufen** (timeup) | Tages-Guthaben des Kindes ist aufgebraucht |
| `limit_schlaft-gut.mp4` | **Zeitfenster-Ende** (limit) | erlaubte Uhrzeit erreicht, z. B. 20 Uhr (Schlafenszeit) |
| `notimer_keine-tv-zeit.mp4` | **Kein Timer / außerhalb Zeit** (notimer) | TV wird ohne aktiven Timer / außerhalb der Zeit eingeschaltet |

## Installieren (beim jeweiligen Nutzer)
1. Die drei Dateien in den Home-Assistant-Ordner **`config/media/`** kopieren
   (z. B. per Samba, „File editor" oder *Medien → Hochladen*).
2. *Einstellungen → Geräte & Dienste → MedienStop.de → **Konfigurieren** → Videos*
   öffnen und je Fall die passende Datei über den **Media-Browser** auswählen
   (oder eine URL angeben). Pro Video lässt sich eine eigene Abschalt-Verzögerung
   (Sekunden) einstellen.

## Wichtig
Damit die Videos **auf dem Fernseher** laufen (und nicht im TV-Browser), sollte
als **Video-Player** ein streamfähiger `media_player` gewählt sein
(Chromecast/Cast oder DLNA Digital Media Renderer) – siehe Haupt-README.
