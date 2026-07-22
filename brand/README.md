# MedienStop.de – Logo (Home Assistant Brands)

Home Assistant lädt Integrations-Logos aus dem offiziellen Repo
`home-assistant/brands` – auch für **eigene** Integrationen (Ordner
`custom_integrations/`). Lokale Bilder im Integrationsordner zeigt HA NICHT an.

## Dateien hier
- `icon.png` (256×256) und `icon@2x.png` (512×512) – das quadratische Icon
- `logo.png` / `logo@2x.png` – optionales Logo (hier = Icon)

(Werden mit `tools/make_brand_icons.py` aus deinem Bären erzeugt.)

## So wird das Logo in HA sichtbar
1. Repo `home-assistant/brands` auf GitHub forken.
2. Ordner anlegen: `custom_integrations/medienstop/`
3. `icon.png` und `icon@2x.png` (und optional `logo.png`/`logo@2x.png`) hineinlegen.
4. Pull Request erstellen. Nach dem Merge erscheint das Logo automatisch unter
   *Einstellungen → Geräte & Dienste → MedienStop.de* (HA holt es von
   `brands.home-assistant.io`).

Hinweis: Bis der PR gemerged ist, zeigt HA ein neutrales Standard-Icon – die
Integration funktioniert davon unabhängig vollständig.
