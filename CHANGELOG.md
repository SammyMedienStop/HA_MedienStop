# Changelog

## 2.5.1
- **Fix (wichtig): Ansagen auf Alexa blieben stumm.** Die Audiodatei wurde ohne den
  vorgeschriebenen `<speak>`-Rahmen an Alexa geschickt – Amazon verwarf sie dann
  kommentarlos. Jetzt kommt die Ansage an. Zusätzlich werden Sonderzeichen in der
  Adresse korrekt maskiert.
- **Fix (wichtig): „Jetzt testen" meldete immer Erfolg.** Der Test startete die
  Wiedergabe nur im Hintergrund und meldete sofort „läuft", ohne das Ergebnis
  abzuwarten. Ein fehlender Dienst, ein ausgeschaltetes Gerät oder ein stummer Echo
  blieben dadurch **völlig unsichtbar**. Jetzt wartet der Test das Ergebnis ab und
  zeigt im Dialog, was wirklich passiert ist.
- **Fix: Ein totes Zielgerät fällt jetzt auf.** War als Fernseher oder Video-Player
  ein Gerät eingetragen, das es nicht mehr gibt oder das gerade nicht erreichbar ist,
  passierte einfach nichts. Jetzt steht es im Klartext im Dialog.
- **Neu: „Mitgelieferte Ansage" wählt die Datei selbst.** Die neue Standard-Einstellung
  nimmt automatisch die richtige Vorlage – ein **Video** für den Fernseher, eine
  **Audiodatei** für Alexa, passend zum jeweiligen Anlass. Du musst nicht mehr wissen,
  was dein Gerät kann; ein späterer Gerätewechsel zieht von allein nach.
- **Neu: Es werden nur noch Quellen angeboten, die auch funktionieren.** An einem Echo
  gibt es keine Video-Vorlagen mehr zur Auswahl, an einem Fernseher keine Text-Ansage.
  Damit lässt sich die Kombination gar nicht mehr falsch einstellen.
- **Neu: Der Ansage-Dialog fragt nur noch, was gebraucht wird.** Statt acht Feldern auf
  einmal kommt zuerst nur die Auswahl der Quelle – und **nur bei eigenen Dateien** ein
  zweiter Schritt mit genau dem einen passenden Feld. Bei den mitgelieferten Ansagen
  ist nach der Auswahl Schluss.
