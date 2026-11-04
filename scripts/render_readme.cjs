#!/usr/bin/env node
// Optional raster renderer. The profile itself has no JavaScript dependency.
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const root = path.resolve(__dirname, '..');
let Resvg;
try { ({ Resvg } = require('@resvg/resvg-js')); }
catch { ({ Resvg } = createRequire(path.join(root, '.preview-tools', 'package.json'))('@resvg/resvg-js')); }

const fontCandidates = process.platform === 'win32'
  ? ['C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/consola.ttf', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/georgia.ttf']
  : ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'];
const fontFiles = fontCandidates.filter(p => fs.existsSync(p));
function render(input, output, width) {
  const options = { font: { loadSystemFonts: fontFiles.length === 0, fontFiles, defaultFontFamily: 'Arial' } };
  if (width) options.fitTo = { mode: 'width', value: width };
  let source = fs.readFileSync(input, 'utf8');
  source = source.replace(/href="(\.\.[^"]+\.png)"/g, (_, relative) => {
    const image = fs.readFileSync(path.resolve(path.dirname(input), relative));
    return `href="data:image/png;base64,${image.toString('base64')}"`;
  });
  const svg = new Resvg(source, options);
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, svg.render().asPng());
}

const args = process.argv.slice(2);
if (args[0] === '--frames') {
  const input = path.resolve(args[1]);
  const output = path.resolve(args[2]);
  const width = Number(args[3] || 1000);
  for (const file of fs.readdirSync(input).filter(n => n.endsWith('.svg')).sort())
    render(path.join(input, file), path.join(output, file.replace('.svg', '.png')), width);
  console.log(`Rendered frames in ${output}`);
} else if (args.length === 2) {
  render(path.resolve(args[0]), path.resolve(args[1]));
} else {
  const source = path.join(root, 'assets/readme/source');
  for (const file of fs.readdirSync(source).filter(n => n.startsWith('project-') && n.endsWith('.svg')))
    render(path.join(source, file), path.join(root, 'assets/readme', file.replace('.svg', '.png')));
  console.log('Rendered all real-page project boards.');
}
