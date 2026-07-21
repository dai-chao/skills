const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getBuiltInMusic: () => ipcRenderer.invoke('get-built-in-music')
});
