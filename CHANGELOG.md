# Changelog

## 2.7.1
> **Dashboard:** muss **nicht** neu erzeugt werden – nach dem Update reicht ein Neustart
> von Home Assistant.
- **Fix (wichtig): Der Play-Knopf erschien, obwohl gar nicht gestartet werden konnte.**
  Stand ein Kind außerhalb seiner erlaubten Zeit, zeigte das Dashboard trotzdem
  **„bereit"** und einen **Play-Knopf**. Beim Drücken kam dann „Außerhalb der erlaubten
  Zeit". Grund: Der Status prüfte das Zeitfenster nur, **während** ein Timer lief – bei
  einem ruhenden oder pausierten Kind wurde es übersehen. Jetzt steht außerhalb des
  Fensters immer **„gesperrt"**, und der Play-Knopf verschwindet von selbst.
- **Neu: Die Meldung sagt jetzt, welche Zeit gilt.** Statt „Außerhalb der erlaubten Zeit
  für Lina." heißt es „… für Lina (erlaubt 08:00-16:00 Uhr)." Damit ist sofort zu sehen,
  welches Zeitfenster gerade greift – hilfreich, wenn ein Kind einem anderen Profil
  zugeordnet ist oder der Ferien-Schalter an ist.

## 2.7.0
> **Dashboard:** muss **nicht** neu erzeugt werden – nach dem Update reicht ein Neustart
> von Home Assistant.
- **Fix (wichtig): Am Sonntagvormittag hieß es „außerhalb der erlaubten Zeit", obwohl
  Zeit da war.** Bisher zählte der Sonntag komplett als **Werktag**. Wer das
  Werktag-Zeitfenster auf „nach der Schule" gestellt hat (z. B. 16–19 Uhr), bei dem war
  der ganze Sonntagvormittag gesperrt – obwohl im Wochenend-Profil z. B. 8–23 Uhr stand.
  Das Wochenend-Fenster griff am Sonntag nie.
- **Neu: Du entscheidest, wie der Sonntag zählt.** Unter *Konfigurieren →
  Grundeinstellungen* gibt es jetzt die Auswahl **„Wie zählt der Sonntag?"**:
  * **Geteilt (neuer Standard):** so viel Zeit wie am Wochenende und der Vormittag ist
    frei – aber **Schluss wie an einem Schultag**. Gedacht für genau diesen Tag: frei,
    und trotzdem ist am Montag früh die Schule.
  * **Ganz wie Wochenende:** Sonntag ist ein Wochenendtag, auch abends.
  * **Ganz wie Werktag:** das bisherige Verhalten, falls du es so behalten willst.
  > **Was sich für dich ändert:** Ohne Zutun gilt ab jetzt „Geteilt". Am Sonntag
  > bekommt dein Kind damit das **Wochenend-Budget** und darf ab der Wochenend-Startzeit
  > schauen; Schluss ist zur **Werktags-Endzeit**. Möchtest du es genau wie vorher,
  > stelle „Ganz wie Werktag" ein.
- **Diagnose zeigt jetzt das wirklich geltende Zeitfenster** je Kind (z. B.
  `fenster=08:00-19:00`) und weist den geteilten Sonntag aus. Damit lässt sich sofort
  sehen, warum gerade gesperrt oder erlaubt ist.

## 2.6.0
> **Dashboard:** muss **nicht** neu erzeugt werden – nach dem Update reicht ein Neustart
> von Home Assistant.
- **Neu: MedienStop.de ist jetzt vollständig auf Deutsch und Englisch verfügbar.** Die
  Sprache folgt der Home-Assistant-Einstellung des Benutzers. Einrichtung, Entitäten,
  Dashboard-Vorlage und Benachrichtigungen waren bereits zweisprachig – jetzt sind es
  auch die letzten fest deutschen Texte:
  * Hinweise im Dashboard, wenn ein Start nicht möglich ist („keine Zeit mehr“,
    „Elternzeit aktiv“, „falscher PIN“, „nur der eigene Timer“ usw.).
  * Rückmeldungen beim Testen einer Ansage (fehlendes Ziel, Alexa-Hinweise, HTTPS).
  * Fehler-Benachrichtigungen beim Abspielen und der Diagnose-Bericht.
- **Neu: Englische Anleitung.** `README_EN.md` mit vollständiger Übersetzung; oben in
  beiden READMEs steht ein Sprachumschalter. Die HACS-Kurzbeschreibung ist zweisprachig.
- **Technisch:** Alle Laufzeittexte liegen zentral in `texts.py` (Schlüssel je Sprache),
  Protokoll-Ausgaben bleiben Deutsch. Für Nutzer mit Home Assistant auf Deutsch ändert
  sich nichts – Wortlaut wie bisher, nur mit echten Umlauten.

