// Export a whiteboard reel to MP4 (1080x1920, 30fps) with the voiceover.
// <project> is a folder holding scene.json (+ the audio / words files it points to).
//   node render.js <project>               -> <project>/out/reel.mp4
//   node render.js <project> --serve       -> live preview at http://localhost:8080
//   node render.js <project> --still 12.5  -> <project>/out/still.jpg (one frame, for checking layout)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ENGINE = __dirname;
const FPS = 30;
const args = process.argv.slice(2);
const projArg = args.find((a, i) => !a.startsWith('--') && args[i - 1] !== '--still');
if (!projArg) { console.error('Usage: node render.js <project-folder> [--serve | --still <sec>]'); process.exit(1); }
const ROOT = path.resolve(projArg);
if (!fs.existsSync(path.join(ROOT, 'scene.json'))) { console.error('No scene.json in', ROOT); process.exit(1); }
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.mp3': 'audio/mpeg', '.woff2': 'font/woff2' };

function serve(port) {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      // project files first (scene.json, audio), then engine files (index.html, board.js, fonts)
      const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html';
      const p = [path.join(ROOT, rel), path.join(ENGINE, rel)].find((f) =>
        (f.startsWith(ROOT + path.sep) || f.startsWith(ENGINE + path.sep)) && fs.existsSync(f) && fs.statSync(f).isFile());
      if (!p) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(res);
    }).listen(port, () => resolve(srv));
  });
}

(async () => {
  if (args.includes('--serve')) { await serve(8080); return console.log('Preview: http://localhost:8080'); }

  const srv = await serve(0);
  const url = `http://localhost:${srv.address().port}/index.html?render=1`;
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto(url);
  const { duration, audio } = await page.evaluate(() => window.init());
  fs.mkdirSync(path.join(ROOT, 'out'), { recursive: true });

  const si = args.indexOf('--still');
  if (si >= 0) {
    const t = parseFloat(args[si + 1] || '10');
    const data = await page.evaluate((t) => window.frame(t), t);
    fs.writeFileSync(path.join(ROOT, 'out', 'still.jpg'), Buffer.from(data.split(',')[1], 'base64'));
    console.log('Wrote out/still.jpg at', t, 's');
  } else {
    const out = path.join(ROOT, 'out', 'reel.mp4');
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS), '-i', '-',
      '-i', path.join(ROOT, audio), '-af', 'apad', '-t', duration.toFixed(2),
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
      '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const frames = Math.ceil(duration * FPS);
    for (let i = 0; i < frames; i++) {
      const data = await page.evaluate((t) => window.frame(t), i / FPS);
      if (!ff.stdin.write(Buffer.from(data.split(',')[1], 'base64'))) await new Promise((r) => ff.stdin.once('drain', r));
      if (i % 150 === 0) process.stdout.write(`frame ${i}/${frames}\n`);
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
    console.log('Wrote', out, `(${duration.toFixed(1)}s)`);
  }
  await browser.close(); srv.close();
})();
