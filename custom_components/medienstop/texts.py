# custom_components/medienstop/texts.py
# -----------------------------------------------------------------------------
# Laufzeit-Texte, die NICHT über translations/*.json laufen können: Fehlermeldungen
# (HomeAssistantError -> Hinweis im Dashboard), Rückmeldungen der Ansage-Weiche,
# Diagnose-Bericht und Hinweis-Benachrichtigungen. Alles zweisprachig; die Sprache
# folgt der Home-Assistant-Einstellung (en -> Englisch, sonst Deutsch) - genau wie
# der Dashboard-Generator und die Benachrichtigungen des Hub-Geräts.
#
# Aufruf: t(hass, "schluessel", name="Lukas")  ->  fertiger Text.
# Keine Abhängigkeit auf andere Module dieser Integration (importzyklenfrei).
# -----------------------------------------------------------------------------

from __future__ import annotations

_DE: dict[str, str] = {
    # --- Fehlermeldungen (erscheinen als Hinweis im Dashboard) ---------------
    "err_system_off": "MedienStop.de-System ist deaktiviert.",
    "err_meal_pause": "Essenspause aktiv – bitte warten.",
    "err_parent_time": "Elternzeit aktiv – Kinder pausiert.",
    "err_other_child": "Ein anderes Kind schaut gerade – bitte warten.",
    "err_no_time": "{name} hat keine Zeit mehr (Start nicht möglich).",
    "err_outside_window": "Außerhalb der erlaubten Zeit für {name}.",
    "err_wrong_pin": "Falscher PIN.",
    "err_unknown_child": "Unbekanntes Kind: {child}",
    "err_no_media": "Bitte eine Mediendatei auswählen oder eine URL angeben.",
    "err_not_allowed": "Nicht erlaubt: {who} darf nur den eigenen Timer bedienen ({what} gesperrt).",
    # Aktionsnamen für err_not_allowed
    "act_start": "Starten",
    "act_pause": "Pausieren",
    "act_stop": "Stoppen",
    "act_add_time": "Zeit gutschreiben",
    "act_set_pin": "PIN ändern",
    "act_apply_budgets": "Budgets anwenden",
    "act_reset_stats": "Statistik zurücksetzen",
    "act_switch": "Schalter „{name}“",
    "act_default": "diese Aktion",
    "act_for": "{action} für {name}",
    # --- Ansage-Weiche (Rückmeldungen im Test-Dialog) -------------------------
    "ann_none": "Keine Ansage eingestellt – der Fernseher geht sofort aus.",
    "ann_no_target": ("Es ist kein Ziel eingerichtet. Bitte unter Konfigurieren einen "
                      "Fernseher oder Video-Player wählen."),
    "ann_not_player": ("Das Ziel {target} ist kein media_player. Für Ansagen bitte unter "
                       "Konfigurieren einen Video-Player (media_player) wählen."),
    "ann_target_missing": ("Das eingestellte Ziel {target} gibt es nicht (mehr). Bitte unter "
                           "Konfigurieren einen vorhandenen Fernseher oder Video-Player wählen."),
    "ann_target_unavailable": ("Das Ziel {target} ist gerade nicht verfügbar (Status: {state}). "
                               "Ist das Gerät eingeschaltet und mit dem Netz verbunden? Solange es "
                               "so ist, kann keine Ansage abgespielt werden."),
    "ann_no_tts_text": "Es ist kein Ansage-Text eingetragen.",
    "ann_tts_needs_alexa": ("Eine Text-Ansage kann nur ein Alexa/Echo vorlesen. {target} ist "
                            "keins – bitte eine Video-/Audio-Vorlage wählen oder unter "
                            "Konfigurieren einen Echo als Video-Player eintragen."),
    "ann_tts_ok": "Text-Ansage an {target}: „{text}“",
    "ann_no_sound": "Es ist kein Klang ausgewählt.",
    "ann_sound_needs_alexa": ("Eingebaute Alexa-Klänge gibt es nur auf Echo-Geräten. {target} ist "
                              "keins – bitte eine andere Quelle wählen."),
    "ann_sound_ok": "Alexa-Klang „{sound}“ an {target}",
    "ann_no_file": "Es ist keine Datei aus dem Ordner www/ ausgewählt.",
    "ann_no_https": ("Home Assistant hat keine öffentliche HTTPS-Adresse. Eigene Dateien brauchen "
                     "Nabu Casa oder eine eigene Domain – sonst bitte eine mitgelieferte Vorlage "
                     "verwenden."),
    "ann_no_template": "Für diese Ansage ist keine Datei hinterlegt.",
    "ann_alexa_no_media_source": ("Alexa kann keine Dateien aus dem Media-Browser abspielen. Bitte "
                                  "eine mitgelieferte Audio-Vorlage, eine Datei aus www/ oder eine "
                                  "Text-Ansage wählen."),
    "ann_alexa_no_video": ("Alexa kann keine Videos abspielen. Bitte die passende Audio-Vorlage "
                           "(MP3) statt der Video-Vorlage wählen."),
    "ann_alexa_needs_https": ("Alexa lädt die Audiodatei selbst herunter und braucht dafür eine "
                              "öffentliche HTTPS-Adresse. Diese hier ist keine:\n{url}"),
    "ann_audio_ok": "Audio-Ansage an {target} (Alexa):\n{url}",
    "ann_play_ok": "Ansage an {target}:\n{url}",
    "ann_local_hint": "(Vorlage aus dem Heimnetz – viele Fernseher können kein HTTPS.)",
    # --- Abspiel-/Ansage-Fehler (Text + Benachrichtigung) ---------------------
    "title_video": "MedienStop.de – Video",
    "title_announce": "MedienStop.de – Ansage",
    "play_failed": ("Abspielen auf {target} fehlgeschlagen: {err}\n"
                    "Ist das die richtige (media_player-)Entität und das Gerät an?"),
    "play_failed_md": ("Abspielen auf **{target}** fehlgeschlagen:\n{err}\n\n"
                       "Ist das die richtige (media_player-)Entität und das Gerät an?"),
    "speak_no_service": ("Ansage auf {target} nicht möglich: der Service notify.alexa_media "
                         "existiert nicht. Ist die (HACS-)Integration „Alexa Media Player“ "
                         "installiert und eingerichtet?"),
    "speak_no_service_md": ("Text-Ansage auf **{target}** nicht möglich: der Service "
                            "`notify.alexa_media` existiert nicht.\n\n"
                            "Ist die (HACS-)Integration **Alexa Media Player** installiert und "
                            "eingerichtet? Ohne sie kann MedienStop.de keine Sprachansage auf "
                            "einem Alexa/Echo-Gerät abspielen."),
    "speak_failed": ("Ansage auf {target} fehlgeschlagen: {err}\n"
                     "Ist „Communications“ für dieses Gerät in der Alexa-App aktiviert? "
                     "Das wird für Ansagen (announce) benötigt."),
    "speak_failed_md": ("Text-Ansage auf **{target}** fehlgeschlagen:\n{err}\n\n"
                        "Ist „Communications“ für dieses Gerät in der Alexa-App aktiviert? "
                        "Das wird für Ansagen (announce) benötigt."),
    # --- Diagnose-Bericht ------------------------------------------------------
    "diag_emergency_1": "*** NOT-AUS: „System aktiv“ ist AUS ***",
    "diag_emergency_2": "MedienStop.de schaltet den Fernseher weder ein noch aus,",
    "diag_emergency_3": "und es wird KEINE Zeit abgezogen und KEINE Statistik gezählt.",
    "diag_system": "System aktiv:    {v}",
    "diag_parent": "Elternzeit:      {v}",
    "diag_meal": "Essenspause:     {v}",
    "diag_holiday": "Ferien heute:    {v}",
    "diag_no_tv": "(KEINE TV-Entity gewählt!)",
    "diag_entity_missing": "(Entity nicht gefunden)",
    "diag_tv_entity": "TV-Entity:       {v}",
    "diag_video_player": "Video-Player:    {v}",
    "diag_tv_raw": "TV roher Zustand:{v}",
    "diag_tv_on": "TV gilt als an:  {v}",
    "diag_daytype": "Tagtyp heute:    {v}",
    "diag_sunday_split": "{daytype} (Sonntag geteilt: Beginn Wochenende, Ende Werktag)",
    "diag_children": "Kinder:",
    "diag_child": ("  - {name}: status={status} rest={remaining}min state={state} "
                   "fenster={window} im_fenster={inw}"),
    "diag_authorized": "=> Jemand berechtigt: {v}",
    "diag_would_off": "=> TV müsste AUS sein: {v}",
    "diag_hint_system_off": "HINWEIS: „System aktiv“ ist AUS -> MedienStop schaltet nichts!",
    "diag_hint_no_tv": "HINWEIS: Keine TV-Entity gewählt -> es kann nichts geschaltet werden!",
    # --- Einrichtung -----------------------------------------------------------
    "cf_reloading": ("Die Integration wird gerade neu geladen. Bitte ein paar Sekunden warten "
                     "und noch einmal testen."),
}

