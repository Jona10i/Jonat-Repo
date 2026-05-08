const { app, BrowserWindow, Tray, Menu, screen, ipcMain, dialog, nativeImage } = require("electron");
const fs = require("node:fs");
const path = require("node:path");
const { Bonjour } = require("bonjour-service");

let mainWindow;
let tray;
let discoveredServerUrl = "http://localhost:4010";
let browser;
let bonjour;
const discoveredServers = new Map();
let discoverySweepTimer;
const DISCOVERY_STALE_MS = 30000;

const configDir = path.join(app.getPath("userData"), "config");
const configPath = path.join(configDir, "settings.json");

function readSettings() {
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }
  if (!fs.existsSync(configPath)) {
    return {};
  }
  try {
    return JSON.parse(fs.readFileSync(configPath, "utf-8"));
  } catch {
    return {};
  }
}

function writeSettings(settings) {
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }
  fs.writeFileSync(configPath, JSON.stringify(settings, null, 2));
}

function toServerSummary(service) {
  const host = service.referer?.address || service.addresses?.find((a) => a.includes(".")) || service.host;
  if (!host || !service.port) {
    return null;
  }
  const id = `${service.fqdn || service.name}-${service.port}`;
  return {
    id,
    name: service.name || "Office LAN Comm",
    host,
    port: service.port,
    url: `http://${host}:${service.port}`,
    lastSeenAt: new Date().toISOString()
  };
}

function getDiscoveredServerList() {
  return Array.from(discoveredServers.values()).sort((a, b) => {
    if (a.url === discoveredServerUrl) return -1;
    if (b.url === discoveredServerUrl) return 1;
    return a.name.localeCompare(b.name);
  });
}

function pickFallbackServerUrl() {
  const first = Array.from(discoveredServers.values())[0];
  return first?.url ?? "http://localhost:4010";
}

function ensureSelectedServerAvailable() {
  if (discoveredServerUrl === "http://localhost:4010") {
    return;
  }
  const hasSelected = Array.from(discoveredServers.values()).some((server) => server.url === discoveredServerUrl);
  if (hasSelected) {
    return;
  }
  discoveredServerUrl = pickFallbackServerUrl();
  const next = { ...readSettings(), preferredServerUrl: discoveredServerUrl };
  writeSettings(next);
}

function pruneStaleServers() {
  const now = Date.now();
  let changed = false;
  for (const [id, server] of discoveredServers.entries()) {
    const age = now - new Date(server.lastSeenAt).getTime();
    if (age > DISCOVERY_STALE_MS) {
      discoveredServers.delete(id);
      changed = true;
    }
  }
  if (changed) {
    ensureSelectedServerAvailable();
    pushDiscoveryUpdate();
  }
}

function pushDiscoveryUpdate() {
  if (!mainWindow?.webContents) {
    return;
  }
  mainWindow.webContents.send("server:list", getDiscoveredServerList());
  mainWindow.webContents.send("server:url", discoveredServerUrl);
}

function getDockBounds() {
  const display = screen.getPrimaryDisplay();
  const width = 420;
  return {
    x: display.workArea.x + display.workArea.width - width,
    y: display.workArea.y,
    width,
    height: display.workArea.height
  };
}

