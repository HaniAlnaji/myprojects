# Home Assistant floor-plan dashboard

A single-file HTML dashboard that shows your home's floor plan with live device states from Home Assistant. You can read sensors and control lights, switches, the AC, curtains, TVs, the speaker and the alarm. It also covers the **new kitchen smoke detector**.

- `index.html` is the dashboard (no build step, no external libraries).
- `floorplan.jpg` is the floor-plan background.

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
| Demo mode | Runs with simulated data until you enter a token, so you can try it right away. |

## 1. Install it in Home Assistant (recommended)

Serving the page from Home Assistant avoids CORS and mixed http/https problems.

1. Copy `index.html` and `floorplan.jpg` to `/config/www/dashboard/` on your HA machine. You can use the File editor or Samba add-on. Create the `www` folder if it doesn't exist, then restart HA once.
2. Open `http://<your-ha-ip>:8123/local/dashboard/index.html`.
3. In HA, go to **your profile → Security → Long-lived access tokens → Create token**.
4. On the dashboard, click the ⚙ (gear) icon, paste the token and click **Save & connect**. The URL is filled in for you.

Optional: add the page to the HA sidebar with **Settings → Dashboards → Add dashboard → Webpage**, using the URL above.

> Anything in `/config/www` is reachable without logging in. The page itself holds no secrets, because the token is stored only in your browser's localStorage. Still, use it only on devices you trust.

## 2. Map your entities

Open `index.html` and edit the `CONFIG` block at the top of the `<script>`. Change each `entity` to your real entity_id. You can find these under **Settings → Devices & services → Entities**.

```js
{ room: "Kitchen", type: "smoke", entity: "binary_sensor.kitchen_smoke_detector", label: "Smoke detector", icon: "smoke", x: 44.0, y: 67.5 },
```

- `type` is one of `light`, `switch`, `fan`, `media`, `cover`, `climate`, `sensor`, `climate_sensor` (temperature + `entity2` humidity), `motion`, `leak` or `smoke`.
- `x` / `y` set the position on the floor plan, in percent.
- If an entity isn't found in HA, its chip is drawn **dashed with "N/A"**, so you can see what still needs mapping.
- `alarmPanel`, `weather`, `smokeDetector` and `securitySensors` are set in the same block.

## 3. Add the kitchen smoke detector

1. Pair a smoke detector with HA. A Zigbee model works well (for example Aqara, Heiman or Frient through ZHA or Zigbee2MQTT). A Z-Wave or Wi-Fi model that exposes a `binary_sensor` with `device_class: smoke` also works.
2. Rename its entity to `binary_sensor.kitchen_smoke_detector`, or put your entity_id in `CONFIG.smokeDetector` and in the kitchen `smoke` device.
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

## How it talks to Home Assistant

It uses the official [WebSocket API](https://developers.home-assistant.io/docs/api/websocket):

- Authenticates with your long-lived token.
- Loads all states with `get_states`.
- Subscribes to `state_changed`, so every chip updates live.
- Sends commands with `call_service` (for example `light.toggle`, `light.turn_on {brightness_pct}`, `climate.set_temperature` and `cover.set_cover_position`).
- Reconnects automatically if the connection drops.
