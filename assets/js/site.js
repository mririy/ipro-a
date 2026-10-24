/* =====================================================================
   Ай Про · IPROSCHOOL — сценарий сайта
   Версия A: день в Ай Про — подводки к блокам по часам,
   палитры глав смешиваются кадр за кадром, покадровые сцены 3D-макета, автобус по маршруту,
   окна программ, галерея, форма записи, новости, помощник.
   ===================================================================== */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');
  var reduce = reduceMQ.matches;
  if (reduceMQ.addEventListener) reduceMQ.addEventListener('change', function (e) { reduce = e.matches; });
  var fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return [].slice.call((c || d).querySelectorAll(s)); };
  var clamp01 = function (v) { return Math.max(0, Math.min(1, v)); };
  var isA11y = function () { return root.classList.contains('a11y'); };
  var tryPlay = function (v) { var p = v.play(); if (p && p.catch) p.catch(function () {}); };

  /* ---------------- первый экран: горизонтальное видео или вертикальное на телефоне ---------------- */
  var introV = $('.intro__v');
  (function () {
    if (!introV) return;
    var mq = matchMedia('(orientation: portrait) and (max-width: 820px)');
    var pick = function () {
      var port = mq.matches;
      var src = port ? introV.dataset.srcPort : introV.dataset.srcLand;
      if (introV.getAttribute('src') === src) return;
      introV.setAttribute('poster', port ? introV.dataset.posterPort : introV.dataset.posterLand);
      introV.src = src; introV.muted = true; tryPlay(introV);
    };
    pick();
    if (mq.addEventListener) mq.addEventListener('change', pick);
  })();

  /* ---------------- главы, палитры, капсула, точки ---------------- */
  var scenes = $$('main .sc');
  var themeMeta = $('meta[name="theme-color"]');
  var chapNum = $('#chapNum'), chapName = $('#chapName'), chapBtn = $('#menuBtn'), bar = $('.dock__bar');
  var KEYS = ['bg', 'fg', 'muted', 'accent', 'aura', 'band', 'card', 'line'];
  var AURA = [[74, 46], [22, 30], [72, 40], [28, 62], [76, 56], [24, 34], [62, 30], [40, 64], [72, 44], [30, 50]];
  scenes.forEach(function (s, i) {
    var a = AURA[i % AURA.length];
    s.style.setProperty('--ax', a[0] + '%'); s.style.setProperty('--ay', a[1] + '%'); s.style.setProperty('--ry', Math.min(a[1], 100 - a[1]) + '%');
  });

  var parse = function (v) {
    var m = v.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
    if (m) { var h = m[1]; if (h.length === 3) h = h.replace(/./g, function (c) { return c + c; }); return [0, 2, 4].map(function (j) { return parseInt(h.slice(j, j + 2), 16); }).concat(1); }
    m = v.match(/^rgba?\(([^)]+)\)$/i);
    if (m) { var p = m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat); if (p.length >= 3) return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
    return null;
  };
  var fmt = function (c) { return 'rgba(' + Math.round(c[0]) + ',' + Math.round(c[1]) + ',' + Math.round(c[2]) + ',' + (+c[3].toFixed(3)) + ')'; };
  var FADE = 1400, FADE_AURA = 1900, pal = null, palRaf = 0;
  var easeOut = function (t) { return 1 - (1 - t) * (1 - t); };
  function fadeTo(s, instant) {
    var cs = getComputedStyle(s), raw = {}, to = {};
    KEYS.forEach(function (k) { raw[k] = cs.getPropertyValue('--s-' + k).trim(); to[k] = parse(raw[k]); });
    cancelAnimationFrame(palRaf);
    var ok = KEYS.every(function (k) { return to[k]; });
    if (!pal || reduce || instant || !ok) {
      KEYS.forEach(function (k) { if (raw[k]) root.style.setProperty('--' + k, raw[k]); });
      if (themeMeta && raw.bg) themeMeta.setAttribute('content', raw.bg);
      pal = ok ? KEYS.reduce(function (o, k) { o[k] = to[k].slice(); return o; }, {}) : null;
      return;
    }
    var from = KEYS.reduce(function (o, k) { o[k] = pal[k].slice(); return o; }, {}), t0 = performance.now();
    var step = function (now) {
      var done = true;
      KEYS.forEach(function (k) {
        var p = Math.min(1, Math.max(0, now - t0) / (k === 'aura' ? FADE_AURA : FADE));
        if (p < 1) done = false;
        var e = easeOut(p);
        pal[k] = from[k].map(function (a, j) { return a + (to[k][j] - a) * e; });
        root.style.setProperty('--' + k, fmt(pal[k]));
      });
      if (themeMeta) themeMeta.setAttribute('content', fmt(pal.bg));
      if (!done) palRaf = requestAnimationFrame(step);
    };
    palRaf = requestAnimationFrame(step);
  }

  var MENU_OF = { news: 'news', concept: 'concept', about: 'concept', programs: 'programs', food: 'food', teachers: 'teachers', safety: 'safety', extra: 'extra', transfer: 'transfer', summer: 'summer', reviews: 'reviews', gallery: 'gallery' };
  var nav = $('.dots');
  var dots = scenes.map(function (s, i) {
    var b = d.createElement('button');
    b.type = 'button';
    if (s.classList.contains('act')) b.className = 'is-act';
    b.setAttribute('aria-label', (s.dataset.num ? s.dataset.num + ' · ' : '') + s.dataset.title);
    var sp = d.createElement('span'); sp.textContent = s.dataset.title; b.appendChild(sp);
    b.addEventListener('click', function () { go(s); });
    nav.appendChild(b);
    return b;
  });
  var active = -1;
  var narrowMQ = matchMedia('(max-width: 560px)');
  function setActive(i) {
    if (i < 0 || i === active) return;
    active = i;
    var s = scenes[i];
    fadeTo(s);
    chapNum.textContent = s.dataset.num || '';
    chapName.textContent = (narrowMQ.matches && s.dataset.short) || s.dataset.title || '';
    if (!reduce) { chapBtn.classList.remove('swap'); void chapBtn.offsetWidth; chapBtn.classList.add('swap'); }
    dots.forEach(function (b, j) { b.setAttribute('aria-current', j === i ? 'true' : 'false'); });
    var m = MENU_OF[s.id];
    $$('.menu a[data-go]').forEach(function (a) { a.setAttribute('aria-current', a.dataset.go === m ? 'true' : 'false'); });
    var ask = $('.ask');
    if (ask) ask.classList.toggle('is-hidden', s.id === 'signup');
  }
  var sceneIO = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) setActive(scenes.indexOf(e.target)); });
  }, { rootMargin: '-50% 0px -49% 0px' });
  scenes.forEach(function (s) { sceneIO.observe(s); });
  fadeTo(scenes[0], true);
  setActive(0);

  function go(target) {
    var el = typeof target === 'string' ? d.getElementById(target) : target;
    if (!el) return;
    el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  }
  addEventListener('keydown', function (e) {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey || $('dialog[open]')) return;
    var t = e.target;
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
    if (e.key === 'ArrowRight') { e.preventDefault(); go(scenes[Math.min(scenes.length - 1, active + 1)]); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); go(scenes[Math.max(0, active - 1)]); }
  });

  /* ---------------- появление: заголовки по словам, блоки снизу ---------------- */
  $$('[data-split]').forEach(function (el) {
    var n = 0;
    (function walk(node) {
      [].slice.call(node.childNodes).forEach(function (c) {
        if (c.nodeType === 3) {
          var f = d.createDocumentFragment();
          c.textContent.split(/(\s+)/).forEach(function (p) {
            if (!p) return;
            if (/^\s+$/.test(p)) { f.appendChild(d.createTextNode(' ')); return; }
            var sp = d.createElement('span'); sp.className = 'w'; sp.style.setProperty('--wi', n++); sp.textContent = p; f.appendChild(sp);
          });
          c.parentNode.replaceChild(f, c);
        } else if (c.nodeType === 1) walk(c);
      });
    })(el);
  });
  var revealIO = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('is-in'); revealIO.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
  $$('.rv, [data-split]').forEach(function (el) { revealIO.observe(el); });
  root.classList.add('rv-ready');

  /* ---------------- видео: играет только то, что на экране ---------------- */
  var vidIO = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      var v = e.target;
      if (e.isIntersecting && !(reduce && v !== introV)) { if (v.paused) tryPlay(v); }
      else if (!v.paused) v.pause();
    });
  }, { threshold: 0.25 });
  $$('main video').forEach(function (v) { v.muted = true; vidIO.observe(v); });

  /* ---------------- счётчики ---------------- */
  var countIO = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      countIO.unobserve(e.target);
      var el = e.target, to = +el.dataset.count, suffix = el.textContent.replace(/[0-9]/g, ''), t0 = performance.now();
      if (reduce || isA11y()) return;
      (function tick(now) {
        var p = Math.min(1, (now - t0) / 1400), v = Math.round(to * easeOut(p));
        el.textContent = v + suffix;
        if (p < 1) requestAnimationFrame(tick);
      })(t0);
    });
  }, { threshold: 0.6 });
  $$('[data-count]').forEach(function (el) { countIO.observe(el); });

  /* ---------------- покадровые сцены 3D-макета ---------------- */
  var seqs = [];
  $$('[data-seq]').forEach(function (el) {
    var n = +el.dataset.frames, path = el.dataset.path, ext = el.dataset.ext;
    var canvas = $('canvas', el), ctx = canvas.getContext('2d'), frame = $('.seq__frame', el), prog = $('.seq__progress', el);
    var imgs = new Array(n), drawn = -1, loading = false, dpr = 1, W = 0, H = 0;
    var order = (function () {
      var o = [], seen = {}, add = function (i) { if (i >= 0 && i < n && !seen[i]) { seen[i] = 1; o.push(i); } };
      add(0); add(n - 1);
      for (var k = 2; k < n; k *= 2) for (var j = 1; j < k; j++) add(Math.round(j * (n - 1) / k));
      for (var i = 0; i < n; i++) add(i);
      return o;
    })();
    var src = function (i) { return path + '/f_' + String(i).padStart(3, '0') + '.' + ext; };
    function size() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = Math.round(frame.clientWidth * dpr); H = Math.round(frame.clientHeight * dpr);
      if (canvas.width !== W || canvas.height !== H) { canvas.width = W; canvas.height = H; drawn = -1; }
    }
    function nearest(i) {
      if (imgs[i] && imgs[i].ok) return i;
      for (var k = 1; k < n; k++) {
        if (imgs[i - k] && imgs[i - k].ok) return i - k;
        if (imgs[i + k] && imgs[i + k].ok) return i + k;
      }
      return -1;
    }
    function draw(i) {
      var j = nearest(i);
      if (j < 0 || j === drawn) return;
      var im = imgs[j].im, iw = im.naturalWidth, ih = im.naturalHeight;
      var s = Math.max(W / iw, H / ih), dw = iw * s, dh = ih * s;
      ctx.clearRect(0, 0, W, H);
      ctx.drawImage(im, (W - dw) / 2, (H - dh) / 2, dw, dh);
      drawn = j;
      if (!el.classList.contains('is-live')) el.classList.add('is-live');
    }
    function load() {
      if (loading) return; loading = true;
      var q = order.filter(function (i) { return !imgs[i]; });
      var next = function () {
        if (!q.length) return;
        var i = q.shift(), im = new Image();
        imgs[i] = { im: im, ok: false };
        im.decoding = 'async';
        im.onload = function () { imgs[i].ok = true; if (st.cur === i || drawn < 0) draw(st.cur); next(); };
        im.onerror = function () { next(); };
        im.src = src(i);
      };
      for (var c = 0; c < 4; c++) next();
    }
    var st = { el: el, cur: 0, n: n, prog: prog, draw: draw, size: size, load: load };
    seqs.push(st);
    new IntersectionObserver(function (es) { if (es[0].isIntersecting && !reduce && !isA11y()) { size(); load(); } }, { rootMargin: '120% 0px' }).observe(el);
  });
  function updSeqs() {
    if (reduce || isA11y()) return;
    var vh = innerHeight;
    seqs.forEach(function (q) {
      var r = q.el.getBoundingClientRect();
      if (r.bottom < -vh || r.top > vh * 2) return;
      var p = clamp01(-r.top / Math.max(1, r.height - vh));
      var i = Math.round(p * (q.n - 1));
      if (q.prog) q.prog.style.setProperty('--p', p.toFixed(3));
      q.cur = i; q.draw(i);
    });
  }

  /* ---------------- солнце по дуге: от акта к акту ---------------- */
  var arcs = $$('[data-arc]').map(function (el, i, all) {
    var end = parseFloat(el.dataset.arc), night = !!el.closest('.seq--night');
    var start = night ? 0.04 : (i > 0 ? parseFloat(all[i - 1].dataset.arc) : 0.02);
    if (night) end = 0.36;
    if (start > end) start = end - 0.2;
    return { el: el, start: start, end: end };
  });
  function updArcs() {
    var vh = innerHeight;
    arcs.forEach(function (a) {
      var r = a.el.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) return;
      var p = reduce ? 1 : clamp01((vh - r.top) / (vh * 0.75));
      var pos = a.start + (a.end - a.start) * p;
      a.el.style.setProperty('--a', (-90 + 180 * pos).toFixed(2) + 'deg');
    });
  }

  /* ---------------- подводки: время дня «доходит» от предыдущей подводки до своей ---------------- */
  var toMin = function (t) { var m = /^(\d{1,2}):(\d{2})$/.exec(t || ''); return m ? (+m[1]) * 60 + (+m[2]) : 0; };
  var fmtT = function (m) { m = Math.round(m); return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); };
  var clocks = $$('.li__t[data-time]');
  var clockIO = new IntersectionObserver(function (es) {
    es.forEach(function (en) {
      if (!en.isIntersecting) return;
      clockIO.unobserve(en.target);
      var el = en.target, i = clocks.indexOf(el), to = toMin(el.dataset.time);
      var from = i > 0 ? toMin(clocks[i - 1].dataset.time) : to - 30, t0 = performance.now();
      if (reduce || isA11y() || from >= to) return;
      (function tick(now) {
        var p = Math.min(1, (now - t0) / 1100);
        el.textContent = fmtT(from + (to - from) * easeOut(p));
        if (p < 1) requestAnimationFrame(tick); else el.textContent = el.dataset.time;
      })(t0);
    });
  }, { threshold: 0.6 });
  clocks.forEach(function (el) { clockIO.observe(el); });

  /* ---------------- трансфер: автобус едет по маршруту ---------------- */
  var route = $('[data-route]'), rPath = route && $('.route__line', route), rDone = route && $('.route__done', route), rBus = route && $('.route__bus', route), rSvg = route && $('svg', route);
  var rLen = 0, stopW = -1, stopLen = 0;
  if (rPath) { rLen = rPath.getTotalLength(); rDone.setAttribute('pathLength', '1'); rDone.style.strokeDasharray = '1 1'; }
  function updRoute() {
    if (!rPath) return;
    var r = route.getBoundingClientRect(), vh = innerHeight;
    if (r.bottom < -100 || r.top > vh + 100) return;
    var p = reduce ? 1 : clamp01((vh * 0.92 - r.top) / (vh * 0.62));
    rDone.style.strokeDashoffset = (1 - p).toFixed(4);
    var sr = rSvg.getBoundingClientRect(), sx = sr.width / 1000, sy = sr.height / 160;
    if (stopW !== sr.width) {  /* автобус останавливается перед остановкой «Ай Про», не наезжая на неё */
      stopW = sr.width; stopLen = rLen;
      var end = rPath.getPointAtLength(rLen);
      for (var k = rLen; k > 0; k -= rLen / 240) { var q = rPath.getPointAtLength(k); if (Math.hypot((end.x - q.x) * sx, (end.y - q.y) * sy) >= 62) { stopLen = k; break; } }
    }
    var pt = rPath.getPointAtLength(stopLen * p), pt2 = rPath.getPointAtLength(Math.min(rLen, stopLen * p + 2));
    var x = (sr.left - r.left) + pt.x * sx, y = (sr.top - r.top) + pt.y * sy;
    var ang = Math.atan2((pt2.y - pt.y) * sy, (pt2.x - pt.x) * sx) * 180 / Math.PI;
    rBus.style.setProperty('--bx', x.toFixed(1) + 'px');
    rBus.style.setProperty('--by', y.toFixed(1) + 'px');
    rBus.style.setProperty('--br', Math.max(-25, Math.min(25, ang)).toFixed(1) + 'deg');
  }

  /* ---------------- параллакс (только компьютер) и прогресс ---------------- */
  var par = fine ? $$('[data-par]') : [];
  var ticking = false;
  var introSec = $('.drw > .intro');
  function updDrawer(vh) {
    if (!introSec) return;
    var p = clamp01(scrollY / vh);
    introSec.style.setProperty('--dp', reduce ? 0 : p.toFixed(3));
    if (introV) {
      if (p > 0.97) { if (!introV.paused) { introV.pause(); introV._covered = true; } }
      else if (introV._covered && introV.paused) { introV._covered = false; tryPlay(introV); }
    }
  }
  function frame() {
    ticking = false;
    var vh = innerHeight, max = root.scrollHeight - vh;
    updDrawer(vh);
    if (bar) bar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, scrollY / max) : 0).toFixed(4) + ')';
    updSeqs(); updArcs(); updRoute();
    if (reduce || isA11y()) return;
    par.forEach(function (el) {
      var r = el.parentElement.getBoundingClientRect();
      if (r.bottom < -300 || r.top > vh + 300) return;
      el.style.translate = '0 ' + ((r.top + r.height / 2 - vh / 2) * (parseFloat(el.dataset.par) || 0)).toFixed(1) + 'px';
    });
  }
  addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }, { passive: true });
  addEventListener('resize', function () { seqs.forEach(function (q) { q.size(); q.draw(q.cur); }); frame(); });
  frame();

  /* ---------------- окна: меню, программы, сведения, помощник ---------------- */
  var openStack = [];
  function anyOpen() { return $('dialog[open]'); }
  function openD(id) {
    var dl = d.getElementById(id);
    if (!dl || dl.tagName !== 'DIALOG') return;
    if (id !== 'lightbox') $$('dialog[open]').forEach(function (x) { if (x !== dl) closeD(x, true); });
    if (!dl.open) { if (dl.showModal) dl.showModal(); else dl.setAttribute('open', ''); }
    if (dl.classList.contains('pm')) { dl.scrollTop = 0; try { history.replaceState(null, '', '#' + id); } catch (e) {} }
    root.classList.add('modal-open');
    if (id === 'menu') chapBtn.setAttribute('aria-expanded', 'true');
    $$('video', dl).forEach(function (v) { v.muted = true; tryPlay(v); });
  }
  function closeD(dl, keepHash) {
    if (!dl) return;
    if (dl.close) dl.close(); else { dl.removeAttribute('open'); dl.dispatchEvent(new Event('close')); }
  }
  $$('dialog').forEach(function (dl) {
    dl.addEventListener('close', function () {
      $$('video', dl).forEach(function (v) { v.pause(); });
      if (dl.id === 'menu') chapBtn.setAttribute('aria-expanded', 'false');
      if (dl.id === 'lightbox') $('#lbStage').innerHTML = '';
      if (!anyOpen()) {
        root.classList.remove('modal-open');
        if (/^#(m-|docs)/.test(location.hash)) { try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {} }
      }
    });
    dl.addEventListener('click', function (e) { if (e.target === dl) closeD(dl); });
  });
  chapBtn.addEventListener('click', function () { openD('menu'); });
  d.addEventListener('click', function (e) {
    var t = e.target.closest('[data-open],[data-close],[data-close-go],[data-go],[data-jump],[data-album]');
    if (!t) return;
    if (t.hasAttribute('data-open')) { e.preventDefault(); openD(t.getAttribute('data-open')); return; }
    if (t.hasAttribute('data-jump')) {
      e.preventDefault();
      var tg = d.getElementById(t.getAttribute('href').slice(1));
      if (tg) tg.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
      return;
    }
    if (t.hasAttribute('data-album')) { e.preventDefault(); openAlbum(t.getAttribute('data-album')); return; }
    var target = t.getAttribute('data-go') || t.getAttribute('data-close-go');
    if (t.hasAttribute('data-close')) {
      e.preventDefault();
      closeD(t.closest('dialog'));
      var h = t.getAttribute('href');
      if (h && h.length > 1) setTimeout(function () { go(h.slice(1)); }, 60);
      return;
    }
    if (target) {
      e.preventDefault();
      var open = anyOpen();
      if (open) closeD(open);
      setTimeout(function () { go(target); }, open ? 60 : 0);
    }
  });
  function openFromHash() {
    var h = location.hash.slice(1);
    if (/^m-/.test(h) || h === 'docs') openD(h);
  }
  openFromHash();
  addEventListener('hashchange', openFromHash);

  /* ---------------- альбомы: разделы галереи и направления кружков ---------------- */
  var escH = function (v) { return String(v == null ? '' : v).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var ALB = {}, albKey = null, lbIndex = 0, lbList = [];
  try { ALB = JSON.parse($('#albumData').textContent); } catch (e) {}
  var playIco = ($('#albumPlay') || {}).innerHTML || '';
  function renderAlbum(k) {
    var a = ALB[k]; if (!a) return false;
    albKey = k;
    $('#albumT').textContent = a.t;
    var sub = $('#albumSub'); sub.textContent = a.sub || ''; sub.hidden = !a.sub;
    $('#albumTabs').innerHTML = Object.keys(ALB).filter(function (x) { return ALB[x].g === a.g; }).map(function (x) {
      var on = x === k;
      return '<button type="button" data-album-tab="' + x + '" aria-pressed="' + on + '"' + (on ? ' class="is-on"' : '') + '>' + escH(ALB[x].t) + '<small>' + ALB[x].items.length + '</small></button>';
    }).join('');
    $('#albumGrid').innerHTML = a.items.map(function (it, i) {
      return '<button type="button" class="album__it" data-i="' + i + '" aria-label="' + escH(it.alt) + '"><img src="' + escH(it.th) + '" alt="" loading="lazy">' + (it.k === 'v' ? '<span class="album__play">' + playIco + '</span>' : '') + '</button>';
    }).join('');
    $('#album').scrollTop = 0;
    showTab();
    return true;
  }
  function showTab() {  /* активный раздел виден в ленте вкладок */
    var tabs = $('#albumTabs'), tab = $('#albumTabs .is-on');
    if (tab && tabs.clientWidth) tabs.scrollLeft = Math.max(0, tab.offsetLeft - (tabs.clientWidth - tab.offsetWidth) / 2);
  }
  function openAlbum(k) { if (renderAlbum(k)) { openD('album'); showTab(); } }
  (function () {
    var dlg = $('#album'); if (!dlg) return;
    dlg.addEventListener('click', function (e) {
      var tb = e.target.closest('[data-album-tab]');
      if (tb) { renderAlbum(tb.getAttribute('data-album-tab')); return; }
      var it = e.target.closest('.album__it');
      if (it) { lbList = ALB[albKey].items; openD('lightbox'); lbShow(+it.dataset.i); }
    });
  })();
  function lbShow(i) {
    if (!lbList.length) return;
    lbIndex = (i + lbList.length) % lbList.length;
    var it = lbList[lbIndex], stage = $('#lbStage');
    stage.innerHTML = '';
    var m;
    if (it.k === 'v') {
      m = d.createElement('video');
      m.src = it.full; m.poster = it.th; m.controls = true; m.playsInline = true; m.loop = true; m.autoplay = true; m.muted = true;
      m.setAttribute('aria-label', it.alt);
    } else {
      m = d.createElement('img'); m.src = it.full; m.alt = it.alt;
    }
    stage.appendChild(m);
    $('#lbCap').textContent = it.alt + '  ·  ' + (lbIndex + 1) + ' из ' + lbList.length;
    if (m.tagName === 'VIDEO') tryPlay(m);
  }
  $$('[data-lb]').forEach(function (b) { b.addEventListener('click', function () { lbShow(lbIndex + (+b.dataset.lb)); }); });
  addEventListener('keydown', function (e) {
    var lb = $('#lightbox');
    if (!lb || !lb.open) return;
    if (e.key === 'ArrowRight') lbShow(lbIndex + 1);
    if (e.key === 'ArrowLeft') lbShow(lbIndex - 1);
  });
  /* свайп в лайтбоксе на телефоне */
  (function () {
    var lb = $('#lightbox'); if (!lb) return;
    var x0 = null, y0 = 0;
    lb.addEventListener('touchstart', function (e) { var t = e.touches[0]; x0 = t.clientX; y0 = t.clientY; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var t = e.changedTouches[0], dx = t.clientX - x0, dy = t.clientY - y0; x0 = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) lbShow(lbIndex + (dx < 0 ? 1 : -1));
    }, { passive: true });
  })();

  /* ---------------- отзывы: листание ---------------- */
  $$('.carousel').forEach(function (c) {
    var tr = $('.carousel__track', c);
    $$('.carousel__nav button', c).forEach(function (b) {
      b.addEventListener('click', function () {
        var card = tr.firstElementChild, step = card ? card.getBoundingClientRect().width + 16 : 300;
        tr.scrollBy({ left: step * (+b.dataset.dir), behavior: reduce ? 'auto' : 'smooth' });
      });
    });
  });

  /* ---------------- новости и объявления: assets/data/news.json ---------------- */
  (function () {
    var list = $('#newsList'), sec = $('#news');
    if (!list) return;
    var esc = escH;
    var arrow = '<svg class="i" aria-hidden="true"><use href="#i-arrow-right"/></svg>';
    var fmtDate = function (s) {
      var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
      if (!m) return s || '';
      var mon = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
      return (+m[3]) + ' ' + mon[+m[2] - 1] + ' ' + m[1];
    };
    var safe = function (u) { return /^(#|https?:|tel:|mailto:|\/|\.\/|[\w-]+\.html)/i.test(String(u || '').trim()) ? u : ''; };
    function render(items) {
      items = (items || []).filter(function (n) { return n && n.title; });
      items.forEach(function (n) { n.link = safe(n.link); n.image = /^(https?:|assets\/|\.\/|\/)/i.test(String(n.image || '')) ? n.image : ''; });
      if (!items.length) { sec.hidden = true; return; }
      items.sort(function (a, b) { return (b.pin ? 1 : 0) - (a.pin ? 1 : 0) || String(b.date || '').localeCompare(String(a.date || '')); });
      list.innerHTML = items.map(function (n) {
        return '<article class="news__card is-in' + (n.pin ? ' is-pin' : '') + '">' +
          (n.image ? '<img src="' + esc(n.image) + '" alt="" loading="lazy">' : '') +
          '<div class="news__meta">' + (n.tag ? '<span class="news__tag">' + esc(n.tag) + '</span>' : '') + (n.date ? '<time datetime="' + esc(n.date) + '">' + esc(fmtDate(n.date)) + '</time>' : '') + '</div>' +
          '<h3>' + esc(n.title) + '</h3><p>' + esc(n.text) + '</p>' +
          (n.link ? '<a class="news__more" href="' + esc(n.link) + '"' + (/^https?:/.test(n.link) ? ' target="_blank" rel="noopener"' : '') + '>' + esc(n.link_text || 'Подробнее') + arrow + '</a>' : '') +
          '</article>';
      }).join('');
    }
    var seed = [];
    try { seed = JSON.parse($('#newsSeed').textContent); } catch (e) {}
    if (location.protocol === 'file:') { render(seed); return; }
    fetch('assets/data/news.json', { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(render).catch(function () { render(seed); });
  })();

  /* ---------------- форма записи ---------------- */
  (function () {
    var form = $('#signupForm'), sent = $('#signupSent');
    if (!form) return;
    var C = { wa: 'https://wa.me/79781600505' };
    var field = function (name) { return form.elements.namedItem(name); };
    function showSent(ok, text) {
      form.hidden = true; sent.hidden = false;
      if (ok) { $('#sentTitle').textContent = 'Заявка отправлена'; $('#sentText').textContent = 'Перезвоним в течение рабочего дня. Хотите быстрее — напишите нам:'; }
      $('#sentWa').href = C.wa + '?text=' + encodeURIComponent(text);
      sent.focus();
    }
    form.addEventListener('input', function (e) { var f = e.target.closest('.field'); if (f) f.classList.remove('is-bad'); });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = field('name').value.trim(), age = field('age').value.trim(), phone = field('phone').value.trim();
      var badName = !name, badPhone = phone.replace(/\D/g, '').length < 10;
      field('name').closest('.field').classList.toggle('is-bad', badName);
      field('phone').closest('.field').classList.toggle('is-bad', badPhone);
      if (badName || badPhone) { (badName ? field('name') : field('phone')).focus(); return; }
      var text = 'Здравствуйте! Хочу записаться на пробные дни в Ай Про.\nИмя: ' + name + (age ? '\nВозраст ребёнка: ' + age : '') + '\nТелефон: ' + phone;
      var ep = form.dataset.endpoint;
      if (!ep) { showSent(false, text); return; }
      var btn = $('.form__go', form); btn.disabled = true;
      fetch(ep, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ name: name, age: age, phone: phone }) })
        .then(function (r) { showSent(r.ok, text); }).catch(function () { showSent(false, text); })
        .then(function () { btn.disabled = false; });
    });
    $('#sentBack').addEventListener('click', function () { sent.hidden = true; form.hidden = false; field('name').focus(); });
  })();

  /* ---------------- помощник «Вопросы?» ---------------- */
  (function () {
    var log = $('#helperLog'), qs = $('#helperQs'), data = [];
    if (!log) return;
    try { data = JSON.parse($('#helperData').textContent); } catch (e) {}
    var bub = function (text, me) { var p = d.createElement('p'); p.className = 'bub' + (me ? ' bub--me' : ''); p.textContent = text; log.appendChild(p); log.scrollTop = log.scrollHeight; return p; };
    qs.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-q]'); if (!b) return;
      var item = data[+b.dataset.q]; if (!item) return;
      bub(item.q, true);
      var dots = d.createElement('p'); dots.className = 'bub bub--dots'; dots.setAttribute('aria-label', 'Помощник печатает'); dots.innerHTML = '<i></i><i></i><i></i>';
      log.appendChild(dots); log.scrollTop = log.scrollHeight;
      setTimeout(function () { dots.remove(); item.a.forEach(function (a) { bub(a); }); }, reduce ? 0 : 650);
    });
  })();

  /* ---------------- версия для слабовидящих ---------------- */
  function syncA11y() {
    var on = isA11y();
    $$('.a11y-toggle').forEach(function (b) { b.setAttribute('aria-pressed', on ? 'true' : 'false'); });
  }
  $$('.a11y-toggle').forEach(function (b) {
    b.addEventListener('click', function () {
      var on = !isA11y();
      root.classList.toggle('a11y', on);
      try { localStorage.setItem('ipro-a11y', on ? '1' : '0'); } catch (e) {}
      syncA11y();
      if (!on) { seqs.forEach(function (q) { q.size(); q.load(); }); frame(); }
    });
  });
  syncA11y();

  /* ---------------- карта в подвале: грузим, когда подвал рядом ---------------- */
  var map = $('.foot__map iframe');
  if (map) new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { map.src = map.dataset.src; o.disconnect(); } }, { rootMargin: '400px 0px' }).observe(map);
})();
