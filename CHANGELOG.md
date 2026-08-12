# Changelog

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