function createWindow() {
  const bounds = getDockBounds();
  mainWindow = new BrowserWindow({
    ...bounds,
    minWidth: 360,
    minHeight: 500,
    frame: true,
    title: "Office LAN Comm",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadURL("http://localhost:5173");

  mainWindow.on("close", (event) => {
    if (!app.isQuiting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on("minimize", () => {
    mainWindow.webContents.send("window:state", "minimized");
  });

  mainWindow.on("restore", () => {
    mainWindow.webContents.send("window:state", "restored");
  });

  mainWindow.on("show", () => {
    mainWindow.webContents.send("window:state", "restored");
  });
}

function createTray() {
  const icon = nativeImage.createFromDataURL(
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScxNicgaGVpZ2h0PScxNicgdmlld0JveD0nMCAwIDE2IDE2Jz4KICA8cmVjdCB4PScwJyB5PScwJyB3aWR0aD0nMTYnIGhlaWdodD0nMTYnIHJ4PSc0JyBmaWxsPScjMmY1NGViJy8+CiAgPHBhdGggZD0nTTQgOEgxMicgc3Ryb2tlPScjd2hpdGUnIHN0cm9rZS13aWR0aD0nMicgc3Rva2UtbGluZWNhcD0ncm91bmQnLz4KPC9zdmc+"
  );
  tray = new Tray(icon);
  const menu = Menu.buildFromTemplate([
    { label: "Open", click: () => mainWindow.show() },
    { label: "Dock Right", click: () => mainWindow.setBounds(getDockBounds()) },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        app.isQuiting = true;
        app.quit();
      }
    }
  ]);
  tray.setToolTip("Office LAN Comm");
  tray.setContextMenu(menu);
  tray.on("click", () => {
    if (mainWindow.isVisible()) {
      mainWindow.hide();
      return;
    }
    mainWindow.show();
  });
}

function startZeroconfDiscovery() {
  bonjour = new Bonjour();
  browser = bonjour.find({ type: "office-lan-comm", protocol: "tcp" });
  browser.on("up", (service) => {
    const summary = toServerSummary(service);
    if (!summary) {
      return;
    }
    discoveredServers.set(summary.id, summary);
    const settings = readSettings();
    if (!settings.preferredServerUrl && discoveredServerUrl === "http://localhost:4010") {
      discoveredServerUrl = summary.url;
    }
    pushDiscoveryUpdate();
  });
  browser.on("down", (service) => {
    const summary = toServerSummary(service);
    if (!summary) {
      return;
    }
    discoveredServers.delete(summary.id);
    ensureSelectedServerAvailable();
    pushDiscoveryUpdate();
  });
}

function restartZeroconfDiscovery() {
  if (browser) {
    browser.stop();
    browser = null;
  }
  if (bonjour) {
    bonjour.destroy();
    bonjour = null;
  }
  discoveredServers.clear();
  startZeroconfDiscovery();
  pushDiscoveryUpdate();
}

app.whenReady().then(async () => {
  app.setLoginItemSettings({ openAtLogin: true });
  createWindow();
  createTray();
  const settings = readSettings();
  if (typeof settings.preferredServerUrl === "string" && settings.preferredServerUrl) {
    discoveredServerUrl = settings.preferredServerUrl;
  }
  startZeroconfDiscovery();
  discoverySweepTimer = setInterval(pruneStaleServers, 5000);
  pushDiscoveryUpdate();

  if (!settings.storageDirectory) {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: "Select storage directory",
      properties: ["openDirectory", "createDirectory"]
    });
    if (!result.canceled && result.filePaths[0]) {
      writeSettings({ ...settings, storageDirectory: result.filePaths[0] });
      mainWindow.webContents.send("storage:selected", result.filePaths[0]);
    }
  }
});

ipcMain.handle("settings:get", () => readSettings());
ipcMain.handle("server:getUrl", () => discoveredServerUrl);
ipcMain.handle("server:getList", () => getDiscoveredServerList());
ipcMain.handle("server:refreshDiscovery", () => {
  restartZeroconfDiscovery();
  return getDiscoveredServerList();
});
ipcMain.handle("server:setUrl", (_, nextServerUrl) => {
  if (typeof nextServerUrl !== "string" || !nextServerUrl.trim()) {
    return discoveredServerUrl;
  }
  discoveredServerUrl = nextServerUrl.trim();
  const next = { ...readSettings(), preferredServerUrl: discoveredServerUrl };
  writeSettings(next);
  pushDiscoveryUpdate();
  return discoveredServerUrl;
});

ipcMain.handle("settings:set", (_, updates) => {
  const next = { ...readSettings(), ...updates };
  writeSettings(next);
  return next;
});

ipcMain.handle("storage:selectDirectory", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "Select storage directory",
    properties: ["openDirectory", "createDirectory"]
  });
  if (result.canceled || !result.filePaths[0]) {
    return null;
  }
  const next = { ...readSettings(), storageDirectory: result.filePaths[0] };
  writeSettings(next);
  return next.storageDirectory;
});

app.on("window-all-closed", () => {
  // Keep app running in tray.
});

app.on("before-quit", () => {
  if (discoverySweepTimer) {
    clearInterval(discoverySweepTimer);
  }
  if (browser) {
    browser.stop();
  }
  if (bonjour) {
    bonjour.destroy();
  }
});
