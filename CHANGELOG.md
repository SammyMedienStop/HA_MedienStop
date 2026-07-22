# Changelog

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
