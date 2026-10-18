/**
 * Preset x theme palettes and per-family role tokens.
 * The preset palettes mirror the variable blocks in `assets/reader.css` so a
 * standalone SVG (no reader) resolves the same colours as the embedded reader.
 * Role tokens are generated here for both scopes (reader root and bare svg).
 */

export const PRESET_THEME_PALETTES = {
  'classic:light': {
    '--vc-bg': '#ffffff', '--vc-surface': '#f8fafc', '--vc-surface-border': '#e2e8f0',
    '--vc-text-primary': '#0f172a', '--vc-text-secondary': '#475569', '--vc-text-muted': '#94a3b8',
    '--vc-accent': '#2563eb', '--vc-accent-light': '#dbeafe',
    '--vc-node-bg': '#ffffff', '--vc-node-border': '#cbd5e1',
    '--vc-edge-stroke': '#64748b', '--vc-edge-active': '#2563eb',
    '--vc-badge-bg': '#f1f5f9', '--vc-font-sans': 'system-ui, -apple-system, sans-serif',
    '--vc-font-mono': 'ui-monospace, monospace',
  },
  'classic:dark': {
    '--vc-bg': '#090d16', '--vc-surface': '#0f172a', '--vc-surface-border': '#1e293b',
    '--vc-text-primary': '#f8fafc', '--vc-text-secondary': '#94a3b8', '--vc-text-muted': '#64748b',
    '--vc-accent': '#38bdf8', '--vc-accent-light': '#0369a1',
    '--vc-node-bg': '#0f172a', '--vc-node-border': '#334155',
    '--vc-edge-stroke': '#475569', '--vc-edge-active': '#38bdf8',
    '--vc-badge-bg': '#1e293b', '--vc-font-sans': 'system-ui, -apple-system, sans-serif',
    '--vc-font-mono': 'ui-monospace, monospace',
  },
  'signal-flow:light': {
    '--vc-bg': '#f0fdf4', '--vc-surface': '#dcfce7', '--vc-surface-border': '#86efac',
    '--vc-text-primary': '#14532d', '--vc-text-secondary': '#166534', '--vc-text-muted': '#4ade80',
    '--vc-accent': '#059669', '--vc-accent-light': '#d1fae5',
    '--vc-node-bg': '#ffffff', '--vc-node-border': '#10b981',
    '--vc-edge-stroke': '#059669', '--vc-edge-active': '#047857',
    '--vc-badge-bg': '#dcfce7', '--vc-font-sans': 'system-ui, -apple-system, sans-serif',
    '--vc-font-mono': 'ui-monospace, monospace',
  },
  'signal-flow:dark': {
    '--vc-bg': '#031c18', '--vc-surface': '#064e3b', '--vc-surface-border': '#047857',
    '--vc-text-primary': '#ecfdf5', '--vc-text-secondary': '#a7f3d0', '--vc-text-muted': '#34d399',
    '--vc-accent': '#34d399', '--vc-accent-light': '#065f46',
    '--vc-node-bg': '#064e3b', '--vc-node-border': '#10b981',
    '--vc-edge-stroke': '#34d399', '--vc-edge-active': '#6ee7b7',
    '--vc-badge-bg': '#064e3b', '--vc-font-sans': 'system-ui, -apple-system, sans-serif',
    '--vc-font-mono': 'ui-monospace, monospace',
  },
  'blueprint:light': {
    '--vc-bg': '#f0f9ff', '--vc-surface': '#e0f2fe', '--vc-surface-border': '#7dd3fc',
    '--vc-text-primary': '#0369a1', '--vc-text-secondary': '#0284c7', '--vc-text-muted': '#38bdf8',
    '--vc-accent': '#0284c7', '--vc-accent-light': '#bae6fd',
    '--vc-node-bg': '#ffffff', '--vc-node-border': '#0ea5e9',
    '--vc-edge-stroke': '#0284c7', '--vc-edge-active': '#0369a1',
    '--vc-badge-bg': '#e0f2fe', '--vc-font-sans': 'ui-monospace, monospace',
    '--vc-font-mono': 'ui-monospace, monospace',
  },
  'blueprint:dark': {
    '--vc-bg': '#081d33', '--vc-surface': '#0c2a4a', '--vc-surface-border': '#1e4976',
    '--vc-text-primary': '#e0f2fe', '--vc-text-secondary': '#bae6fd', '--vc-text-muted': '#38bdf8',
    '--vc-accent': '#38bdf8', '--vc-accent-light': '#0369a1',
    '--vc-node-bg': '#0c213a', '--vc-node-border': '#38bdf8',
    '--vc-edge-stroke': '#7dd3fc', '--vc-edge-active': '#38bdf8',
    '--vc-badge-bg': '#0c213a', '--vc-font-sans': 'ui-monospace, monospace',
    '--vc-font-mono': 'ui-monospace, monospace',
  },
  'editorial:light': {
    '--vc-bg': '#faf8f5', '--vc-surface': '#f3efe6', '--vc-surface-border': '#e2dacb',
    '--vc-text-primary': '#1c1917', '--vc-text-secondary': '#57534e', '--vc-text-muted': '#a8a29e',
    '--vc-accent': '#991b1b', '--vc-accent-light': '#fecaca',
    '--vc-node-bg': '#ffffff', '--vc-node-border': '#d6cfc4',
    '--vc-edge-stroke': '#78716c', '--vc-edge-active': '#991b1b',
    '--vc-badge-bg': '#f3efe6', '--vc-font-sans': 'system-ui, serif',
    '--vc-font-mono': 'ui-monospace, monospace',
  },
  'editorial:dark': {
    '--vc-bg': '#1c1917', '--vc-surface': '#292524', '--vc-surface-border': '#44403c',
    '--vc-text-primary': '#fafaf9', '--vc-text-secondary': '#d6d3d1', '--vc-text-muted': '#78716c',
    '--vc-accent': '#ef4444', '--vc-accent-light': '#7f1d1d',
    '--vc-node-bg': '#292524', '--vc-node-border': '#78716c',
    '--vc-edge-stroke': '#a8a29e', '--vc-edge-active': '#f87171',
    '--vc-badge-bg': '#292524', '--vc-font-sans': 'system-ui, serif',
    '--vc-font-mono': 'ui-monospace, monospace',
  },
};

