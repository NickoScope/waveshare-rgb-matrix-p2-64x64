// mtr1-radar-card: a live floor plan of the Apollo MTR-1's HLK-LD2450 radar for a
// Home Assistant dashboard. The sensor sits at the bottom centre and looks up the
// screen; the fan is the module's 6 m range and ±60° field of view (Hi-Link,
// KB docs/16-presence-radar.md, source 1). Each of the three targets is drawn at
// its X/Y with a fading trail kept in the card; zones are drawn when the device's
// Zone Type is not "Disabled". Colours come from the HA theme.
//
// Usage:  type: custom:mtr1-radar-card
//         device: apollo_mtr_1_53bc60      # the entity id stem
//         title: Гостиная                  # optional
//         trail_s: 15                      # optional, seconds of trail
//         range_m: 6                       # optional, radius drawn (the module reaches 6 m)
//         mirror_x: false                  # optional, flip left and right

const HALF_FOV = (60 * Math.PI) / 180;
const TARGET_COLOURS = ["#20b8d8", "#e89a1c", "#d6508c"];

class Mtr1RadarCard extends HTMLElement {
  static getStubConfig() {
    return { device: "apollo_mtr_1_53bc60" };
  }

  setConfig(config) {
    if (!config || !config.device) throw new Error("Set device: the entity id stem, e.g. apollo_mtr_1_53bc60");
    this._cfg = { title: "Радар", trail_s: 15, range_m: 6, mirror_x: false, ...config };
    this._cfg.range_m = Math.min(6, Math.max(1, Number(this._cfg.range_m) || 6));
    this._trails = [[], [], []];
    if (!this.shadowRoot) this._build();
  }

  getCardSize() {
    return 7;
  }

  getGridOptions() {
    return { columns: 12, rows: "auto", min_columns: 6 };
  }

