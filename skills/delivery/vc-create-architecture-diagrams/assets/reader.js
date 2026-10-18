/**
 * Diagram Reader Runtime
 * Pure vanilla JavaScript, zero runtime dependencies.
 */
(function() {
  function escapeXml(unsafe) {
    if (typeof unsafe !== 'string') return '';
    return unsafe
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  function initDiagram(container) {
    if (!container || container.__ak_initialized) return;
    container.__ak_initialized = true;

    const dataEl = container.querySelector('script[type="application/json"].vc-diagram-data');
    if (!dataEl) return;

    let irData;
    try {
      irData = JSON.parse(dataEl.textContent);
    } catch (e) {
      console.error('Failed to parse diagram data:', e);
      return;
    }

    const state = {
      focusedNodeId: null,
      activeReach: null, // 'upstream' | 'downstream'
      activeRoute: null,
      activeLensIndex: -1,
      currentChapterIndex: 0,
      isPresentation: false
    };

    // DOM Elements
    const root = container;
    const searchInput = container.querySelector('.vc-diagram-search-input');
    const nodes = Array.from(container.querySelectorAll('.vc-node'));
    const edges = Array.from(container.querySelectorAll('.vc-edge'));
    const themeBtn = container.querySelector('.vc-btn-theme');
    const presentBtn = container.querySelector('.vc-btn-present');
    const shareBtn = container.querySelector('.vc-btn-share');
    const reachDownBtn = container.querySelector('.vc-btn-reach-down');
    const reachUpBtn = container.querySelector('.vc-btn-reach-up');
    const routeBtn = container.querySelector('.vc-btn-route');
    const lensBtn = container.querySelector('.vc-btn-lens');
    const chapterPrevBtn = container.querySelector('.vc-btn-prev-chapter');
    const chapterNextBtn = container.querySelector('.vc-btn-next-chapter');
    const chapterLabel = container.querySelector('.vc-chapter-label');
    const motionBtn = container.querySelector('.vc-btn-motion');
    const svgEl = container.querySelector('.vc-diagram-svg');

    // Replay the finite entrance/trace motion by re-arming data-motion on the svg.
    function replayMotion() {
      if (!svgEl) return;
      svgEl.removeAttribute('data-motion');
      void svgEl.getBoundingClientRect();
      svgEl.setAttribute('data-motion', 'play');
    }
    if (motionBtn) motionBtn.addEventListener('click', replayMotion);

    // Build Graph Adjacency & Distinct Roles
    const outgoing = new Map();
    const incoming = new Map();
    const allRoles = new Set();

    nodes.forEach(n => {
      const role = n.getAttribute('data-role');
      if (role) allRoles.add(role);
    });
    const rolesList = Array.from(allRoles).sort();

    edges.forEach(edgeEl => {
      const from = edgeEl.getAttribute('data-from');
      const to = edgeEl.getAttribute('data-to');
      const edgeId = edgeEl.getAttribute('data-edge-id') || `${from}->${to}`;
      if (from && to) {
        if (!outgoing.has(from)) outgoing.set(from, []);
        outgoing.get(from).push({ to, edgeEl, edgeId });

        if (!incoming.has(to)) incoming.set(to, []);
        incoming.get(to).push({ from, edgeEl, edgeId });
      }
    });

    function clearHighlights() {
      nodes.forEach(n => {
        n.classList.remove('is-focused', 'is-dimmed');
      });
      edges.forEach(e => {
        e.classList.remove('is-highlighted', 'is-dimmed', 'is-active-trace');
      });
      state.focusedNodeId = null;
      state.activeReach = null;
      state.activeRoute = null;
    }

    function focusNodes(nodeIds) {
      const ids = (nodeIds || []).filter(Boolean);
      clearHighlights();
      if (ids.length === 0) {
        state.focusedNodeId = null;
        return;
      }
      state.focusedNodeId = ids[0];

      const focusSet = new Set(ids);
      const connectedNodeIds = new Set(ids);
      ids.forEach(id => {
        (outgoing.get(id) || []).forEach(e => connectedNodeIds.add(e.to));
        (incoming.get(id) || []).forEach(e => connectedNodeIds.add(e.from));
      });

      nodes.forEach(n => {
        const id = n.getAttribute('data-node-id');
        if (focusSet.has(id)) {
          n.classList.add('is-focused');
        } else if (!connectedNodeIds.has(id)) {
          n.classList.add('is-dimmed');
        }
      });

      edges.forEach(e => {
        const from = e.getAttribute('data-from');
        const to = e.getAttribute('data-to');
        if (focusSet.has(from) || focusSet.has(to)) {
          e.classList.add('is-highlighted');
        } else {
          e.classList.add('is-dimmed');
        }
      });
    }

    function focusNode(nodeId) {
      focusNodes(nodeId ? [nodeId] : []);
    }

    function traceReach(nodeId, direction) {
      const targetId = nodeId || state.focusedNodeId || (nodes[0] ? nodes[0].getAttribute('data-node-id') : null);
      if (!targetId) return;
      clearHighlights();
      state.focusedNodeId = targetId;
      state.activeReach = direction;

      const reachedNodes = new Set([targetId]);
      const reachedEdges = new Set();
      const queue = [targetId];

      while (queue.length > 0) {
        const current = queue.shift();
        const neighbors = (direction === 'downstream') ? (outgoing.get(current) || []) : (incoming.get(current) || []);
        neighbors.forEach(item => {
          const nextNode = (direction === 'downstream') ? item.to : item.from;
          reachedEdges.add(item.edgeEl);
          if (!reachedNodes.has(nextNode)) {
            reachedNodes.add(nextNode);
            queue.push(nextNode);
          }
        });
      }

      nodes.forEach(n => {
        const id = n.getAttribute('data-node-id');
        if (id === targetId) {
          n.classList.add('is-focused');
        } else if (!reachedNodes.has(id)) {
          n.classList.add('is-dimmed');
        }
      });

      edges.forEach(e => {
        if (reachedEdges.has(e)) {
          e.classList.add('is-highlighted', 'is-active-trace');
        } else {
          e.classList.add('is-dimmed');
        }
      });
    }

    function traceShortestRoute(sourceId, targetId) {
      if (!sourceId || !targetId || sourceId === targetId) return;
      clearHighlights();

      const queue = [[sourceId]];
      const visited = new Set([sourceId]);
      let shortestPath = null;

      while (queue.length > 0) {
        const path = queue.shift();
        const current = path[path.length - 1];
        if (current === targetId) {
          shortestPath = path;
          break;
        }
        const neighbors = outgoing.get(current) || [];
        const sorted = [...neighbors].sort((a, b) => a.to.localeCompare(b.to));
        for (const item of sorted) {
          if (!visited.has(item.to)) {
            visited.add(item.to);
            queue.push([...path, item.to]);
          }
        }
      }

      if (!shortestPath) return;

      const pathNodes = new Set(shortestPath);
      const pathEdges = new Set();

      for (let i = 0; i < shortestPath.length - 1; i++) {
        const u = shortestPath[i];
        const v = shortestPath[i + 1];
        const edgeObj = (outgoing.get(u) || []).find(e => e.to === v);
        if (edgeObj) pathEdges.add(edgeObj.edgeEl);
      }

      nodes.forEach(n => {
        const id = n.getAttribute('data-node-id');
        if (!pathNodes.has(id)) n.classList.add('is-dimmed');
        else if (id === sourceId || id === targetId) n.classList.add('is-focused');
      });

      edges.forEach(e => {
        if (pathEdges.has(e)) e.classList.add('is-highlighted', 'is-active-trace');
        else e.classList.add('is-dimmed');
      });
    }

    function cycleRoleLens() {
      if (rolesList.length === 0) return;
      state.activeLensIndex = (state.activeLensIndex + 1) % (rolesList.length + 1);

      if (state.activeLensIndex === rolesList.length) {
        clearHighlights();
        state.activeLens = null;
        return;
      }

      const roleName = rolesList[state.activeLensIndex];
      clearHighlights();
      state.activeLens = roleName;

      nodes.forEach(n => {
        const role = n.getAttribute('data-role');
        if (role !== roleName) {
          n.classList.add('is-dimmed');
        } else {
          n.classList.add('is-focused');
        }
      });
    }

    function cycleRoute() {
      if (nodes.length < 2) return;
      const src = nodes[0].getAttribute('data-node-id');
      const dst = nodes[nodes.length - 1].getAttribute('data-node-id');
      traceShortestRoute(src, dst);
    }

    function togglePresentation() {
      state.isPresentation = !state.isPresentation;
      root.classList.toggle('is-presentation', state.isPresentation);
    }

    function setChapter(index) {
      const views = (irData.meta && irData.meta.views) || [];
      if (views.length === 0) return;
      if (index < 0) index = 0;
      if (index >= views.length) index = views.length - 1;
      state.currentChapterIndex = index;
      const chapter = views[index];

      if (chapterLabel) {
        chapterLabel.textContent = `${index + 1}/${views.length}: ${chapter.title || chapter.id}`;
      }

      clearHighlights();
      if (chapter.focus_nodes && chapter.focus_nodes.length > 0) {
        focusNodes(chapter.focus_nodes);
      } else if (chapter.highlight_route && chapter.highlight_route.length >= 2) {
        traceShortestRoute(chapter.highlight_route[0], chapter.highlight_route[chapter.highlight_route.length - 1]);
      }
    }
    const PRESET_THEME_PALETTES = {
      'classic:light': {
        '--vc-bg': '#ffffff', '--vc-surface': '#f8fafc', '--vc-surface-border': '#e2e8f0',
        '--vc-text-primary': '#0f172a', '--vc-text-secondary': '#475569', '--vc-text-muted': '#94a3b8',
        '--vc-accent': '#2563eb', '--vc-accent-light': '#dbeafe',
        '--vc-node-bg': '#ffffff', '--vc-node-border': '#cbd5e1',
        '--vc-edge-stroke': '#64748b', '--vc-edge-active': '#2563eb',
        '--vc-badge-bg': '#f1f5f9', '--vc-font-sans': 'system-ui, -apple-system, sans-serif',
        '--vc-font-mono': 'ui-monospace, monospace'
      },
      'classic:dark': {
        '--vc-bg': '#090d16', '--vc-surface': '#0f172a', '--vc-surface-border': '#1e293b',
        '--vc-text-primary': '#f8fafc', '--vc-text-secondary': '#94a3b8', '--vc-text-muted': '#64748b',
        '--vc-accent': '#38bdf8', '--vc-accent-light': '#0369a1',
        '--vc-node-bg': '#0f172a', '--vc-node-border': '#334155',
        '--vc-edge-stroke': '#475569', '--vc-edge-active': '#38bdf8',
        '--vc-badge-bg': '#1e293b', '--vc-font-sans': 'system-ui, -apple-system, sans-serif',
        '--vc-font-mono': 'ui-monospace, monospace'
      },
      'signal-flow:light': {
        '--vc-bg': '#f0fdf4', '--vc-surface': '#dcfce7', '--vc-surface-border': '#86efac',
        '--vc-text-primary': '#14532d', '--vc-text-secondary': '#166534', '--vc-text-muted': '#4ade80',
        '--vc-accent': '#059669', '--vc-accent-light': '#d1fae5',
        '--vc-node-bg': '#ffffff', '--vc-node-border': '#10b981',
        '--vc-edge-stroke': '#059669', '--vc-edge-active': '#047857',
        '--vc-badge-bg': '#dcfce7', '--vc-font-sans': 'system-ui, -apple-system, sans-serif',
        '--vc-font-mono': 'ui-monospace, monospace'
      },
      'signal-flow:dark': {
        '--vc-bg': '#031c18', '--vc-surface': '#064e3b', '--vc-surface-border': '#047857',
        '--vc-text-primary': '#ecfdf5', '--vc-text-secondary': '#a7f3d0', '--vc-text-muted': '#34d399',
        '--vc-accent': '#34d399', '--vc-accent-light': '#065f46',
        '--vc-node-bg': '#064e3b', '--vc-node-border': '#10b981',
        '--vc-edge-stroke': '#34d399', '--vc-edge-active': '#6ee7b7',
        '--vc-badge-bg': '#064e3b', '--vc-font-sans': 'system-ui, -apple-system, sans-serif',
        '--vc-font-mono': 'ui-monospace, monospace'
      },
      'blueprint:light': {
        '--vc-bg': '#f0f9ff', '--vc-surface': '#e0f2fe', '--vc-surface-border': '#7dd3fc',
        '--vc-text-primary': '#0369a1', '--vc-text-secondary': '#0284c7', '--vc-text-muted': '#38bdf8',
        '--vc-accent': '#0284c7', '--vc-accent-light': '#bae6fd',
        '--vc-node-bg': '#ffffff', '--vc-node-border': '#0ea5e9',
        '--vc-edge-stroke': '#0284c7', '--vc-edge-active': '#0369a1',
        '--vc-badge-bg': '#e0f2fe', '--vc-font-sans': 'ui-monospace, monospace',
        '--vc-font-mono': 'ui-monospace, monospace'
      },
      'blueprint:dark': {
        '--vc-bg': '#081d33', '--vc-surface': '#0c2a4a', '--vc-surface-border': '#1e4976',
        '--vc-text-primary': '#e0f2fe', '--vc-text-secondary': '#bae6fd', '--vc-text-muted': '#38bdf8',
        '--vc-accent': '#38bdf8', '--vc-accent-light': '#0369a1',
        '--vc-node-bg': '#0c213a', '--vc-node-border': '#38bdf8',
        '--vc-edge-stroke': '#7dd3fc', '--vc-edge-active': '#38bdf8',
        '--vc-badge-bg': '#0c213a', '--vc-font-sans': 'ui-monospace, monospace',
        '--vc-font-mono': 'ui-monospace, monospace'
      },
      'editorial:light': {
        '--vc-bg': '#faf8f5', '--vc-surface': '#f3efe6', '--vc-surface-border': '#e2dacb',
        '--vc-text-primary': '#1c1917', '--vc-text-secondary': '#57534e', '--vc-text-muted': '#a8a29e',
        '--vc-accent': '#991b1b', '--vc-accent-light': '#fecaca',
        '--vc-node-bg': '#ffffff', '--vc-node-border': '#d6cfc4',
        '--vc-edge-stroke': '#78716c', '--vc-edge-active': '#991b1b',
        '--vc-badge-bg': '#f3efe6', '--vc-font-sans': 'system-ui, serif',
        '--vc-font-mono': 'ui-monospace, monospace'
      },
      'editorial:dark': {
        '--vc-bg': '#1c1917', '--vc-surface': '#292524', '--vc-surface-border': '#44403c',
        '--vc-text-primary': '#fafaf9', '--vc-text-secondary': '#d6d3d1', '--vc-text-muted': '#78716c',
        '--vc-accent': '#ef4444', '--vc-accent-light': '#7f1d1d',
        '--vc-node-bg': '#292524', '--vc-node-border': '#78716c',
        '--vc-edge-stroke': '#a8a29e', '--vc-edge-active': '#f87171',
        '--vc-badge-bg': '#292524', '--vc-font-sans': 'system-ui, serif',
        '--vc-font-mono': 'ui-monospace, monospace'
      }
    };

    function exportShareCard() {
      const svg = root.querySelector('.vc-diagram-svg');
      if (!svg) return;

      const title = (irData.meta && irData.meta.title) || 'System Map';
      const preset = root.getAttribute('data-preset') || 'classic';
      const theme = root.getAttribute('data-theme') || 'light';

      const VAR_WHITELIST = [
        '--vc-bg', '--vc-surface', '--vc-surface-border',
        '--vc-text-primary', '--vc-text-secondary', '--vc-text-muted',
        '--vc-accent', '--vc-accent-light',
        '--vc-node-bg', '--vc-node-border',
        '--vc-edge-stroke', '--vc-edge-active',
        '--vc-badge-bg', '--vc-font-sans', '--vc-font-mono'
      ];

      const paletteKey = `${preset}:${theme}`;
      const fallbackPalette = PRESET_THEME_PALETTES[paletteKey] || PRESET_THEME_PALETTES['classic:light'];

      let computed = null;
      if (typeof window !== 'undefined' && typeof window.getComputedStyle === 'function') {
        try { computed = window.getComputedStyle(root); } catch (e) { computed = null; }
      }

      const resolvedVars = {};
      VAR_WHITELIST.forEach(varName => {
        let val = '';
        if (computed && typeof computed.getPropertyValue === 'function') {
          val = computed.getPropertyValue(varName);
        }
        resolvedVars[varName] = (val && val.trim()) ? val.trim() : (fallbackPalette[varName] || '#000000');
      });

      const cardBg = resolvedVars['--vc-bg'];
      const cardSurface = resolvedVars['--vc-surface'];
      const cardBorder = resolvedVars['--vc-surface-border'];
      const textPrimary = resolvedVars['--vc-text-primary'];
      const textMuted = resolvedVars['--vc-text-muted'];
      const accent = resolvedVars['--vc-accent'];

      const cssDeclarations = Object.entries(resolvedVars)
        .map(([k, v]) => `${k}: ${v};`)
        .join(' ');

      const styleBlock = `<style>
        svg {
          ${cssDeclarations}
          font-family: var(--vc-font-sans);
        }
      </style>`;

      // Construct canonical 1200x630 Share Card SVG with self-contained resolved variables
      const shareCardSvg = `<svg viewBox="0 0 1200 630" width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
        <defs>
          ${styleBlock}
        </defs>
        <rect width="1200" height="630" fill="${cardBg}" rx="12" stroke="${cardBorder}" stroke-width="2"/>
        <g transform="translate(48, 56)">
          <text x="0" y="0" font-family="system-ui, sans-serif" font-size="28" font-weight="700" fill="${textPrimary}">${escapeXml(title)}</text>
          <text x="0" y="28" font-family="system-ui, sans-serif" font-size="14" fill="${textMuted}">System Map • Preset: ${escapeXml(preset)} • Theme: ${escapeXml(theme)}</text>
        </g>
        <g transform="translate(48, 120)">
          <rect width="1104" height="450" fill="${cardSurface}" rx="8" stroke="${cardBorder}" stroke-width="1.5"/>
          <svg x="20" y="20" width="1064" height="410" viewBox="${svg.getAttribute('viewBox') || '0 0 1000 600'}">
            ${svg.innerHTML}
          </svg>
        </g>
      </svg>`;

      const blob = new Blob([shareCardSvg], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-share-card-1200x630.svg`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    // Attach Node Click Handlers
    nodes.forEach(nodeEl => {
      nodeEl.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = nodeEl.getAttribute('data-node-id');
        if (state.focusedNodeId === id) {
          clearHighlights();
        } else {
          focusNode(id);
        }
      });
    });

    const viewport = container.querySelector('.vc-diagram-viewport');
    if (viewport) {
      viewport.addEventListener('click', () => {
        clearHighlights();
      });
    }

    // Search Input (Searches Label, ID, Description, Role)
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const q = e.target.value.trim().toLowerCase();
        if (!q) {
          clearHighlights();
          return;
        }
        clearHighlights();
        nodes.forEach(n => {
          const label = (n.getAttribute('data-label') || '').toLowerCase();
          const id = (n.getAttribute('data-node-id') || '').toLowerCase();
          const desc = (n.getAttribute('data-desc') || '').toLowerCase();
          const role = (n.getAttribute('data-role') || '').toLowerCase();
          if (label.includes(q) || id.includes(q) || desc.includes(q) || role.includes(q)) {
            n.classList.remove('is-dimmed');
            n.classList.add('is-focused');
          } else {
            n.classList.add('is-dimmed');
          }
        });
      });
    }

    // Control Buttons
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        const currentTheme = root.getAttribute('data-theme') || 'light';
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', nextTheme);
        themeBtn.textContent = nextTheme === 'dark' ? '☀️' : '🌙';
      });
    }

    if (presentBtn) presentBtn.addEventListener('click', togglePresentation);
    if (shareBtn) shareBtn.addEventListener('click', exportShareCard);
    if (reachDownBtn) reachDownBtn.addEventListener('click', () => traceReach(null, 'downstream'));
    if (reachUpBtn) reachUpBtn.addEventListener('click', () => traceReach(null, 'upstream'));
    if (routeBtn) routeBtn.addEventListener('click', cycleRoute);
    if (lensBtn) lensBtn.addEventListener('click', cycleRoleLens);

    if (chapterPrevBtn) {
      chapterPrevBtn.addEventListener('click', () => setChapter(state.currentChapterIndex - 1));
    }
    if (chapterNextBtn) {
      chapterNextBtn.addEventListener('click', () => setChapter(state.currentChapterIndex + 1));
    }

    // Global Scoped Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA')) {
        if (e.key === 'Escape') activeEl.blur();
        return;
      }

      if (e.key === '/') {
        if (searchInput) {
          e.preventDefault();
          searchInput.focus();
        }
      } else if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        togglePresentation();
      } else if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        cycleRoute();
      } else if (e.key === 'l' || e.key === 'L') {
        e.preventDefault();
        cycleRoleLens();
      } else if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        replayMotion();
      } else if (e.key === '[') {
        e.preventDefault();
        setChapter(state.currentChapterIndex - 1);
      } else if (e.key === ']') {
        e.preventDefault();
        setChapter(state.currentChapterIndex + 1);
      } else if (e.key === 'Escape') {
        if (state.isPresentation) {
          togglePresentation();
        } else {
          clearHighlights();
        }
      }
    });

    if (irData.meta && irData.meta.views && irData.meta.views.length > 0) {
      setChapter(0);
    }
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.vc-diagram-root').forEach(initDiagram);
      });
    } else {
      document.querySelectorAll('.vc-diagram-root').forEach(initDiagram);
    }
  }

  if (typeof window !== 'undefined') {
    window.VcDiagram = { init: initDiagram };
  }
})();
