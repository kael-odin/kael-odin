#!/usr/bin/env node
// Produce a local-only preview of the actual README, not a second mock layout.
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const root = path.resolve(__dirname, '..');
const local = createRequire(path.join(root, 'package.json'));
const fallback = createRequire(path.join(root, '.preview-tools/package.json'));
function dependency(name) {
  try { return local.resolve(name); } catch { return fallback.resolve(name); }
}
(async () => {
  const { marked } = await import(require('node:url').pathToFileURL(dependency('marked')));
  const css = fs.readFileSync(dependency('github-markdown-css/github-markdown.css'), 'utf8');
  const markdown = fs.readFileSync(path.join(root, 'README.md'), 'utf8');
  const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kael Odin · README preview</title><style>${css}
  :root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;padding:28px;background:#fff;color:#1f2328;font:14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.preview-label{max-width:980px;margin:0 auto 18px;color:#656d76;font:11px ui-monospace,monospace;letter-spacing:1.5px}.frame{max-width:980px;margin:auto;padding:40px;border:1px solid #d1d9e0;border-radius:8px}.markdown-body img{max-width:100%;height:auto}.markdown-body picture img{vertical-align:middle}.markdown-body br{line-height:1.4}@media(prefers-color-scheme:dark){body{background:#0d1117;color:#f0f6fc}.frame{border-color:#3d444d}.preview-label{color:#9198a1}}@media(max-width:640px){body{padding:12px 8px}.frame{padding:16px 10px}.preview-label{font-size:9px;letter-spacing:.8px}.markdown-body h2{font-size:21px}}
  </style></head><body><div class="preview-label">KAEL ODIN / ACTUAL README · GITHUB MARKDOWN CSS</div><main class="frame"><article class="markdown-body">${marked.parse(markdown, { gfm: true })}</article></main></body></html>`;
  fs.writeFileSync(path.join(root, '_preview.html'), html);
  console.log('Preview generated from README.md.');
})();
