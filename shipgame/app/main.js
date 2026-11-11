// ShipGame as a desktop app: one window running shipgame.html, served from a tiny local web
// server (the game loads its models with fetch, which needs http rather than file://).
const { app, BrowserWindow, dialog } = require('electron');
const http = require('http');
const fs = require('fs');
const path = require('path');

// The game folder: named in game-path.txt next to the exe (written by build.ps1), or found by
// walking up from here.
function gameRoot() {
  const candidates = [];
  const txt = path.join(path.dirname(process.execPath), 'game-path.txt');
  if (fs.existsSync(txt)) candidates.push(fs.readFileSync(txt, 'utf8').trim());
  for (let d = __dirname; ; d = path.dirname(d)) {
    candidates.push(d);
    if (path.dirname(d) === d) break;
  }
  return candidates.find(d => fs.existsSync(path.join(d, 'shipgame.html')));
}

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css',
  '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.bin': 'application/octet-stream',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm',
};

// A fixed port keeps the page's saved settings (they're stored per address); any free port if it's taken.
function serve(root, port = 47615) {
  return new Promise(resolve => {
    const server = http.createServer((req, res) => {
      const rel = decodeURIComponent(new URL(req.url, 'http://local').pathname);
      const file = path.normalize(path.join(root, rel));
      if (!file.startsWith(root)) { res.writeHead(403); res.end(); return; }
      fs.stat(file, (err, st) => {
        if (err || !st.isFile()) { res.writeHead(404); res.end(); return; }
        // no-cache: a model or the game file replaced on disk shows up on the next launch
        res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] ?? 'application/octet-stream', 'Content-Length': st.size, 'Cache-Control': 'no-cache' });
        fs.createReadStream(file).pipe(res);
      });
    });
    server.once('error', () => resolve(serve(root, 0)));
    server.listen(port, '127.0.0.1', () => resolve(server.address().port));
  });
}

// use the fast GPU, and don't slow the game down when the window loses focus
app.commandLine.appendSwitch('ignore-gpu-blocklist');
app.commandLine.appendSwitch('force_high_performance_gpu');
app.commandLine.appendSwitch('disable-background-timer-throttling');
app.commandLine.appendSwitch('disable-renderer-backgrounding');
// sound plays without waiting for a click first
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

app.whenReady().then(async () => {
  const root = gameRoot();
  if (!root) {
    dialog.showErrorBox('ShipGame', "Couldn't find shipgame.html. Put its folder's path in game-path.txt next to ShipGame.exe.");
    app.quit();
    return;
  }
  const port = await serve(path.normalize(root));
  const win = new BrowserWindow({
    width: 1600, height: 900, title: 'ShipGame', backgroundColor: '#000000', autoHideMenuBar: true, show: false,
    webPreferences: { backgroundThrottling: false },
  });
  win.setMenu(null);
  win.once('ready-to-show', () => { win.maximize(); win.show(); });
  // F11 fullscreen, F12 developer tools
  win.webContents.on('before-input-event', (e, input) => {
    if (input.type !== 'keyDown') return;
    if (input.key === 'F11') { win.setFullScreen(!win.isFullScreen()); e.preventDefault(); }
    if (input.key === 'F12') { win.webContents.toggleDevTools(); e.preventDefault(); }
  });
  win.loadURL(`http://127.0.0.1:${port}/shipgame.html`);
});

app.on('window-all-closed', () => app.quit());
