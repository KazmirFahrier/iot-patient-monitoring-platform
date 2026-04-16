const endpoint = "/api/dashboard";
const wsUrl = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/live`;

const statsRoot = document.getElementById("stats-grid");
const deviceList = document.getElementById("device-list");
const alertFeed = document.getElementById("alert-feed");
const eventFeed = document.getElementById("event-feed");
const generatedAt = document.getElementById("generated-at");

const statCards = [
  ["Registered devices", "total_devices"],
  ["Open alerts", "active_alerts"],
  ["Critical alerts", "critical_alerts"],
  ["Avg heart rate", "average_heart_rate_bpm"],
  ["Avg SpO2", "average_spo2_percent"],
];

async function loadDashboard() {
  const response = await fetch(endpoint);
  const data = await response.json();
  renderDashboard(data);
}

function renderDashboard(data) {
  generatedAt.textContent = `Updated ${new Date(data.generated_at).toLocaleTimeString()}`;
  renderStats(data.stats);
  renderDevices(data.devices);
  renderAlerts(data.alerts);
  renderEvents(data.recent_events);

  renderSparkline("heart-rate-chart", data.vitals_trend, "heart_rate_bpm", "#50d7c7");
  renderSparkline("spo2-chart", data.vitals_trend, "spo2_percent", "#ffd166");
  renderSparkline("temp-chart", data.vitals_trend, "body_temperature_c", "#ff8fab");
  renderSparkline("room-temp-chart", data.ambient_trend, "room_temperature_c", "#7dd3fc");
  renderSparkline("humidity-chart", data.ambient_trend, "humidity_percent", "#8ecae6");
  renderSparkline("pressure-chart", data.ambient_trend, "pressure_hpa", "#b8f2e6");
}

function renderStats(stats) {
  statsRoot.innerHTML = statCards
    .map(([label, key]) => {
      const value = stats[key];
      const pretty =
        typeof value === "number" ? (Number.isInteger(value) ? value : value.toFixed(1)) : "n/a";
      return `
        <article class="stat-card">
          <div class="stat-label">${label}</div>
          <div class="stat-value">${pretty}</div>
        </article>
      `;
    })
    .join("");
}

function renderDevices(devices) {
  if (!devices.length) {
    deviceList.innerHTML = `<p class="empty">No devices registered yet.</p>`;
    return;
  }

  deviceList.innerHTML = devices
    .map(
      (device) => `
        <article class="device-card">
          <header>
            <div>
              <div class="device-type">${device.type.replaceAll("_", " ")}</div>
              <strong>${device.name}</strong>
            </div>
            <span class="device-meta">${device.location_label || "No location label"}</span>
          </header>
          <div class="device-meta">Key: ${device.device_key}</div>
          <div class="device-meta">Patient: ${device.patient_name || "Unassigned"}</div>
          <div class="device-meta">Last seen: ${device.last_seen_at ? new Date(device.last_seen_at).toLocaleString() : "Never"}</div>
        </article>
      `,
    )
    .join("");
}

function renderAlerts(alerts) {
  if (!alerts.length) {
    alertFeed.innerHTML = `<p class="empty">No alerts have been raised yet.</p>`;
    return;
  }

  alertFeed.innerHTML = alerts
    .map(
      (alert) => `
        <article class="feed-item">
          <header>
            <strong>${alert.title}</strong>
            <span class="severity severity-${alert.severity}">${alert.severity}</span>
          </header>
          <div>${alert.message}</div>
          <div class="alert-meta">${alert.device_name} • ${new Date(alert.created_at).toLocaleString()}</div>
        </article>
      `,
    )
    .join("");
}

function renderEvents(events) {
  if (!events.length) {
    eventFeed.innerHTML = `<p class="empty">No telemetry has arrived yet.</p>`;
    return;
  }

  eventFeed.innerHTML = events
    .map(
      (event) => `
        <article class="feed-item">
          <header>
            <strong>${event.device_name}</strong>
            <span class="device-type">${event.category}</span>
          </header>
          <div>${formatPayload(event.payload)}</div>
          <div class="event-meta">${new Date(event.recorded_at).toLocaleString()}</div>
        </article>
      `,
    )
    .join("");
}

function formatPayload(payload) {
  const entries = Object.entries(payload)
    .filter(([key]) => !["device_key", "recorded_at"].includes(key))
    .slice(0, 5)
    .map(([key, value]) => `${labelize(key)}: ${value}`);
  return entries.join(" • ");
}

function labelize(value) {
  return value.replaceAll("_", " ");
}

function renderSparkline(elementId, points, key, color) {
  const root = document.getElementById(elementId);
  const values = points.map((point) => point[key]).filter((value) => typeof value === "number");
  if (!values.length) {
    root.innerHTML = `<p class="empty">Waiting for ${labelize(key)} samples.</p>`;
    return;
  }

  const width = 320;
  const height = 128;
  const padding = 14;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = (width - padding * 2) / Math.max(values.length - 1, 1);

  const path = values
    .map((value, index) => {
      const x = padding + index * step;
      const y = height - padding - ((value - min) / range) * (height - padding * 2);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  root.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${labelize(key)} trend">
      <defs>
        <linearGradient id="${elementId}-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="${color}" stop-opacity="0.55"></stop>
          <stop offset="100%" stop-color="${color}" stop-opacity="0.02"></stop>
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="${width}" height="${height}" rx="18" fill="rgba(255,255,255,0.02)"></rect>
      <path d="${path}" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round"></path>
      <text x="${padding}" y="${padding}" fill="#9fbfd6" font-size="12">Min ${min.toFixed(1)}</text>
      <text x="${width - 80}" y="${padding}" fill="#9fbfd6" font-size="12">Max ${max.toFixed(1)}</text>
      <text x="${padding}" y="${height - 12}" fill="${color}" font-size="13">${values[values.length - 1].toFixed(1)} latest</text>
    </svg>
  `;
}

function connectSocket() {
  const socket = new WebSocket(wsUrl);
  socket.onmessage = () => loadDashboard().catch(console.error);
  socket.onclose = () => setTimeout(connectSocket, 1500);
}

loadDashboard().catch(console.error);
connectSocket();
