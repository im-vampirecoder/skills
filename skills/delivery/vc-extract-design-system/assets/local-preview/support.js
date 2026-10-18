/*
 * vc local preview loader for canvas boards (.dc.html).
 *
 * Every board loads ./support.js. On claude.ai the canvas serves its own
 * file under that name; locally this one stands in for it:
 *
 * 1. Served over http (canvas/local/serve.mjs) and with the real Design
 *    runtime downloaded to canvas/local/artifact-type/dc-runtime.js, it
 *    loads that runtime, so boards render exactly as on claude.ai.
 * 2. Otherwise (opened from disk, or no runtime downloaded) it falls back
 *    to the small built-in runtime below, which covers the subset
 *    canvas-board-build.md allows: {{dotted.path}} holes, <sc-for>,
 *    <sc-if>, on* handlers from renderVals(), setState and data-props
 *    defaults. <dc-import> renders as a labelled box.
 *
 * Never published: claude-design-sync.md sends only *.dc.html and
 * canvas.json.
 */
(function () {
  'use strict';

  // The app folder is everything before "/canvas/" in this script's URL.
  var src = (document.currentScript && document.currentScript.src) || '';
  var cut = src.lastIndexOf('/canvas/');
  var appRoot = cut >= 0 ? src.slice(0, cut + 1) : '';
  var served = /^https?:$/.test(location.protocol);

  window.__vcStartLite = startLite;
  if (served && appRoot) {
    // The real runtime; a missing file falls through to the built-in one.
    document.write(
      '<script src="' + appRoot + 'canvas/local/artifact-type/dc-runtime.js"' +
      ' onerror="window.__vcNoRuntime=true"><\/script>' +
      '<script>if (window.__vcNoRuntime) window.__vcStartLite();<\/script>'
    );
    return;
  }
  startLite();

  function startLite() {
  // Load the upload-id -> local file map, then swallow the rest of the
  // document as raw text so table-hostile tags like <sc-for> survive.
  if (appRoot) {
    document.write('<script src="' + appRoot + 'canvas/local/blob-map.js"><\/script>');
  }
  document.write('<plaintext id="vc-raw" style="display:none">');

  function DCLogic(props) {
    this.props = props || {};
    this.state = {};
  }
  DCLogic.prototype.renderVals = function () { return {}; };
  DCLogic.prototype.setState = function (patch) {
    var next = typeof patch === 'function' ? patch(this.state, this.props) : patch;
    this.state = Object.assign({}, this.state, next);
    if (this.__render) this.__render();
  };
  DCLogic.prototype.forceUpdate = function () { if (this.__render) this.__render(); };
  window.DCLogic = DCLogic;

  function decodeEntities(s) {
    var t = document.createElement('textarea');
    t.innerHTML = s;
    return t.value;
  }

  // Swap /_blob/<id> for the local file recorded at publish time.
  function rewriteBlobs(text) {
    var map = window.__vcBlobMap || {};
    return text.replace(/\/_blob\/([A-Za-z0-9]+)/g, function (m, id) {
      return map[id] ? appRoot + map[id] : m;
    });
  }

  // <template> may sit anywhere, tables included, so control-flow tags
  // become templates before parsing.
  function toTemplates(html) {
    return html
      .replace(/<sc-for\b/g, '<template data-sc="for"').replace(/<\/sc-for>/g, '</template>')
      .replace(/<sc-if\b/g, '<template data-sc="if"').replace(/<\/sc-if>/g, '</template>');
  }

  function resolve(expr, scope) {
    var p = expr.trim();
    if (p === 'true') return true;
    if (p === 'false') return false;
    if (p === 'null') return null;
    if (/^-?\d+(\.\d+)?$/.test(p)) return Number(p);
    if (/^(['"]).*\1$/.test(p)) return p.slice(1, -1);
    var parts = p.split('.');
    var v = scope;
    for (var i = 0; i < parts.length; i++) {
      if (v === null || v === undefined) return undefined;
      v = v[parts[i]];
    }
    return v;
  }

  var WHOLE = /^\s*\{\{([^}]+)\}\}\s*$/;
  var HOLES = /\{\{([^}]+)\}\}/g;

  function interpolate(text, scope) {
    return text.replace(HOLES, function (m, p) {
      var v = resolve(p, scope);
      return v === undefined || v === null ? '' : String(v);
    });
  }

  function renderChildren(nodes, scope, parent) {
    for (var i = 0; i < nodes.length; i++) renderNode(nodes[i], scope, parent);
  }

  function renderNode(node, scope, parent) {
    if (node.nodeType === 3) {
      parent.appendChild(document.createTextNode(interpolate(node.nodeValue, scope)));
      return;
    }
    if (node.nodeType !== 1) return;
    var tag = node.localName;

    if (tag === 'template' && node.getAttribute('data-sc') === 'for') {
      var list = resolve((node.getAttribute('list') || '').replace(/[{}]/g, ''), scope) || [];
      var as = node.getAttribute('as') || 'item';
      for (var i = 0; i < list.length; i++) {
        var child = Object.create(scope);
        child[as] = list[i];
        child.$index = i;
        renderChildren(node.content.childNodes, child, parent);
      }
      return;
    }
    if (tag === 'template' && node.getAttribute('data-sc') === 'if') {
      if (resolve((node.getAttribute('value') || '').replace(/[{}]/g, ''), scope)) {
        renderChildren(node.content.childNodes, scope, parent);
      }
      return;
    }
    if (tag === 'dc-import') {
      var box = document.createElement('div');
      var size = (node.getAttribute('hint-size') || '100%,80px').split(',');
      box.style.cssText = 'width:' + size[0] + ';height:' + (size[1] || '80px') +
        ';border:1px dashed #94a3b8;display:flex;align-items:center;justify-content:center;' +
        'font:12px system-ui;color:#64748b';
      box.textContent = '[' + (node.getAttribute('name') || 'component') + ']';
      parent.appendChild(box);
      return;
    }

    var el = node.namespaceURI === 'http://www.w3.org/1999/xhtml'
      ? document.createElement(tag)
      : document.createElementNS(node.namespaceURI, node.tagName);
    for (var a = 0; a < node.attributes.length; a++) {
      var attr = node.attributes[a];
      var whole = WHOLE.exec(attr.value);
      if (/^on/.test(attr.name) && whole) {
        var fn = resolve(whole[1], scope);
        if (typeof fn === 'function') el.addEventListener(attr.name.slice(2), fn);
        continue;
      }
      if (whole) {
        var v = resolve(whole[1], scope);
        if (v === false || v === null || v === undefined) continue;
        el.setAttribute(attr.name, v === true ? '' : String(v));
        continue;
      }
      el.setAttribute(attr.name, interpolate(attr.value, scope));
    }
    var kids = tag === 'template' ? node.content.childNodes : node.childNodes;
    renderChildren(kids, scope, el);
    parent.appendChild(el);
  }

  function boot() {
    var holder = document.getElementById('vc-raw');
    if (!holder) return;
    var raw = rewriteBlobs(holder.textContent);
    holder.parentNode.removeChild(holder);

    // Head lines after support.js (stylesheet or script uploads).
    var headEnd = raw.search(/<\/head>/i);
    if (headEnd > 0) {
      document.head.appendChild(document.createRange().createContextualFragment(raw.slice(0, headEnd)));
    }

    var xdc = /<x-dc>([\s\S]*?)<\/x-dc>/.exec(raw);
    var markup = xdc ? xdc[1] : '';
    var helmet = /<helmet>([\s\S]*?)<\/helmet>/.exec(markup);
    if (helmet) {
      document.head.appendChild(document.createRange().createContextualFragment(helmet[1]));
      markup = markup.replace(helmet[0], '');
    }

    var scriptTag = /<script\b[^>]*data-dc-script[^>]*>([\s\S]*?)<\/script>/.exec(raw);
    var propsAttr = scriptTag && /data-props='([^']*)'/.exec(scriptTag[0]);
    var decl = {};
    try { decl = propsAttr ? JSON.parse(decodeEntities(propsAttr[1])) : {}; } catch (e) { console.warn('data-props', e); }
    var props = {};
    Object.keys(decl).forEach(function (k) {
      if (k !== '$preview' && decl[k] && 'default' in decl[k]) props[k] = decl[k]['default'];
    });

    var Component = DCLogic;
    if (scriptTag) {
      try {
        Component = new Function('DCLogic', scriptTag[1] + '\nreturn Component;')(DCLogic);
      } catch (e) { console.error('Board logic failed to load', e); }
    }
    var inst = new Component(props);
    if (!inst.state) inst.state = {};

    var tpl = document.createElement('template');
    tpl.innerHTML = toTemplates(markup);
    var root = document.createElement('div');
    root.style.display = 'contents';
    document.body.appendChild(root);

    inst.__render = function () {
      var vals = {};
      try { vals = inst.renderVals() || {}; } catch (e) { console.error('renderVals failed', e); }
      var frag = document.createDocumentFragment();
      renderChildren(tpl.content.childNodes, vals, frag);
      root.replaceChildren(frag);
    };
    inst.__render();
    if (typeof inst.componentDidMount === 'function') inst.componentDidMount();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
  }
})();
