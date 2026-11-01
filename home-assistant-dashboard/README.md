# Home Assistant floor-plan dashboard

A single-file HTML dashboard that shows your home's floor plan with live device states from Home Assistant. You can read sensors and control lights, switches, the AC, curtains, TVs, the speaker and the alarm. It also covers the **new kitchen smoke detector**.

- `index.html` is the dashboard (no build step, no external libraries).
- `floorplan.jpg` is the floor-plan background: your render with the old baked-in labels removed and upscaled to 2730×1536.
- `tools/clean_floorplan.py` is the script that cleaned the photo. You only need it if you want to re-process a new render.

## Features

| Area | What it does |
|---|---|
| Lights | Tap to toggle. Press and hold (or right-click) to set brightness. |
| Switches / smart plug / hood fan | Tap to toggle. |
| AC (climate) | Set the target temperature with + / −, and change the mode (off / cool / heat / …). |
| Curtains (covers) | Open, stop, close, or set a position from 0 to 100%. |
| TVs / speaker | Power, play/pause and volume. |
| Sensors | Temperature, humidity, AQI, fridge, motion and water leak, all live. |
| Security | Arm home / arm away / disarm through `alarm_control_panel`. Shows door, window and motion sensors. |
| **Kitchen smoke detector** | Shown on the plan and in its own card. When it reports smoke, the screen shows a full-screen red alarm with a 3-beep siren sound, and the browser sends a notification. It can also turn on a siren in the house (`smokeSiren`). |
| Status bar | Shows how many lights are on, with an **All off** button, plus open doors/windows, active motion, leaks and smoke. |
| Filters | Show only Lights, Sensors, Safety, or Climate & media on the plan. |
| Room tags | Each room has a name tag on the plan. A tag can also show that room's temperature and humidity. |
| Setup mode (✎) | Assign every button to your own Home Assistant entities by picking from a list, drag buttons into place, and add or delete buttons. No coding needed. |
| Demo mode | Runs with simulated data until you enter a token, so you can try it right away. |

## 1. Install it in Home Assistant (recommended)

Serving the page from Home Assistant avoids CORS and mixed http/https problems.