_EN: dict[str, str] = {
    "err_system_off": "The MedienStop.de system is disabled.",
    "err_meal_pause": "Meal break active – please wait.",
    "err_parent_time": "Parent time active – children are paused.",
    "err_other_child": "Another child is watching right now – please wait.",
    "err_no_time": "{name} has no time left (cannot start).",
    "err_outside_window": "Outside the allowed time for {name}.",
    "err_wrong_pin": "Wrong PIN.",
    "err_unknown_child": "Unknown child: {child}",
    "err_no_media": "Please select a media file or enter a URL.",
    "err_not_allowed": "Not allowed: {who} may only operate their own timer ({what} is locked).",
    "act_start": "Start",
    "act_pause": "Pause",
    "act_stop": "Stop",
    "act_add_time": "Add time",
    "act_set_pin": "Change PIN",
    "act_apply_budgets": "Apply budgets",
    "act_reset_stats": "Reset statistics",
    "act_switch": "Switch \"{name}\"",
    "act_default": "this action",
    "act_for": "{action} for {name}",
    "ann_none": "No announcement configured – the TV turns off immediately.",
    "ann_no_target": ("No target is set up. Please choose a TV or video player under "
                      "Configure."),
    "ann_not_player": ("The target {target} is not a media_player. For announcements please "
                       "choose a video player (media_player) under Configure."),
    "ann_target_missing": ("The configured target {target} does not exist (anymore). Please "
                           "choose an existing TV or video player under Configure."),
    "ann_target_unavailable": ("The target {target} is currently unavailable (state: {state}). "
                               "Is the device switched on and connected to the network? While it "
                               "stays like this, no announcement can be played."),
    "ann_no_tts_text": "No announcement text has been entered.",
    "ann_tts_needs_alexa": ("Only an Alexa/Echo can read out a text announcement. {target} is "
                            "not one – please choose a video/audio template or set an Echo as "
                            "video player under Configure."),
    "ann_tts_ok": "Text announcement to {target}: \"{text}\"",
    "ann_no_sound": "No sound has been selected.",
    "ann_sound_needs_alexa": ("Built-in Alexa sounds only exist on Echo devices. {target} is "
                              "not one – please choose another source."),
    "ann_sound_ok": "Alexa sound \"{sound}\" to {target}",
    "ann_no_file": "No file from the www/ folder has been selected.",
    "ann_no_https": ("Home Assistant has no public HTTPS address. Your own files need Nabu Casa "
                     "or your own domain – otherwise please use a bundled template."),
    "ann_no_template": "No file is stored for this announcement.",
    "ann_alexa_no_media_source": ("Alexa cannot play files from the media browser. Please choose a "
                                  "bundled audio template, a file from www/ or a text "
                                  "announcement."),
    "ann_alexa_no_video": ("Alexa cannot play videos. Please choose the matching audio template "
                           "(MP3) instead of the video template."),
    "ann_alexa_needs_https": ("Alexa downloads the audio file itself and therefore needs a public "
                              "HTTPS address. This one is not:\n{url}"),
    "ann_audio_ok": "Audio announcement to {target} (Alexa):\n{url}",
    "ann_play_ok": "Announcement to {target}:\n{url}",
    "ann_local_hint": "(Template served from the home network – many TVs cannot handle HTTPS.)",
    "title_video": "MedienStop.de – Video",
    "title_announce": "MedienStop.de – Announcement",
    "play_failed": ("Playback on {target} failed: {err}\n"
                    "Is this the right (media_player) entity and is the device on?"),
    "play_failed_md": ("Playback on **{target}** failed:\n{err}\n\n"
                       "Is this the right (media_player) entity and is the device on?"),
    "speak_no_service": ("Announcement on {target} not possible: the service notify.alexa_media "
                         "does not exist. Is the (HACS) integration \"Alexa Media Player\" "
                         "installed and set up?"),
    "speak_no_service_md": ("Text announcement on **{target}** not possible: the service "
                            "`notify.alexa_media` does not exist.\n\n"
                            "Is the (HACS) integration **Alexa Media Player** installed and set "
                            "up? Without it MedienStop.de cannot play a voice announcement on an "
                            "Alexa/Echo device."),
    "speak_failed": ("Announcement on {target} failed: {err}\n"
                     "Is \"Communications\" enabled for this device in the Alexa app? "
                     "It is required for announcements (announce)."),
    "speak_failed_md": ("Text announcement on **{target}** failed:\n{err}\n\n"
                        "Is \"Communications\" enabled for this device in the Alexa app? "
                        "It is required for announcements (announce)."),
    "diag_emergency_1": "*** EMERGENCY STOP: \"System active\" is OFF ***",
    "diag_emergency_2": "MedienStop.de neither turns the TV on nor off,",
    "diag_emergency_3": "and NO time is deducted and NO statistics are counted.",
    "diag_system": "System active:   {v}",
    "diag_parent": "Parent time:     {v}",
    "diag_meal": "Meal break:      {v}",
    "diag_holiday": "Holiday today:   {v}",
    "diag_no_tv": "(NO TV entity selected!)",
    "diag_entity_missing": "(entity not found)",
    "diag_tv_entity": "TV entity:       {v}",
    "diag_video_player": "Video player:    {v}",
    "diag_tv_raw": "TV raw state:    {v}",
    "diag_tv_on": "TV counts as on: {v}",
    "diag_daytype": "Day type today:  {v}",
    "diag_sunday_split": "{daytype} (Sunday split: start from weekend, end from weekday)",
    "diag_children": "Children:",
    "diag_child": ("  - {name}: status={status} left={remaining}min state={state} "
                   "window={window} in_window={inw}"),
    "diag_authorized": "=> Someone authorized: {v}",
    "diag_would_off": "=> TV should be OFF: {v}",
    "diag_hint_system_off": "NOTE: \"System active\" is OFF -> MedienStop switches nothing!",
    "diag_hint_no_tv": "NOTE: No TV entity selected -> nothing can be switched!",
    "cf_reloading": ("The integration is being reloaded right now. Please wait a few seconds "
                     "and test again."),
}

TEXTS: dict[str, dict[str, str]] = {"de": _DE, "en": _EN}


def lang_of(hass) -> str:
    """„en“, wenn Home Assistant auf Englisch läuft, sonst „de“."""
    try:
        code = (hass.config.language or "de")[:2].lower()
    except Exception:  # pragma: no cover - hass noch nicht bereit
        code = "de"
    return "en" if code == "en" else "de"


def t(hass, key: str, **kw) -> str:
    """Text in der HA-Sprache; fehlende Schlüssel fallen auf Deutsch zurück."""
    table = TEXTS.get(lang_of(hass), _DE)
    text = table.get(key) or _DE.get(key) or key
    return text.format(**kw) if kw else text