  _build() {
    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        ha-card { padding: 12px 16px 14px; }
        .head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 12px; margin-bottom: 8px; }
        .title { font-size: 1.05rem; font-weight: 600; color: var(--primary-text-color); margin-right: auto; }
        .chip { font-size: 0.8rem; padding: 2px 9px; border-radius: 999px; background: var(--secondary-background-color);
                color: var(--secondary-text-color); font-variant-numeric: tabular-nums; white-space: nowrap; }
        .chip.on { background: color-mix(in srgb, var(--primary-color) 22%, transparent); color: var(--primary-text-color); }
        .wrap { position: relative; width: 100%; aspect-ratio: 1.732 / 1.08; }
        canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
        .rows { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 6px 14px; margin-top: 8px; }
        .row { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: var(--secondary-text-color);
               font-variant-numeric: tabular-nums; }
        .dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
        .row b { color: var(--primary-text-color); font-weight: 600; }
        .off { opacity: 0.45; }
      </style>
      <ha-card>
        <div class="head"><span class="title"></span><span class="chips"></span></div>
        <div class="wrap"><canvas></canvas></div>
        <div class="rows"></div>
      </ha-card>`;
    this._canvas = root.querySelector("canvas");
    this._wrap = root.querySelector(".wrap");
    this._titleEl = root.querySelector(".title");
    this._chipsEl = root.querySelector(".chips");
    this._rowsEl = root.querySelector(".rows");
    this._ro = new ResizeObserver(() => this._draw());
    this._ro.observe(this._wrap);
  }

  connectedCallback() {
    // Trails fade between state updates, which arrive about once a second.
    this._timer = setInterval(() => {
      if (!document.hidden) this._draw();
    }, 200);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  set hass(hass) {
    this._hass = hass;
    const now = Date.now();
    const keep = this._cfg.trail_s * 1000;
    for (let i = 1; i <= 3; i++) {
      const t = this._target(i);
      const trail = this._trails[i - 1];
      const last = trail[trail.length - 1];
      if (t && (!last || last.x !== t.x || last.y !== t.y)) trail.push({ x: t.x, y: t.y, ts: now });
      while (trail.length && now - trail[0].ts > keep) trail.shift();
    }
    this._renderText();
    this._draw();
  }

  _id(domain, name) {
    return `${domain}.${this._cfg.device}_${name}`;
  }

  _state(domain, name) {
    const s = this._hass && this._hass.states[this._id(domain, name)];
    return s ? s.state : undefined;
  }

  _num(domain, name) {
    const v = parseFloat(this._state(domain, name));
    return Number.isFinite(v) ? v : null;
  }

  _target(i) {
    const x = this._num("sensor", `target_${i}_x`);
    const y = this._num("sensor", `target_${i}_y`);
    if (x === null || y === null || (x === 0 && y === 0)) return null;
    return {
      x,
      y,
      speed: this._num("sensor", `target_${i}_speed`),
      distance: Math.hypot(x, y),
      angle: (Math.atan2(x, y) * 180) / Math.PI,
      direction: this._state("sensor", `target_${i}_direction`),
    };
  }

  _renderText() {
    if (!this._hass) return;
    this._titleEl.textContent = this._cfg.title;
    const present = this._state("binary_sensor", "ld2450_presence") === "on";
    const count = this._num("sensor", "presence_target_count") ?? 0;
    const moving = this._num("sensor", "moving_target_count") ?? 0;
    const still = this._num("sensor", "still_target_count") ?? 0;
    const lux = this._num("sensor", "ltr390_light");
    const online = this._state("binary_sensor", "online") !== "off";
    const chips = [
      [online ? (present ? "Кто-то есть" : "Никого") : "Нет связи", present && online],
      [`Людей: ${count}`, count > 0],
      [`Движутся: ${moving}`, moving > 0],
      [`Стоят: ${still}`, still > 0],
    ];
    if (lux !== null) chips.push([`${Math.round(lux)} лк`, false]);
    this._chipsEl.innerHTML = chips
      .map(([text, on]) => `<span class="chip${on ? " on" : ""}">${text}</span>`)
      .join(" ");
    const rows = [];
    for (let i = 1; i <= 3; i++) {
      const t = this._target(i);
      const colour = TARGET_COLOURS[i - 1];
      rows.push(
        t
          ? `<div class="row"><span class="dot" style="background:${colour}"></span><span>Цель ${i}: <b>${(t.distance / 1000).toFixed(2)} м</b>, ${Math.round(t.angle)}°, ${Math.round(Math.abs(t.speed ?? 0) / 10)} см/с${t.direction ? `, ${t.direction}` : ""}</span></div>`
          : `<div class="row off"><span class="dot" style="background:${colour}"></span><span>Цель ${i}: нет</span></div>`
      );
    }
    this._rowsEl.innerHTML = rows.join("");
  }

  _draw() {
    if (!this._canvas || !this._hass) return;
    const cssW = this._wrap.clientWidth;
    const cssH = this._wrap.clientHeight;
    if (!cssW || !cssH) return;
    const dpr = window.devicePixelRatio || 1;
    if (this._canvas.width !== Math.round(cssW * dpr) || this._canvas.height !== Math.round(cssH * dpr)) {
      this._canvas.width = Math.round(cssW * dpr);
      this._canvas.height = Math.round(cssH * dpr);
    }
    const ctx = this._canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    const css = getComputedStyle(this);
    const ink = css.getPropertyValue("--primary-text-color").trim() || "#212121";
    const muted = css.getPropertyValue("--secondary-text-color").trim() || "#727272";
    const accent = css.getPropertyValue("--primary-color").trim() || "#03a9f4";

    // Sensor at the bottom centre; range_m reaches the top with room for labels.
    const RANGE_MM = this._cfg.range_m * 1000;
    const pad = 18;
    const scale = Math.min((cssW - 2 * pad) / (2 * RANGE_MM * Math.sin(HALF_FOV)), (cssH - 2 * pad) / RANGE_MM);
    const ox = cssW / 2;
    const oy = cssH - pad;
    const mx = this._cfg.mirror_x ? -1 : 1;
    const px = (x) => ox + mx * x * scale;
    const py = (y) => oy - y * scale;
    const start = -Math.PI / 2 - HALF_FOV;
    const end = -Math.PI / 2 + HALF_FOV;

    // The fan.
    ctx.beginPath();
    ctx.moveTo(ox, oy);
    ctx.arc(ox, oy, RANGE_MM * scale, start, end);
    ctx.closePath();
    ctx.globalAlpha = 0.1;
    ctx.fillStyle = accent;
    ctx.fill();
    ctx.globalAlpha = 0.55;
    ctx.strokeStyle = accent;
    ctx.lineWidth = 1.2;
    ctx.stroke();

    // Rings every metre, spokes every 30°.
    ctx.globalAlpha = 0.28;
    ctx.strokeStyle = muted;
    ctx.lineWidth = 1;
    for (let m = 1; m < this._cfg.range_m; m++) {
      ctx.beginPath();
      ctx.arc(ox, oy, m * 1000 * scale, start, end);
      ctx.stroke();
    }
    for (const deg of [-30, 0, 30]) {
      const a = -Math.PI / 2 + (deg * Math.PI) / 180;
      ctx.beginPath();
      ctx.moveTo(ox, oy);
      ctx.lineTo(ox + Math.cos(a) * RANGE_MM * scale, oy + Math.sin(a) * RANGE_MM * scale);
      ctx.stroke();
    }
    ctx.globalAlpha = 0.8;
    ctx.fillStyle = muted;
    ctx.font = "11px system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    for (let m = 1; m <= Math.floor(this._cfg.range_m); m++) {
      const a = end;
      ctx.fillText(`${m} м`, ox + Math.cos(a) * m * 1000 * scale + 4, oy + Math.sin(a) * m * 1000 * scale);
    }

    // Zones, when the device uses them.
    const zoneType = this._state("select", "zone_type");
    if (zoneType && zoneType !== "Disabled") {
      for (let z = 1; z <= 3; z++) {
        const x1 = this._num("number", `zone_${z}_x1`);
        const y1 = this._num("number", `zone_${z}_y1`);
        const x2 = this._num("number", `zone_${z}_x2`);
        const y2 = this._num("number", `zone_${z}_y2`);
        if ([x1, y1, x2, y2].some((v) => v === null) || (x1 === x2 && y1 === y2)) continue;
        const occupied = (this._num("sensor", `zone_${z}_all_target_count`) ?? 0) > 0;
        const left = Math.min(px(x1), px(x2));
        const top = Math.min(py(y1), py(y2));
        const w = Math.abs(px(x2) - px(x1));
        const h = Math.abs(py(y2) - py(y1));
        ctx.globalAlpha = occupied ? 0.22 : 0.08;
        ctx.fillStyle = zoneType === "Filter" ? muted : accent;
        ctx.fillRect(left, top, w, h);
        ctx.globalAlpha = 0.7;
        ctx.setLineDash([5, 4]);
        ctx.strokeStyle = zoneType === "Filter" ? muted : accent;
        ctx.strokeRect(left, top, w, h);
        ctx.setLineDash([]);
        ctx.fillStyle = ink;
        ctx.fillText(`Зона ${z}`, left + 5, top + 10);
      }
    }

    // The sensor.
    ctx.globalAlpha = 1;
    ctx.fillStyle = ink;
    ctx.fillRect(ox - 9, oy, 18, 5);

    // Trails, then the targets on top.
    const now = Date.now();
    const keep = this._cfg.trail_s * 1000;
    this._trails.forEach((trail, idx) => {
      const colour = TARGET_COLOURS[idx];
      for (let k = 1; k < trail.length; k++) {
        const age = (now - trail[k].ts) / keep;
        if (age >= 1) continue;
        ctx.globalAlpha = 0.6 * (1 - age);
        ctx.strokeStyle = colour;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(px(trail[k - 1].x), py(trail[k - 1].y));
        ctx.lineTo(px(trail[k].x), py(trail[k].y));
        ctx.stroke();
      }
    });
    for (let i = 1; i <= 3; i++) {
      const t = this._target(i);
      if (!t) continue;
      const colour = TARGET_COLOURS[i - 1];
      const cx = px(t.x);
      const cy = py(t.y);
      const moving = Math.abs(t.speed ?? 0) / 10 > 12;   // cm/s: the panel's room_radar threshold, so both call the same person still
      ctx.globalAlpha = 0.25;
      ctx.fillStyle = colour;
      ctx.beginPath();
      ctx.arc(cx, cy, moving ? 16 : 13, 0, 2 * Math.PI);
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.beginPath();
      ctx.arc(cx, cy, 7, 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 10px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(String(i), cx, cy + 0.5);
    }
    ctx.globalAlpha = 1;
  }
}

if (!customElements.get("mtr1-radar-card")) {
  customElements.define("mtr1-radar-card", Mtr1RadarCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "mtr1-radar-card",
    name: "MTR-1 radar",
    description: "Live floor plan of the Apollo MTR-1 LD2450 targets, trails and zones",
  });
}
