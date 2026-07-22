# MedienStop – Dashboards als Blaupause

Home Assistant erlaubt es einer Integration **nicht**, Dashboards automatisch
anzulegen. Deshalb bekommst du hier wiederverwendbare Blaupausen, die für
**beliebig viele Kinder/Profile** funktionieren – egal ob 1, 3 oder 8 Kinder.

Du hast drei Wege (vom bequemsten zum manuellsten):

## Weg 1 – Generator (empfohlen, passt sich jeder Anzahl an)
Erzeugt ein komplettes Dashboard (Eltern- + Kinder-Ansicht) für deine Anzahl:

```
python3 tools/generate_dashboard.py --children 3 --profiles 2 > mein_dashboard.yaml
```

Dann in HA: *Einstellungen → Dashboards → Dashboard hinzufügen →* beim neuen
Dashboard oben rechts die drei Punkte → *Raw-Konfigurationseditor* → Inhalt
einfügen. Fertig.

> Du musst das nicht selbst ausführen – sag mir einfach „generier mir das
> Dashboard für 3 Kinder und 2 Profile", dann liefere ich dir das fertige YAML.

Fertige Beispiele liegen schon bei:
- `beispiel_4kinder_1profil.yaml`
- `beispiel_2kinder_2profile.yaml`

## Weg 2 – Bausteine kopieren (ohne Generator)
- `blaupause_pro_kind.yaml` – eine Steuer-Karte für **ein** Kind. So oft kopieren
  wie du Kinder hast und `kind_1` → `kind_2`, `kind_3` … ersetzen.
- `blaupause_pro_profil.yaml` – eine Einstellungs-Karte für **ein** Profil
  (`profil_1` → `profil_2` …).

Diese Karten unter `cards:` deines Dashboards einfügen.

## Weg 3 – Automatisch mit HACS (skaliert von selbst)
`kinder_AUTO_hacs.yaml` nutzt die HACS-Karte **auto-entities** und listet ohne
Zutun alle Kinder auf – egal wie viele. Play/Pause-Buttons bleiben pro Kind über
Weg 1/2, weil Buttons mit Service-Aufruf nicht automatisch erzeugt werden können.

---

## Wichtig: dem Kind einen Namen geben
Jedes Kind ist ein eigenes **Gerät**. Unter *Einstellungen → Geräte → „Kind 1"*
kannst du das Gerät umbenennen (z. B. in „Max"). Dann heißen alle zugehörigen
Anzeigen automatisch „Max Restzeit", „Max Status" usw. Die internen IDs
(`kind_1`) bleiben gleich, deine Dashboards funktionieren also weiter.

## Tabs, Sichtbarkeit & Namen (neu)
Die generierten Dashboards haben **pro Kind und pro Profil einen eigenen Tab**:
- Über *Tab bearbeiten → Sichtbarkeit* legst du je Tab fest, welcher HA-Benutzer
  ihn sieht. So sieht jedes Kind nur seinen eigenen Tab und kann keine fremde Zeit
  starten.
- Die Tab-Titel sind die **Gerätenamen**. Benenne „Kind 1"/„Profil 1" unter
  *Einstellungen → Geräte* um und drücke dann den Button „Dashboard-Vorlage
  erstellen" erneut – die neue Vorlage trägt die neuen Namen.
- Im Kinder-Tab gibt es bewusst **kein Stop** und kein Start bei Restzeit 0.
