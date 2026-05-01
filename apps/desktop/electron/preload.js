const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("officeApi", {
  getSettings: () => ipcRenderer.invoke("settings:get"),
  setSettings: (updates) => ipcRenderer.invoke("settings:set", updates),
  getServerUrl: () => ipcRenderer.invoke("server:getUrl"),
  getDiscoveredServers: () => ipcRenderer.invoke("server:getList"),
  refreshDiscovery: () => ipcRenderer.invoke("server:refreshDiscovery"),
  setServerUrl: (serverUrl) => ipcRenderer.invoke("server:setUrl", serverUrl),
  chooseStorageDirectory: () => ipcRenderer.invoke("storage:selectDirectory"),
  onStorageSelected: (handler) => ipcRenderer.on("storage:selected", (_, path) => handler(path)),
  onServerUrl: (handler) => ipcRenderer.on("server:url", (_, serverUrl) => handler(serverUrl)),
  onServerList: (handler) => ipcRenderer.on("server:list", (_, servers) => handler(servers))
});
