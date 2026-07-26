# Changelog

## Unveröffentlicht
- **i18n:** Auch die **Service-Namen und -Beschreibungen** (inkl. Feldbeschriftungen)
  folgen jetzt der Home-Assistant-Sprache – die `services`-Sektion in
  `translations/de.json`, `translations/en.json` und `strings.json`. Kommt mit dem
  nächsten gebündelten Release in HACS an.

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
