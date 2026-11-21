// Export the whiteboard reel to MP4 (1080x1920, 30fps) with the voiceover.
//   node render.js                 -> out/reel.mp4
//   node render.js --serve         -> live preview at http://localhost:8080
//   node render.js --still 12.5    -> out/still.jpg (one frame, for checking layout)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ROOT = __dirname;
const FPS = 30;
const args = process.argv.slice(2);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.mp3': 'audio/mpeg', '.woff2': 'font/woff2' };

function serve(port) {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
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
