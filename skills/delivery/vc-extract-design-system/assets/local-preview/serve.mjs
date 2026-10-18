#!/usr/bin/env node
/*
 * vc local preview server. Lives at docs/design-system/<app>/canvas/local/
 * and serves the whole <app> folder, so boards, assets and the downloaded
 * Design runtime load over http like they do on claude.ai.
 *
 * /_blob/<id> (an upload's URL on claude.ai) is answered from the local
 * file named for that id in canvas/local/blob-map.js.
 *
 * Usage: node docs/design-system/<app>/canvas/local/serve.mjs [port]
 * No dependencies; Node 18+.
 */
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { dirname, extname, join, normalize, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const localDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(localDir, '..', '..');
const port = Number(process.argv[2]) || 4321;

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.md': 'text/markdown; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.webp': 'image/webp', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf',
};

// blob-map.js is `window.__vcBlobMap = { "<id>": "assets/…" };`
async function blobMap() {
  try {
    const text = await readFile(join(localDir, 'blob-map.js'), 'utf8');
    return JSON.parse(text.slice(text.indexOf('{'), text.lastIndexOf('}') + 1));
  } catch {
    return {};
  }
}

async function send(res, file) {
  const info = await stat(file);
  if (info.isDirectory()) return send(res, join(file, 'index.html'));
  res.writeHead(200, {
    'Content-Type': TYPES[extname(file).toLowerCase()] || 'application/octet-stream',
    'Cache-Control': 'no-store',
  });
  res.end(await readFile(file));
}

createServer(async (req, res) => {
  try {
    let path = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const blob = /^\/_blob\/([A-Za-z0-9]+)/.exec(path);
    if (blob) {
      const mapped = (await blobMap())[blob[1]];
      if (!mapped) throw new Error('unmapped blob');
      path = '/' + mapped;
    }
    if (path === '/') {
      // Redirect so the overview's relative paths resolve under /canvas/.
      res.writeHead(302, { Location: '/canvas/index.html' });
      res.end();
      return;
    }
    const file = normalize(join(appRoot, path));
    if (file !== appRoot && !file.startsWith(appRoot + sep)) throw new Error('outside app');
    await send(res, file);
  } catch {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
  }
}).listen(port, '127.0.0.1', () => {
  console.log(`Design preview: http://127.0.0.1:${port}/canvas/index.html`);
});
