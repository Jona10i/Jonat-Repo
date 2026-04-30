const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("officeApi", {
  getSettings: () => ipcRenderer.invoke("settings:get"),
  setSettings: (updates) => ipcRenderer.invoke("settings:set", updates),
  getServerUrl: () => ipcRenderer.invoke("server:getUrl"),
  chooseStorageDirectory: () => ipcRenderer.invoke("storage:selectDirectory"),
  onStorageSelected: (handler) => ipcRenderer.on("storage:selected", (_, path) => handler(path)),
  onServerUrl: (handler) => ipcRenderer.on("server:url", (_, serverUrl) => handler(serverUrl))
});
