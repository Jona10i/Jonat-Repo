const { app, BrowserWindow, Tray, Menu, screen, ipcMain, dialog, nativeImage } = require("electron");
const fs = require("node:fs");
const path = require("node:path");
const { Bonjour } = require("bonjour-service");

let mainWindow;
let tray;
let discoveredServerUrl = "http://localhost:4010";
let browser;
let bonjour;

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
}

function createTray() {
  const icon = nativeImage.createFromDataURL(
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
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
  browser = bonjour.find({ type: "office-lan-comm", protocol: "tcp" }, (service) => {
    const host = service.referer?.address || service.addresses?.find((a) => a.includes(".")) || service.host;
    if (!host || !service.port) return;
    discoveredServerUrl = `http://${host}:${service.port}`;
    if (mainWindow?.webContents) {
      mainWindow.webContents.send("server:url", discoveredServerUrl);
    }
  });
}

app.whenReady().then(async () => {
  app.setLoginItemSettings({ openAtLogin: true });
  createWindow();
  createTray();
  startZeroconfDiscovery();

  const settings = readSettings();
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
  if (browser) {
    browser.stop();
  }
  if (bonjour) {
    bonjour.destroy();
  }
});
