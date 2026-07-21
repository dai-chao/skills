const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;

// 获取打包后的音乐资源路径
function getMusicPath() {
  const isDev = !app.isPackaged;
  if (isDev) {
    return path.join(__dirname, 'assets', 'music');
  }
  return path.join(process.resourcesPath, 'music');
}

// 扫描内置音乐
function scanBuiltInMusic() {
  const musicDir = getMusicPath();
  const audioExts = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'];

  try {
    if (!fs.existsSync(musicDir)) {
      console.log('音乐目录不存在:', musicDir);
      return [];
    }
    const files = fs.readdirSync(musicDir);
    return files
      .filter(f => audioExts.includes(path.extname(f).toLowerCase()))
      .map(f => {
        const filePath = path.join(musicDir, f);
        const stats = fs.statSync(filePath);
        return {
          path: filePath,
          name: path.basename(f, path.extname(f)),
          size: stats.size,
          ext: path.extname(f).toLowerCase()
        };
      })
      .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
  } catch (err) {
    console.error('扫描音乐失败:', err);
    return [];
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1726,
    height: 1242,
    minWidth: 800,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'renderer', 'preload.js')
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC: 获取内置音乐列表
ipcMain.handle('get-built-in-music', () => {
  return scanBuiltInMusic();
});