- **Geändert:** Die Alexa-Klänge stehen jetzt mit Klartext-Namen in der Liste
  („Türgong" statt `amzn_sfx_doorbell_chime_01`), und bei der Dateiauswahl aus `www/`
  ist keine freie Eingabe mehr möglich – nur noch wirklich vorhandene Dateien.

## 2.5.0
- **Neu: Mitgelieferte Ansagen zum Anklicken.** In *Konfigurieren → Ansage …* gibt es
  jetzt **eine Auswahlliste** mit den fertigen MedienStop-Ansagen – je Fall als
  **Video** (für Fernseher/Chromecast) und als **Audio** (auch für Alexa). Du musst
  **nichts mehr herunterladen und nichts mehr in den Medien-Ordner kopieren** – ein
  Klick genügt.
- **Neu: Eigene MP3 auf Alexa/Echo.** MedienStop.de kann Audiodateien jetzt auch auf
  einem Echo abspielen. Die mitgelieferten Audios sind dafür passend aufbereitet.
  Für **eigene** Dateien gelten Amazons strenge Formatvorgaben – die komplette
  Anleitung zum Konvertieren steht in [`media/README.md`](media/README.md).
- **Neu: Jede Ansage einzeln änderbar.** Die Einstellungen sind jetzt ein **Menü**:
  Du änderst gezielt *eine* Ansage, ohne dich durch Kinderzahl, Namen und
  Sichtbarkeit klicken zu müssen – und ohne die beiden anderen Ansagen anzufassen.
- **Neu: Testen vor dem Speichern.** Im Ansage-Formular gibt es das Feld
  **„Jetzt testen – noch nicht speichern"**. Damit hörst du dir die Ansage sofort an;
  gespeichert wird erst, wenn du das Häkchen wieder entfernst und absendest.
  Zusätzlich gibt es jetzt am Hub-Gerät **je einen Test-Knopf für alle drei Fälle**
  (vorher nur für „Zeit abgelaufen").
- **Neu:** Eingebaute **Alexa-Klänge** (Glocke, Türgong …) als Ansage wählbar.
- **Fix:** Ein einmal gesetztes Video ließ sich **nicht mehr entfernen** – jetzt geht
  das über die Auswahl „Keine Ansage – sofort ausschalten".
- **Fix:** Eine Verzögerung von **0 Sekunden** wurde stillschweigend auf 10 gesetzt.
- **Fix:** Beim Verringern der Kinderzahl gingen die **Namen** der entfallenen Kinder
  verloren. Sie bleiben jetzt erhalten und sind wieder da, wenn du die Anzahl
  erhöhst.
- **Fix:** Beim Speichern wurde die Integration zweimal neu geladen.
- Deine **bestehenden Videos und Einstellungen bleiben unverändert** und funktionieren
  weiter wie bisher – es ist keine Anpassung nötig.

## 2.4.1
- **Fix (wichtig): Die Überwachung blieb irgendwann stehen.** Sobald man die
  **Auto-Aus-Zeit** der Elternzeit verstellt oder den Schalter „Elternzeit Auto-Aus"
  umgelegt hatte, hörte die 15-Sekunden-Prüfung dauerhaft auf zu arbeiten: Der
  Fernseher wurde nicht mehr abgeschaltet, der Sensor **„Letzte Prüfung"** fror ein
  und die Hooks feuerten nicht mehr. Das war die gemeinsame Ursache für gleich
  mehrere gemeldete Fehler.
- **Fix: „System aktiv" ist jetzt ein echter Not-Aus.** Ist der Schalter aus, rührt
  MedienStop.de den Fernseher **gar nicht mehr an** – auch eine bereits laufende
  Abschalt-Verzögerung wird sofort abgebrochen (vorher schaltete sie den Fernseher
  trotzdem ab). Außerdem läuft in dieser Zeit **keine Statistik** mit: Restzeit und
  „Heute geschaut" bleiben stehen, bis das System wieder eingeschaltet wird.
- **Fix: Hooks lösen jetzt wirklich aus.** Die Hook-URLs wurden per `GET` aufgerufen –
  Home-Assistant-Webhooks nehmen aber nur `POST` an und lehnten den Aufruf still ab.
  Jetzt wird `POST` verwendet (mit `GET` als Rückfall für Dienste wie IFTTT), und
  **Erfolg wie Fehler stehen im Protokoll** (Filter: `MedienStop.de`) – vorher war
  überhaupt nichts zu sehen.
- **Fix:** Nach einem Neustart von Home Assistant wurde fälschlich ein
  „Elternzeit aktiv"-Hook ausgelöst. Beim ersten Durchlauf wird der Zustand jetzt nur
  noch abgeglichen, ohne zu feuern.
- Kein Neu-Erzeugen des Dashboards nötig – die Fixes wirken nach dem Update sofort.

## 2.4.0
- **Neu: Text-Ansage statt Video/Audio-Datei** (z. B. für Alexa/Echo-Lautsprecher).
  Unter *Konfigurieren → Videos* gibt es je Grund (Zeit/Budget abgelaufen,
  Zeitfenster-Ende, kein Timer) jetzt zusätzlich ein Feld „…oder Text-Ansage" –
  der eingetragene Text wird direkt über Amazons Sprachausgabe vorgelesen, es muss
  keine Audio-/Videodatei mehr gehostet/ausgewählt werden. Dafür wird die separate
  (HACS-)Integration **Alexa Media Player** benötigt; ist sie installiert, reicht es,
  im „Video-Player"-Feld die Alexa-Geräte-Entity auszuwählen. Ist eine Text-Ansage
  gesetzt, hat sie Vorrang vor einem eingestellten Video/einer URL für denselben
  Grund. Der bestehende Media-Browser zeigt bei Alexa-Geräten weiterhin „Mediaplayer
  unterstützt kein Auswählen aus Medienquellen" – das ist eine Einschränkung der
  Alexa-Integration selbst (kein `browse_media`), keine Einschränkung von
  MedienStop.de.

## 2.3.3
- **Fix:** Am gemeinsamen Fernseher kann jetzt wirklich nur **ein Kind gleichzeitig**
  schauen. Solange ein Kind läuft, zeigen die anderen **„belegt"** an und der
  **Play-/Fortsetzen-Knopf verschwindet** aus ihrem Kind-Dashboard (vorher blieb er
  bei pausierten Kindern sichtbar, obwohl der Start ohnehin blockiert war). Sobald der
  Fernseher frei ist, können pausierte Kinder wie gewohnt fortsetzen.
- Kein Neu-Erzeugen des Dashboards nötig – der Fix wirkt nach dem Update sofort.

## 2.3.2
- **Verbessert:** Die **Reset-Knöpfe im Statistik-Tab** sind jetzt kompakte
  Pillen-Buttons im Karten-Footer (Stil wie „+15/+30/Stop") statt großer Kacheln –
  je Kind einer, jeweils mit Sicherheitsabfrage.
- **Geändert:** „Statistik ALLE zurücksetzen" gibt es nur noch auf der
  **Geräte-/Integrationsseite** (bei Diagnose, Video-Test usw.), nicht mehr im
  Dashboard.
- **Neu:** Die Reset-Knöpfe **auf der Geräteseite** haben jetzt eine
  **Sicherheitsabfrage** – 1× drücken stellt scharf und warnt, erst der 2. Druck
  innerhalb von 15 Sekunden setzt wirklich zurück (Entity-Buttons haben keinen
  eingebauten Bestätigungsdialog).
- **i18n:** Auch die **Service-Namen und -Beschreibungen** (inkl. Feldbeschriftungen)
  folgen jetzt der Home-Assistant-Sprache.
- Nach dem Update einmal **„Dashboard-Vorlage erstellen"** drücken und die neue
  Vorlage einfügen, damit der kompakte Reset erscheint.

## 2.3.1
- **Neu:** Auch die **Dashboard-Vorlage** und die **Benachrichtigungen**
  (Dashboard-Erstellung, Diagnose, Video-Test) folgen jetzt der Home-Assistant-Sprache
  – Tabs, Karten, Knöpfe, Diagramm-Titel und Sicherheitsabfragen erscheinen auf
  **Englisch**, wenn die Sprache auf English steht, sonst auf **Deutsch**.
- Nach dem Update einmal **„Dashboard-Vorlage erstellen"** drücken und die neue Vorlage
  einfügen, damit die übersetzten Beschriftungen erscheinen.

## 2.3.0
- **Neu: Englischer Modus / English mode.** Die Integration folgt jetzt der
  eingestellten Home-Assistant-Sprache **je Benutzer** (Profil → Sprache → English)
  – kein separater Schalter nötig. Übersetzt sind der **Einrichtungs-Assistent** und
  **alle Entitätsnamen** (Deutsch/Englisch). Jedes Familienmitglied kann so seine
  eigene Sprache nutzen.
- (Folgt in einem kleinen Update: Beschriftungen der Dashboard-Vorlage und der
  Benachrichtigungen ebenfalls sprachabhängig.)

## 2.2.0
- **Neu:** Elternzeit-Statistik – Minuten mit aktiver Elternzeit (Heute / Woche /
  Monat / Jahr) als eigene Sensoren am Hub, inkl. eigener Karte im Statistik-Tab.
- **Neu:** Balken-Diagramm „Fernsehzeit pro Tag" im Statistik-Tab (nutzt die
  Home-Assistant-Langzeitstatistik; füllt sich über die Zeit).
- Der Reset „Statistik ALLE zurücksetzen" schließt die Elternzeit-Statistik mit ein.

## 2.1.1
- **Neu:** Reset-Knöpfe direkt im **Statistik-Tab** der Dashboard-Vorlage – je Kind
  und „Statistik ALLE zurücksetzen", jeweils mit **Sicherheitsabfrage**. Dashboard
  nach dem Update einmal neu erzeugen (Knopf „Dashboard-Vorlage erstellen").

## 2.1.0
- **Neu:** Statistik zurücksetzen – per Knopf am jeweiligen Kind-Gerät, per
  „Statistik ALLE zurücksetzen"-Knopf am Hub oder per Service
  `medienstop.reset_statistics` (Kind wählbar oder alle; Umfang: alles / nur
  Heute / Woche / Monat / Jahr).
- **Fix:** Integrations-Icon wird jetzt angezeigt – die Brand-Bilder liegen nun im
  Integrationsordner (`custom_components/medienstop/brand/`), wie es Home Assistant
  ab 2026.3 für Custom-Integrationen unterstützt.

## 2.0.2
- **Fix:** Bei Erreichen des Zeitfenster-Endes (z. B. 20 Uhr) wird jetzt korrekt
  das **„Zeitfenster-Ende / Schlafenszeit"-Video (limit)** gezeigt – vorher hat die
  15-Sekunden-Prüfung immer das „kein Timer"-Video (notimer) ausgelöst.
- Grund-Erkennung (timeup / limit / notimer) in Minuten-Loop und 15-Sekunden-Prüfung
  vereinheitlicht (`_scan`). Kind wird bei Fensterende pausiert, damit spätere
  TV-Starts korrekt als „notimer" gelten.

## 2.0.1
- **Fix:** Restzeit bleibt über einen Neustart erhalten. Bisher wurde beim Start
  die Restzeit auf die Standard-Budgets gesetzt, bevor die gespeicherten Werte
  wiederhergestellt waren – dadurch bekam ein Kind nach einem (auch ungewollten)
  Neustart z. B. 60 statt der eingestellten 90 Minuten.
- Budgets werden erst nach dem Wiederherstellen angewendet (nur für Kinder ohne
  gespeicherte Restzeit / Neuinstallation).

## 2.0.0
- Profile mit Budget + Zeitfenster (Werktag/Wochenende/Ferien), Schulnacht-Logik.
- Automatische TV-Abschaltung (15-s-Prüfung), Play/Pause/Stop, „nur ein Kind".
- Elternmodus (neustartfest), Essenspause, Ferien-Schalter, Elternzeit-Auto-Aus.
- Videos vor dem Ausschalten (timeup/limit/notimer) mit eigener Verzögerung,
  Media-Browser-Auswahl, separater Video-Player (Cast/DLNA), Test-Buttons.
- Statistik je Kind (Tag/Woche/Monat/Jahr), Webhooks (pro Kind + Elternmodus).
- Tab-Sichtbarkeit je Benutzer (persistent), Dashboard-Generator, Diagnose &
  Heartbeat, WARNING-Diagnose-Logs.