/** Family stroke colours per theme; fills are derived with low alpha. */
export const ROLE_COLORS = {
  client: ['#0e7490', '#22d3ee'],
  service: ['#4f46e5', '#818cf8'],
  data: ['#b45309', '#fbbf24'],
  queue: ['#7c3aed', '#a78bfa'],
  cache: ['#c2410c', '#fb923c'],
  gateway: ['#0369a1', '#38bdf8'],
  security: ['#be123c', '#fb7185'],
  external: ['#475569', '#94a3b8'],
  worker: ['#0f766e', '#2dd4bf'],
  start: ['#047857', '#34d399'],
  success: ['#059669', '#34d399'],
  failure: ['#b91c1c', '#f87171'],
  waiting: ['#a16207', '#facc15'],
  decision: ['#a21caf', '#e879f9'],
  process: ['#1d4ed8', '#60a5fa'],
  governance: ['#6d28d9', '#c4b5fd'],
  transform: ['#4338ca', '#a5b4fc'],
  filter: ['#4d7c0f', '#a3e635'],
};

function rgba(hex, alpha) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha})`;
}

/** CSS declaring `--vc-role-<family>-stroke/fill` for light and dark scopes. */
export function roleTokenCss() {
  const light = [];
  const dark = [];
  for (const [family, [l, d]] of Object.entries(ROLE_COLORS)) {
    light.push(`--vc-role-${family}-stroke:${l};--vc-role-${family}-fill:${rgba(l, 0.1)};`);
    dark.push(`--vc-role-${family}-stroke:${d};--vc-role-${family}-fill:${rgba(d, 0.16)};`);
  }
  const perFamily = Object.keys(ROLE_COLORS).map((family) =>
    `.vc-node[data-family="${family}"]{--vc-node-stroke:var(--vc-role-${family}-stroke);--vc-node-fill:var(--vc-role-${family}-fill);}` +
    `.vc-legend-item[data-family="${family}"] .vc-legend-swatch{fill:var(--vc-role-${family}-fill);stroke:var(--vc-role-${family}-stroke);}`).join('\n');
  return [
    `.vc-diagram-root,svg.vc-diagram-svg{${light.join('')}}`,
    `.vc-diagram-root[data-theme="dark"],svg.vc-diagram-svg[data-theme="dark"]{${dark.join('')}}`,
    perFamily,
  ].join('\n');
}

/** Resolve a palette for a standalone svg `<style>` block. */
export function paletteCss(preset, theme, selector = 'svg') {
  const palette = PRESET_THEME_PALETTES[`${preset}:${theme}`] || PRESET_THEME_PALETTES['classic:light'];
  const body = Object.entries(palette).map(([k, v]) => `${k}:${v};`).join('');
  return `${selector}{${body}font-family:var(--vc-font-sans);}`;
}
