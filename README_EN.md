🇩🇪 [Deutsche Version](README.md) · 🇬🇧 English

<div align="center">

# 📺 MedienStop.de
### Screen-time control for Home Assistant

**A side project of [MedienStop.de](https://medienstop.de) – the parental-control guide that parents actually understand.**

[![Home Assistant][ha-badge]][ha] [![HACS][hacs-badge]][hacs] [![Release][release-badge]][releases] [![License: MIT][mit-badge]][mit] [![Website][web-badge]][website] [![Donate][donate-badge]][donate]

[Website](https://medienstop.de) · [Installation](#-installation) · [Setup](#-setup) · [Dashboard](#-dashboard-setup) · [Announcements](#-shutdown-announcements) · [Alexa/Echo](#️-announcements-via-alexaecho) · [Hooks](#-hooks-for-your-own-automations) · [Troubleshooting](#-troubleshooting) · [❤️ Donate][donate]

</div>

---

## About MedienStop.de

**[MedienStop.de](https://medienstop.de)** helps parents make their **children's
digital home safe, one step at a time** – explained in plain language, without
tech jargon, "like a chat over coffee in the living room". It offers more than 20
free **step-by-step guides** (FRITZ!Box & Wi-Fi, phones & tablets, consoles,
computers, TV & streaming, apps & games) – all **available as audio, too** –, the
guided parent dashboard **Eltern-SOC** and the workbook **Familien-Fahrplan**.
Please note: the website and its content are in **German**.

## What is this project?

This **Home Assistant integration** is a **side project** of MedienStop.de – for
families who run **Home Assistant** at home and want to **automate their children's
screen time**. It manages a daily budget and allowed time windows per child, counts
the time down and switches the TV off automatically when time is up – optionally
with a short **goodbye announcement** as video or audio ("Your time is up" /
"Sleep well" / "It's not TV time right now"). A small, technical building block of
the bigger MedienStop idea.

> [!NOTE]
> **New to Home Assistant?** Home Assistant is a free smart-home hub that you run
> yourself. This integration is an add-on for it. If you don't use Home Assistant
> (yet), the best place to start is
> [MedienStop.de](https://medienstop.de) – no technology required there (German only).

## ✨ Features

- **Profiles** with a budget (minutes) and time window per day type **weekday /
  weekend / holidays**. Children are assigned to profiles.
- **"School night" logic**: weekend = Friday + Saturday. **Sunday** is configurable
  (*Configure → Basics*): **split** by default – as much time as on the weekend, but
  bedtime as on a school day. Alternatively entirely as weekend or entirely as weekday.
- **Nightly reset (midnight)** to the daily budget – survives restarts.
- **Automatic TV shutdown**: checks every 15 s whether the TV is being watched
  although no time/no timer is active – and switches it off if so.
- **Play / Pause / Stop** per child, only one child at a time, no start at 0 minutes.
- **Parent mode** (override, survives restarts), **Meal break** (hard off),
  **Holiday switch**, **Parent time auto-off** at a fixed time of day.
- **Shutdown announcements as video _or_ audio** for "time is up", "bedtime" and
  "no TV time" – each with its own delay, selectable via the media browser,
  streamable via Cast/DLNA.
- **Statistics** per child: watched today / this week / this month / this year.
- **Reset statistics** – per child or for all (button on the device/hub or
  service `medienstop.reset_statistics`).
- **Webhooks (hooks)** per child and for parent mode – for your own automations
  (see [Hooks](#-hooks-for-your-own-automations)).
- **Tab visibility per user** (children only see their own tab), survives updates.
- **Dashboard generator** at the push of a button + **diagnostic tools**.

## 📸 Screenshots

![Overview: integration, budgets, controls and shutdown announcements](https://raw.githubusercontent.com/SammyMedienStop/HA_MedienStop/main/docs/screenshots/00_uebersicht.png)

| Budgets & time windows | Video/audio announcements |
|---|---|
| ![Budgets & time windows](https://raw.githubusercontent.com/SammyMedienStop/HA_MedienStop/main/docs/screenshots/01_budgets-zeitfenster.png) | ![Video/audio announcements](https://raw.githubusercontent.com/SammyMedienStop/HA_MedienStop/main/docs/screenshots/10_videos-audio.png) |

More screenshots in the folder [`docs/screenshots/`](docs/screenshots/).

## ✅ Requirements

- Home Assistant **2024.4** or newer.
- A switchable entity acting as the "TV" (smart plug/`switch`, `media_player` …).
- For videos/audio: a **stream-capable** `media_player` (Chromecast/Cast **or**
  DLNA Digital Media Renderer). For pure **audio** announcements, a **speaker**
  (e.g. Google Nest/Cast speaker) is sufficient.

## 📦 Installation

> [!TIP]
> **What is HACS?** The [Home Assistant Community Store (HACS)](https://hacs.xyz/)
> is an "app store" for add-ons. It lets you install MedienStop.de with a few
> clicks and shows you when updates are available. The one-time HACS setup is
> described at [hacs.xyz](https://hacs.xyz/).

### Option A – HACS (recommended)
1. In HACS, click **⋮ → Custom repositories** in the top right.
2. Repository: `https://github.com/SammyMedienStop/HA_MedienStop`
   – Category: **Integration**. Click **Add**.
3. Search for "MedienStop.de", **install** it, **restart** Home Assistant.

### Option B – Manual (without HACS)
1. Download the file `medienstop-x.y.z.zip` from the [latest release][releases]
   and unpack it. It contains **one** folder named `medienstop`.
2. Copy this `medienstop` folder into the `custom_components` folder of your
   Home Assistant configuration so that exactly this path results:

   ```
   config/custom_components/medienstop/manifest.json
   ```

   Create the `custom_components` folder yourself first if needed. It sits next to
   your `configuration.yaml` – reachable e.g. via the add-on *Samba share*, *Studio
   Code Server* or *File editor*.
3. **Restart** Home Assistant.

> [!TIP]
> You can check whether it worked under *Settings → Devices & services →
> **Add integration***: "MedienStop.de" must now show up there. If it doesn't, the
> path is usually wrong – the most common mistake is one folder too deep,
> i.e. `custom_components/medienstop/medienstop/`.

## 🚀 Setup

*Settings → Devices & services → **Add integration** → "MedienStop.de".*

The wizard guides you step by step:
1. **Number of children & profiles**, optionally **TV** and **video player entity**.
2. **Names** for children and profiles.
3. **Visibility**: which HA user(s) see the parent tabs and the respective
   child's tab.
4. **Dashboard variant**.

You choose the announcements played before switching off afterwards under
*MedienStop.de → **Configure*** – there is one menu entry per case
(see [Shutdown announcements](#-shutdown-announcements)).

## 🖥️ Dashboard setup

The integration generates a **ready-made dashboard** as a template for you – no
need to build anything by hand. Here's how, beginner-friendly:

1. **Generate the template:** Open *Settings → Devices & services → **MedienStop.de***
   and there the hub device. Press the button **"Create dashboard template"**.
   *(Alternatively: Developer tools → Actions → `medienstop.create_dashboard`
   → **Perform action**.)*
2. **Open the template:** A **notification** appears. Click **"Notifications"** in
   the bottom left of Home Assistant and open the entry
   **"MedienStop.de – Dashboard template"**.
3. **Copy the text:** Select the entire text in the grey **code box** (that is
   the YAML) and copy it (**Ctrl + C**).
4. **Create a new dashboard:** *Settings → **Dashboards** → top right
   **"Add dashboard"** → **"New dashboard from scratch"** → choose a name
   (e.g. "MedienStop") and icon → **"Create"***.
5. **Open the raw configuration editor:** Open the new dashboard. Click the
   **pencil icon (Edit)** in the top right and confirm the notice. Then, top right,
   **⋮ menu → "Raw configuration editor"**.
6. **Paste & save:** Delete the existing content completely, paste the copied
   text (**Ctrl + V**) and click **"Save"**. Close the editor via the **✕** in the
   top left.
7. **Done!** Your tabs (parents, children, statistics if applicable) are there. If
   you rename children or profiles later, simply press **"Create dashboard
   template"** again and repeat the steps.

> [!NOTE]
> Who sees which tab is already baked into the template – you defined that in the
> setup wizard under **Visibility**. The assignment also acts as a
> **safeguard**: a user assigned to a child can only start and pause their own
> timer – not the siblings' timers, not Parent time and no other parent
> functions. Not even when opening a hidden tab directly via its address.

### 👨‍👩‍👧 The "Children" tab for parents

Next to the parent tab there is a **"Children"** tab that shows the controls of
**all** children one below the other – with the same **Play** button the child sees.
Handy when you want to release time in between without signing in as a child.

The tab is visible **only to the parent users**; the individual children's tabs
remain reserved for the respective child. You can turn it off under
*Configure → **Visibility*** – then generate the dashboard once more.

## 🎬 Shutdown announcements

Shortly before switching off, an announcement is played. There are three cases,
each with its own source and its own delay:

| Case | When | Bundled template |
|---|---|---|
| **Time is up** | daily budget used up | "TV time is over" |
| **Bedtime** | allowed end time reached (e.g. 8 pm) | "Sleep well" |
| **No TV time** | TV started outside the time window / without a timer | "No TV time" |

### ✅ Easiest way: keep "Bundled announcement"

You need to **download nothing, copy nothing and know nothing about file formats**:

1. *Settings → Devices & services → **MedienStop.de** → **Configure***.
2. Pick the entry for the desired case, e.g. **"Announcement: time/budget
   used up"**.
3. Under **"Announcement source"**, **"Bundled announcement – matched to your
   device"** is already selected. That is the default and almost always exactly right.
4. Tick **"Test now – do not save yet"** and submit: the announcement is played
   immediately, **without** saving anything. The dialog then tells you what
   happened – and, in case of a problem, **why** it failed. If everything is fine,
   untick the box and submit again; only then is it saved.

> [!TIP]
> **Why "matched to your device"?** MedienStop.de picks the file itself: a
> **video** for the TV, an **audio file** for an Echo – plus the announcement that
> fits the occasion. If you change the target device later, the announcement
> follows automatically. You can still pin a specific template if you prefer.

You are also **only offered sources that work on your device**:
On an Echo the video templates don't even appear, on a TV no spoken text. An
impossible combination therefore cannot be configured.

Each case is saved **individually**; the other two announcements and all other
settings remain untouched.

### 📥 Using your own files

Instead of the templates you can also use your own announcements. If you choose one
of these sources, the dialog asks **for exactly the one matching entry in the next
step** – you never see fields you don't need.

| Source | What for |
|---|---|
| **Your own file from the media browser** | TV/Chromecast. Copy the file to `…/config/media/` and select it in the browser. **Not possible for Alexa** (and not offered there). |
| **Your own file from the `www/` folder** | Also for **Alexa** – put the file in `…/config/www/`, MedienStop.de builds the internet address itself. You pick from a list of existing files, so no typos are possible. |
| **Your own URL** | Any address on the internet. |
| **Spoken text** | Alexa reads out a freely entered sentence (only on an Echo). |
| **Built-in Alexa sound** | Bell, doorbell chime etc. directly from Amazon (only on an Echo). |
| **No announcement** | TV switches off immediately. |

> [!IMPORTANT]
> **Your own audio files for Alexa must be converted.** Amazon only accepts MP3 in
> one very specific format – if it doesn't match, the Echo stays **silent, without
> an error message**. The complete guide including a ready-to-use command is in
> **[`media/README.md`](media/README.md)**. The bundled audio templates are
> already prepared accordingly.

**Testing:** On the hub device there is a separate test button for **each of the
three cases**. Alternatively use the action `medienstop.test_video`
(Developer tools → Actions).

> [!WARNING]
> **Screen stays black or the browser opens?** (Panasonic, Samsung, LG,
> Android TV) → These TVs accept the play command but do not actually stream.
> Select a **Cast/Chromecast** or your TV's **DLNA renderer** as the
> **"Video player"**. Note: the DLNA entry often only appears in Home Assistant
> **once the TV is switched on**. For pure **audio** announcements a speaker is
> sufficient as the target.

> [!NOTE]
> **Why are videos stored in `config/www/medienstop/`?** Many TVs and DLNA
> receivers cannot handle `https://` addresses and then stay silent.
> MedienStop.de therefore fetches the bundled templates **once** into your home
> network when Home Assistant starts (around 30 MB for the three videos) and plays
> them from there via `http://`. This runs in the background and does not delay
> startup. Nothing is downloaded for **Alexa** – there Amazon fetches the file
> itself and needs the public address for exactly that.

## 🗣️ Announcements via Alexa/Echo

An **Echo** can serve as the target for the announcements – either as **spoken
text**, as an **audio file** or as a **built-in Alexa sound**.

1. **Prerequisite:** The (free, HACS-installable) integration
   **[Alexa Media Player](https://github.com/alandtse/alexa_media_player)** must be
   set up and expose your Echo as a `media_player` entity.
2. Select this entity under *MedienStop.de → Configure → Basics* as the
   **"Video player"** (exactly like a Chromecast).
3. For the desired case, **"Bundled announcement – matched to your device"** is
   enough: MedienStop.de then automatically uses the Alexa-compatible MP3. Alternatively:
   * **Spoken text** – a freely entered sentence that Alexa reads out.
   * **Built-in Alexa sound** – e.g. bell or doorbell chime.
   * **Your own file from the `www/` folder** – see
     [`media/README.md`](media/README.md) for the required conversion.
4. For spoken announcements, **"Communications"** must be enabled for this device
   in the Alexa app – otherwise the speaker stays silent, without an error message
   in Home Assistant.

> [!NOTE]
> **An Echo fundamentally cannot play videos or files from the media browser** –
> that is down to Amazon, not MedienStop.de. These sources are therefore not even
> offered for selection on an Echo.

> [!IMPORTANT]
> **The target device must be reachable.** If the TV or video player is set to an
> entity that is currently `unavailable` or no longer exists at all, Home
> Assistant accepts the play command without complaint – nothing just happens. Since
> version 2.5.1 the test button tells you this in plain words. A TV that is merely
> **switched off**, on the other hand, is no problem – Home Assistant can wake it up.

## 🪝 Hooks for your own automations

Per child (and for parent mode) you can store two addresses: one is called as soon
as the child **starts** watching, the other as soon as they **stop**.
This lets you trigger your own automations (dim the lights, send a message to your
phone …).

**Connecting to a Home Assistant webhook:**
1. *Settings → Automations & scenes → **Create automation*** → choose **Webhook**
   as the trigger. Home Assistant shows you an address of the form
   `https://<your-ha-address>/api/webhook/<long-id>`.
2. Enter this address in MedienStop.de for the desired child in the field
   **"Hook active"** or **"Hook inactive"** (on the child device under *Settings →
   Devices & services → MedienStop.de*).

> [!NOTE]
> MedienStop.de calls the address via **POST** – exactly what a Home Assistant
> webhook expects. Only if the target does not accept POST (e.g. IFTTT) does it
> automatically fall back to `GET`. Whether a call succeeded is shown in the
> log (*Settings → System → Logs*, filter `MedienStop.de`).

> [!WARNING]
> The addresses may be **at most 255 characters** long – that is a fixed limit
> of Home Assistant. Webhook addresses are normally well below that.

## 🩺 Troubleshooting

- **No announcement is played?** The quickest way: *Configure → pick the affected
  case → tick **"Test now"** → submit*. The dialog then tells you the cause in
  plain words – such as an unreachable target device or a missing Alexa
  integration. (Up to version 2.5.0 the test always reported success, even when
  nothing could be heard.)
- **Diagnostics button** on the hub → notification with the complete state.
- Sensor **"Last check"** must tick ~every 15 s (otherwise the logic isn't running →
  restart Home Assistant).
- Diagnostic lines appear as **WARNING** in the log (*Settings → System →
  Logs*, filter: `MedienStop.de`).

## 🤝 Contributing & support

Ideas, bugs or wishes? Feel free to report them as an [issue][issues].
All about media education & child protection (in German): **[MedienStop.de](https://medienstop.de)**.

## ❤️ Support the project

If MedienStop.de helps you, I'd be glad about a small donation – it keeps the
project alive:

👉 **[Donate via PayPal](https://www.paypal.com/donate/?hosted_button_id=JN23TQFMSX5EU)**

## 📄 License

Released under the **[MIT License](LICENSE)**.

---

<div align="center">
Made with ❤️ for more relaxed TV evenings · <a href="https://medienstop.de">MedienStop.de</a>
</div>

[ha]: https://www.home-assistant.io/
[hacs]: https://hacs.xyz/
[website]: https://medienstop.de
[releases]: https://github.com/SammyMedienStop/HA_MedienStop/releases
[issues]: https://github.com/SammyMedienStop/HA_MedienStop/issues
[mit]: LICENSE
[ha-badge]: https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=homeassistant&logoColor=white
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[release-badge]: https://img.shields.io/github/v/release/SammyMedienStop/HA_MedienStop?display_name=tag
[mit-badge]: https://img.shields.io/badge/License-MIT-green.svg
[web-badge]: https://img.shields.io/badge/Web-MedienStop.de-ff7f0e
[donate]: https://www.paypal.com/donate/?hosted_button_id=JN23TQFMSX5EU
[donate-badge]: https://img.shields.io/badge/PayPal-Spenden-00457C?logo=paypal&logoColor=white
