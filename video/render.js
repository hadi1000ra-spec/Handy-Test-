// Renders video/mcp-erklaert.html frame by frame into video/mcp-erklaert.mp4
// Usage: node video/render.js [fps] [--stills]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

const FPS = Number(process.argv[2]) || 30;
const STILLS = process.argv.includes('--stills');
const dir = __dirname;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(dir, 'mcp-erklaert.html') + '?render');
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.DURATION);

  if (STILLS) {
    for (const t of [3, 12, 19, 30, 38, 48, 54, 62]) {
      await page.evaluate((t) => window.render(t), t);
      await page.locator('canvas').screenshot({ path: path.join(dir, `still-${t}.png`) });
    }
    await browser.close();
    return;
  }

  const out = path.join(dir, 'mcp-erklaert.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '20', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });

  const frames = Math.round(duration * FPS);
  for (let i = 0; i < frames; i++) {
    const data = await page.evaluate((t) => { window.render(t); return document.getElementById('c').toDataURL('image/jpeg', 0.93); }, i / FPS);
    const buf = Buffer.from(data.split(',')[1], 'base64');
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${frames}`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await browser.close();
  console.log('wrote', out);
})();