1. Copy `index.html` and `floorplan.jpg` (and `layout.json`, once you've made one) to `/config/www/dashboard/` on your HA machine. You can use the File editor or Samba add-on. Create the `www` folder if it doesn't exist, then restart HA once.
2. Open `http://<your-ha-ip>:8123/local/dashboard/index.html`.
3. In HA, go to **your profile → Security → Long-lived access tokens → Create token**.
4. On the dashboard, click the ⚙ (gear) icon, paste the token and click **Save & connect**. The URL is filled in for you.

Optional: add the page to the HA sidebar with **Settings → Dashboards → Add dashboard → Webpage**, using the URL above.

> Anything in `/config/www` is reachable without logging in. The page itself holds no secrets, because the token is stored only in your browser's localStorage. Still, use it only on devices you trust.

## 2. Assign the buttons to your devices (no coding)

1. Connect the dashboard to Home Assistant first (⚙ → URL + token), so it can list your real devices.
2. Click the **✎ pencil** button at the top right to turn on **setup mode**. Linked buttons get a blue dashed ring and buttons that aren't linked yet get an orange one. The bar above the plan shows how many are linked, for example "3/37 buttons linked".
3. **Click a button** to open "Assign button":
   - **Home Assistant entity:** start typing (for example `kitchen` or `light.`) and pick your device from the list. The list only shows devices that fit the button's type, with their name and current state. A green ✓ line confirms it was found.
   - **Type, name and icon** are filled in automatically from the device you pick. You can change any of them.
   - **Room** groups the device under "All devices by room".
   - **Show as a button on the floor plan:** untick it to keep the device only in the list.
   - **Delete** removes the button. Nothing changes in Home Assistant.
4. **Drag** any button or room label to move it.
5. Use **+ Device** to add a new button, and **+ Room label** to add a room name tag. A room tag can also show a temperature and humidity sensor.
6. Pick the alarm panel and weather entities in ⚙ settings.
7. Click **Done**.

Your changes are saved in this browser straight away. **To use the same layout on every phone, tablet and PC:**

1. In setup mode, click **Download layout.json**.
2. Copy `layout.json` into the same folder as `index.html` (`/config/www/dashboard/`).
3. Every browser then loads it automatically.

**Reset** forgets this browser's changes and goes back to `layout.json`, or to the built-in example if there's no `layout.json`.

Which button types work with which Home Assistant entities:

| Button type | Home Assistant entities | Tap does |
|---|---|---|
| Light | `light.*` | toggle (hold = brightness) |
| Switch / plug | `switch.*`, `input_boolean.*` | toggle |
| Fan | `fan.*` | toggle |
| TV / speaker | `media_player.*` | opens power / play / volume |
| Curtain / blind | `cover.*` | opens open / stop / close / position |
| AC / thermostat | `climate.*` | opens temperature / mode |
| Sensor reading | `sensor.*` | shows the value |
| Motion / presence | `binary_sensor.*` (motion, occupancy) | shows Motion / Clear |
| Door / window | `binary_sensor.*` (door, window, opening) | shows Open / Closed |
| Water leak | `binary_sensor.*` (moisture) | shows Dry / LEAK! |
| Smoke / gas / CO | `binary_sensor.*` (smoke, gas, carbon_monoxide) | shows Clear / SMOKE! + full-screen alarm |

Door, window, motion, leak and smoke buttons also appear in the **Doors, windows & motion** card. Once you're connected, example sensors that don't exist in your Home Assistant are hidden from that card.

### Editing by hand (optional)

The built-in example layout is the `CONFIG` block at the top of the `<script>` in `index.html`, and `layout.json` uses the same format:

```js
{ room: "Kitchen", type: "smoke", entity: "binary_sensor.kitchen_smoke_detector", label: "Smoke detector", icon: "smoke", x: 46, y: 64 },
```

- `x` / `y` are the position on the floor plan, in percent.
- `entity2` is the humidity sensor for the `climate_sensor` type.
- `plan: false` hides the device from the plan.

## 3. Add the kitchen smoke detector

1. Pair a smoke detector with HA. A Zigbee model works well (for example Aqara, Heiman or Frient through ZHA or Zigbee2MQTT). A Z-Wave or Wi-Fi model that exposes a `binary_sensor` with `device_class: smoke` also works.
2. In setup mode, click the smoke button in the kitchen and pick your detector's entity. The smoke card, the status bar and the full-screen alarm all follow that button.
3. Mount it on the ceiling, at least 3 m from the stove, so normal cooking doesn't set it off. In kitchens, a heat detector is often recommended next to the smoke detector.

The dashboard alarm works only while the page is open. **Also add this automation in HA** so you get alerted on your phone, even when the dashboard is closed:

```yaml
alias: Kitchen smoke alarm
triggers:
  - trigger: state
    entity_id: binary_sensor.kitchen_smoke_detector
    to: "on"
actions:
  - action: notify.notify            # or notify.mobile_app_<your_phone>
    data:
      title: "🔥 Smoke in the kitchen!"
      message: "Kitchen smoke detector triggered at {{ now().strftime('%H:%M') }}"
      data:
        push:
          sound:
            name: default
            critical: 1
            volume: 1.0
  - action: light.turn_on            # light the way out
    target:
      area_id: kitchen
    data:
      brightness_pct: 100
  - action: fan.turn_off             # stop the hood fan from spreading smoke
    target:
      entity_id: fan.kitchen_hood
mode: single
```

## Troubleshooting: it doesn't connect

The badge next to "My Home" tells you what's wrong:

| Badge says | What to do |
|---|---|
| **Demo mode – not connected** | No token is saved. Open ⚙, paste the token and click **Save & connect**. |
| **No Home Assistant URL** | Enter the address in ⚙, for example `http://192.168.1.10:8123`. Use the same address you type to open Home Assistant in the browser. |
| **Can't reach HA – retrying** | The address is wrong or can't be reached. Check the IP and the `:8123` port. Check that this phone or PC is on your home Wi-Fi. Check `http` vs `https`: if you open HA with `https://…`, use that here too. |
| **Invalid token** | Home Assistant rejected the token. Create a new one (your profile → Security → Long-lived access tokens) and copy **all** of it. It's a long text with two dots in it. |
| **Blocked: https page → http HA** | The dashboard was opened from an `https://` address (for example GitHub), and browsers won't let that page talk to a plain `http://` Home Assistant. Open it from Home Assistant (`/local/dashboard/index.html`) or from your PC instead. |

Never share your token in chats, screenshots or e-mails. If you did, delete it in Home Assistant and create a new one.

## How it talks to Home Assistant

It uses the official [WebSocket API](https://developers.home-assistant.io/docs/api/websocket):

- Authenticates with your long-lived token.
- Loads all states with `get_states`.
- Subscribes to `state_changed`, so every chip updates live.
- Sends commands with `call_service` (for example `light.toggle`, `light.turn_on {brightness_pct}`, `climate.set_temperature` and `cover.set_cover_position`).
- Reconnects automatically if the connection drops.