## 2.5.4
> **Dashboard:** muss **nicht** neu erzeugt werden – nach dem Update reicht ein Neustart
> von Home Assistant.
- **Fix (wichtig): Kinder konnten fremde Timer und den Elternmodus bedienen.** Die
  Tab-Sichtbarkeit im Dashboard versteckt nur die Reiter – ein Kind konnte einen
  fremden Tab per Adresse aufrufen oder den Elternzeit-Schalter über die Suche finden
  und so den Timer eines Geschwisterkinds stoppen oder sich selbst unbegrenzt Zeit
  verschaffen. MedienStop.de prüft jetzt **serverseitig**, wer eine Aktion auslöst:
  * Ein Benutzer, der unter *Sichtbarkeit* einem Kind zugeordnet ist, darf **nur den
    eigenen Timer** starten und pausieren. Fremde Kinder, die Hub-Schalter (Elternzeit,
    System aktiv, Ferien, Essenspause, Auto-Aus), Zeit gutschreiben, PIN ändern,
    Budgets anwenden und Statistik zurücksetzen werden für ihn abgelehnt – mit einer
    verständlichen Meldung im Dashboard und einem Eintrag im Protokoll.
  * Eltern-Benutzer, Home-Assistant-Administratoren, Automationen und Benutzer ohne
    Zuordnung sind wie bisher nicht eingeschränkt.
  > Voraussetzung: Unter *Konfigurieren → Sichtbarkeit* ist jedem Kind sein
  > Benutzer zugeordnet. Ohne Zuordnung gibt es keine Sperre.
- **Fix: Während der Elternzeit läuft garantiert keine Kinderzeit weiter.** Beim
  Einschalten der Elternzeit werden laufende Kinder pausiert; zusätzlich fängt die
  Minutenschleife jetzt jeden anderen Weg ab, auf dem ein Kind während der Elternzeit
  noch auf „läuft" stehen könnte – es wird pausiert, keine Minute abgezogen, nichts
  gezählt. Nach dem Ende der Elternzeit zeigt das Kind „pausiert" und kann mit Play
  weitermachen.
- **Fix: Knopf „Dashboard-Vorlage erstellen" beachtet die Einstellung „Sammel-Tab
  Kinder".** Bisher erzeugte der Knopf den Tab immer, auch wenn er unter *Sichtbarkeit*
  abgeschaltet war (der Service `medienstop.create_dashboard` war schon korrekt).

## 2.5.3
- **Neu: Sammel-Tab „Kinder" für die Eltern.** Im Dashboard gibt es jetzt einen
  zusätzlichen Tab, der die Steuerung **aller** Kinder untereinander zeigt – mit
  demselben **Play**-Knopf, den auch das Kind hat. Damit gibst du Zeit frei, ohne dich
  als Kind anmelden zu müssen. Der Tab ist **nur für die Eltern-Benutzer** sichtbar;
  die eigenen Kinder-Tabs bleiben unverändert dem jeweiligen Kind vorbehalten.
  Abschaltbar unter *Konfigurieren → Sichtbarkeit*.
  > Damit der Tab erscheint, das Dashboard einmal **neu erzeugen** (Knopf
  > „Dashboard-Vorlage erstellen" am Hub-Gerät).
- **Neu: Menüpunkt „Über & unterstützen".** Unter *Konfigurieren* ganz unten: zeigt die
  installierte Version und führt zur Anleitung, zu medienstop.de und zur
  Fehlermeldung – und enthält einen dezenten Spendenhinweis. Er erscheint nur, wenn du
  diesen Punkt selbst aufrufst, und steht sonst nirgends im Weg.

## 2.5.2
- **Fix (wichtig): Videos liefen auf vielen Fernsehern nicht.** Die mitgelieferten
  Videos wurden dem Fernseher als `https://`-Adresse übergeben – **viele Fernseher und
  DLNA-Empfänger können aber kein HTTPS**. Sie nehmen den Auftrag entgegen und tun
  dann nichts, ohne Fehlermeldung. (Nachgewiesen an einem Panasonic Viera: dieselbe
  Datei aus dem Heimnetz läuft, von GitHub nicht.) MedienStop.de legt die Vorlagen
  jetzt unter `config/www/medienstop/` ab und spielt sie **aus deinem Heimnetz** ab.
- **Neu: Vorlagen werden beim Start vorgeladen.** Der Download läuft einmalig im
  Hintergrund, sobald Home Assistant startet – nicht erst dann, wenn die Ansage
  gebraucht wird. Sonst liefe bei langsamer Leitung die Abschalt-Verzögerung ab,
  bevor das Video überhaupt zu sehen war. Der Start von Home Assistant wird dadurch
  **nicht** verzögert.
  * Nur für Fernseher/Cast – bei **Alexa** wird nichts geladen, dort braucht Amazon
    weiterhin die öffentliche Adresse.
  * Nur was gebraucht wird: eigene Dateien oder Text-Ansagen lösen keinen Download aus.
  * Klappt der Download nicht, wird wie bisher die Adresse von GitHub genutzt.
- **Fix:** Der Test zeigte die Adresse von GitHub an, obwohl in Wahrheit die Datei aus
  dem Heimnetz abgespielt wurde. Jetzt steht dort, was tatsächlich lief.

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
