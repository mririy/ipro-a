/* =====================================================================
   Ай Про (IPROSCHOOL) — сценарий сайта, версия A
   Один день в школе: глава переключается, когда её заголовок пересекает 40 % окна;
   шкала дня 08:30 → 18:00 заполняется при прокрутке. Видео: сначала постер, у каждого — пауза.
   Окна программ, альбомы, форма записи, новости, помощник, версия для слабовидящих.
   ===================================================================== */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');
  var reduce = reduceMQ.matches;
  if (reduceMQ.addEventListener) reduceMQ.addEventListener('change', function (e) { reduce = e.matches; });
  var wideMQ = matchMedia('(min-width: 1024px)');
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return [].slice.call((c || d).querySelectorAll(s)); };
  var clamp01 = function (v) { return Math.max(0, Math.min(1, v)); };
  var isA11y = function () { return root.classList.contains('a11y'); };
  var tryPlay = function (v) { var p = v.play(); if (p && p.catch) p.catch(function () {}); };
  var still = function () { return reduce || isA11y(); };
  function anyOpen() { return $('dialog[open]'); }

  /* ---------------- видео: кнопки паузы ---------------- */
  function setVBtn(b, paused) {
    if (!b) return;
    b.setAttribute('aria-pressed', paused ? 'true' : 'false');
    b.setAttribute('aria-label', paused ? 'Включить видео' : 'Остановить видео');
  }
  var introV = $('.intro__v'), heroBtn = $('.vbtn--hero');
  $$('[data-vtoggle]').forEach(function (b) {
    var v = b.parentElement.querySelector('video');
    if (!v) return;
    setVBtn(b, true);
    v.addEventListener('play', function () { setVBtn(b, false); });
    v.addEventListener('pause', function () { setVBtn(b, true); });
    b.addEventListener('click', function () {
      if (v.paused) {
        v._userPaused = false;
        if (v === introV && !v.getAttribute('src')) startHero(true);
        tryPlay(v);
      } else { v._userPaused = true; v.pause(); }
    });
  });

  /* ---------------- первый экран: постер сразу, видео — после загрузки страницы ---------------- */
  var heroStarted = false;
  var portMQ = matchMedia('(orientation: portrait) and (max-width: 1023px)');
  function heroSrc() { return portMQ.matches ? introV.dataset.srcPort : introV.dataset.srcLand; }
  function startHero(force) {
    if (!introV) return;
    heroStarted = true;
    if (introV.getAttribute('src') !== heroSrc()) introV.src = heroSrc();
    introV.muted = true;
    if (force || (!still() && !introV._userPaused)) tryPlay(introV);
  }
  if (introV) {
    var kick = function () { setTimeout(function () { startHero(false); }, 150); };
    if (d.readyState === 'complete') kick(); else addEventListener('load', kick);
    if (portMQ.addEventListener) portMQ.addEventListener('change', function () { if (heroStarted) startHero(false); });
  }

  /* постеры видео в блоках — когда блок рядом; на телефоне — уменьшенная копия */
  var posterIO = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      var v = e.target; posterIO.unobserve(v);
      var big = v.clientWidth * Math.min(window.devicePixelRatio || 1, 2) > 700;
      v.poster = big ? v.dataset.poster : (v.dataset.posterSm || v.dataset.poster);
    });
  }, { rootMargin: '800px 0px' });
  $$('video[data-poster]').forEach(function (v) { posterIO.observe(v); });

  /* видео в блоках: играют, только когда на экране; при «Уменьшить движение» — постер и кнопка */
  var vidIO = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      var v = e.target;
      if (e.isIntersecting) { if (v.paused && !v._userPaused && !still()) tryPlay(v); }
      else if (!v.paused) v.pause();
    });
  }, { threshold: 0.35 });
  $$('main video').forEach(function (v) { v.muted = true; if (v !== introV) vidIO.observe(v); });

  /* ---------------- шапка, главы, шкала дня ---------------- */
  var hdr = $('#hdr'), chTime = $('#chTime'), chName = $('#chName'), menuBtn = $('#menuBtn');
  var intro = $('.intro'), sheet = $('.drw__sheet');
  var scenes = $$('main .sec');
  var heads = scenes.map(function (s) { return $('.sec__head', s) || s; });
  var themeMeta = $('meta[name="theme-color"]');
  var BG = { white: '#FFFFFF', alt: '#F4F7FB', navy: '#0A2C55' };
  var active = -2;
  function bgOf(s) { var m = / bg-(\w+)/.exec(' ' + s.className); return m ? BG[m[1]] : '#FFFFFF'; }
  function setActive(i) {
    if (i === active) return;
    active = i;
    var s = i >= 0 ? scenes[i] : null, id = s ? s.id : 'top';
    if (chTime) chTime.textContent = s ? (s.dataset.time || '') : '';
    if (chName) chName.textContent = s ? (s.dataset.short || s.dataset.title || '') : '';
    $$('.menu a[data-go], .hdr__nav a').forEach(function (a) { a.setAttribute('aria-current', a.dataset.go === id ? 'true' : 'false'); });
    if (themeMeta) themeMeta.setAttribute('content', s ? bgOf(s) : '#0A2C55');
  }

  var toMin = function (t) { var m = /^(\d{1,2}):(\d{2})$/.exec(t || ''); return m ? (+m[1]) * 60 + (+m[2]) : 0; };
  var dayEls = ['programs', 'food', 'extra', 'transfer'].map(function (k) { return d.getElementById(k); }).filter(Boolean);
  var dayMin = dayEls.map(function (el) { return toMin(el.dataset.time); });
  var D0 = dayMin[0], D1 = dayMin[dayMin.length - 1];
  var tlPts = $$('.tl__pt'), rail = $('.rail'), railPts = $$('.rail__pt');
  function dayNow(line) {
    if (!dayEls.length) return null;
    var y = scrollY + line;
    var ys = dayEls.map(function (el) { return ($('.sec__head', el) || el).getBoundingClientRect().top + scrollY; });
    var last = dayEls[dayEls.length - 1], end = last.getBoundingClientRect().bottom + scrollY;
    if (y < ys[0] || y > end) return null;
    for (var k = 0; k < ys.length - 1; k++) {
      if (y < ys[k + 1]) return dayMin[k] + (dayMin[k + 1] - dayMin[k]) * clamp01((y - ys[k]) / (ys[k + 1] - ys[k]));
    }
    return D1;
  }
  function markDay(pts, m) {
    pts.forEach(function (p, k) {
      var t = dayMin[k], next = k + 1 < dayMin.length ? dayMin[k + 1] : Infinity;
      p.classList.toggle('is-now', m !== null && m >= t - 0.5 && m < next - 0.5);
      p.classList.toggle('is-past', m !== null && m >= next - 0.5);
    });
  }

  /* нижняя панель на телефоне: после первого экрана, кроме записи и подвала */
  var bbar = $('.bbar'), atSignup = false, nearFoot = false;
  function updBar() {
    if (!bbar) return;
    bbar.classList.toggle('is-on', scrollY > innerHeight * 0.6 && !atSignup && !nearFoot && !anyOpen());
  }
  var endIO = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.target.id === 'signup') atSignup = e.isIntersecting; else nearFoot = e.isIntersecting; });
    root.classList.toggle('at-signup', atSignup);
    updBar();
  }, { threshold: 0.12 });
  ['signup', 'contacts'].forEach(function (id) { var el = d.getElementById(id); if (el) endIO.observe(el); });

  var ticking = false;
  function frame() {
    ticking = false;
    var vh = innerHeight, line = vh * 0.4;
    /* лист-дровер: видео тускнеет и встаёт на паузу, когда лист его закрыл */
    var sheetTop = sheet ? sheet.getBoundingClientRect().top : -1;
    var onHero = sheetTop > (hdr ? hdr.offsetHeight : 56) - 1;
    if (hdr) hdr.classList.toggle('is-hero', onHero);
    root.classList.toggle('on-hero', onHero);
    if (intro) intro.style.setProperty('--dp', still() ? 0 : clamp01(scrollY / vh).toFixed(3));
    if (sheet) sheet.style.setProperty('--sh', clamp01(scrollY / 80).toFixed(2));
    if (introV && heroStarted) {
      if (sheetTop <= 0) { if (!introV.paused) { introV.pause(); introV._covered = true; } }
      else if (introV._covered && introV.paused && !introV._userPaused) { introV._covered = false; tryPlay(introV); }
    }
    /* глава — последняя, чей заголовок пересёк 40 % высоты окна */
    var idx = -1;
    for (var i = 0; i < heads.length; i++) { if (heads[i].getBoundingClientRect().top <= line) idx = i; else break; }
    setActive(onHero ? -1 : idx);
    /* шкала дня */
    var m = onHero ? null : dayNow(line);
    var inDay = m !== null;
    if (hdr) hdr.classList.toggle('in-day', inDay);
    if (rail) rail.classList.toggle('is-on', inDay && !wideMQ.matches && !isA11y());
    if (inDay) root.style.setProperty('--p', clamp01((m - D0) / (D1 - D0)).toFixed(4));
    markDay(tlPts, m); markDay(railPts, m);
    updBar();
    updSeqs(); updRoute();
  }
  addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }, { passive: true });

  function go(target) {
    var el = typeof target === 'string' ? d.getElementById(target) : target;
    if (!el) return;
    el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  }
  addEventListener('keydown', function (e) {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey || anyOpen()) return;
    var t = e.target;
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || (t.closest && t.closest('.hs')))) return;
    if (e.key === 'ArrowRight') { e.preventDefault(); go(scenes[Math.min(scenes.length - 1, active + 1)]); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); go(active <= 0 ? 'top' : scenes[active - 1]); }
  });

  /* ---------------- появление: один короткий fade ---------------- */
  var revealIO = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('is-in'); revealIO.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -4% 0px', threshold: 0.06 });
  $$('.rv').forEach(function (el) { revealIO.observe(el); });
  root.classList.add('rv-ready');

  /* ---------------- 3D-макет: кадры меняются, пока блок проходит через экран ---------------- */
  var seqs = [];
  $$('[data-seq]').forEach(function (el) {
    var n = +el.dataset.frames, path = el.dataset.path, ext = el.dataset.ext;
    var canvas = $('canvas', el), ctx = canvas.getContext('2d');
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
      W = Math.round(el.clientWidth * dpr); H = Math.round(el.clientHeight * dpr);
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
      if (j < 0 || j === drawn || !W) return;
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
    var st = { el: el, cur: 0, n: n, draw: draw, size: size, load: load };
    seqs.push(st);
    new IntersectionObserver(function (es) { if (es[0].isIntersecting && !still()) { size(); load(); } }, { rootMargin: '100% 0px' }).observe(el);
  });
  function updSeqs() {
    if (still()) return;
    var vh = innerHeight;
    seqs.forEach(function (q) {
      var r = q.el.getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) return;
      var p = clamp01(((vh - r.top) / (vh + r.height) - 0.12) / 0.76);
      var i = Math.round(p * (q.n - 1));
      q.cur = i; q.draw(i);
    });
  }

  /* ---------------- трансфер: автобус едет по маршруту ---------------- */
  var route = $('[data-route]'), rPath = route && $('.route__line', route), rDone = route && $('.route__done', route), rBus = route && $('.route__bus', route), rSvg = route && $('svg', route);
  var rLen = 0, stopW = -1, stopLen = 0;
  if (rPath) { rLen = rPath.getTotalLength(); rDone.setAttribute('pathLength', '1'); rDone.style.strokeDasharray = '1 1'; }
  function updRoute() {
    if (!rPath) return;
    var r = route.getBoundingClientRect(), vh = innerHeight;
    if (r.bottom < -100 || r.top > vh + 100) return;
    var p = still() ? 1 : clamp01((vh * 0.95 - r.top) / (vh * 0.55));
    rDone.style.strokeDashoffset = (1 - p).toFixed(4);
    var sr = rSvg.getBoundingClientRect(), sx = sr.width / 1000, sy = sr.height / 160;
    if (stopW !== sr.width) {  /* автобус останавливается перед школой, не наезжая на неё */
      stopW = sr.width; stopLen = rLen;
      var end = rPath.getPointAtLength(rLen);
      for (var k = rLen; k > 0; k -= rLen / 240) { var q = rPath.getPointAtLength(k); if (Math.hypot((end.x - q.x) * sx, (end.y - q.y) * sy) >= 46) { stopLen = k; break; } }
    }
    var pt = rPath.getPointAtLength(stopLen * p), pt2 = rPath.getPointAtLength(Math.min(rLen, stopLen * p + 2));
    var x = (sr.left - r.left) + pt.x * sx, y = (sr.top - r.top) + pt.y * sy;
    var ang = Math.atan2((pt2.y - pt.y) * sy, (pt2.x - pt.x) * sx) * 180 / Math.PI;
    rBus.style.setProperty('--bx', x.toFixed(1) + 'px');
    rBus.style.setProperty('--by', y.toFixed(1) + 'px');
    rBus.style.setProperty('--br', Math.max(-20, Math.min(20, ang)).toFixed(1) + 'deg');
  }

  addEventListener('resize', function () { seqs.forEach(function (q) { q.size(); q.draw(q.cur); }); frame(); });
  frame();

  /* ---------------- окна: меню, программы, сведения, альбом, помощник ---------------- */
  function openD(id) {
    var dl = d.getElementById(id);
    if (!dl || dl.tagName !== 'DIALOG') return;
    if (id !== 'lightbox') $$('dialog[open]').forEach(function (x) { if (x !== dl) closeD(x); });
    if (!dl.open) { if (dl.showModal) dl.showModal(); else dl.setAttribute('open', ''); }
    if (dl.classList.contains('pm')) { dl.scrollTop = 0; try { history.replaceState(null, '', '#' + id); } catch (e) {} }
    root.classList.add('modal-open');
    if (id === 'menu' && menuBtn) menuBtn.setAttribute('aria-expanded', 'true');
    updBar();
  }
  function closeD(dl) {
    if (!dl) return;
    if (dl.close) dl.close(); else { dl.removeAttribute('open'); dl.dispatchEvent(new Event('close')); }
  }
  $$('dialog').forEach(function (dl) {
    dl.addEventListener('close', function () {
      $$('video', dl).forEach(function (v) { v.pause(); });
      if (dl.id === 'menu' && menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
      if (dl.id === 'lightbox') $('#lbStage').innerHTML = '';
      if (!anyOpen()) {
        root.classList.remove('modal-open');
        if (/^#(m-|docs)/.test(location.hash)) { try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {} }
      }
      updBar();
    });
    dl.addEventListener('click', function (e) { if (e.target === dl) closeD(dl); });
  });
  if (menuBtn) menuBtn.addEventListener('click', function () { openD('menu'); });
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

  /* ---------------- альбомы галереи и просмотр ---------------- */
  var escH = function (v) { return String(v == null ? '' : v).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var ALB = {}, albKey = null, lbIndex = 0, lbList = [];
  try { ALB = JSON.parse($('#albumData').textContent); } catch (e) {}
  var playIco = ($('#albumPlay') || {}).innerHTML || '';
  function renderAlbum(k) {
    var a = ALB[k]; if (!a) return false;
    albKey = k;
    $('#albumT').textContent = a.t;
    $('#albumTabs').innerHTML = Object.keys(ALB).map(function (x) {
      var on = x === k;
      return '<button type="button" data-album-tab="' + x + '" aria-pressed="' + on + '"' + (on ? ' class="is-on"' : '') + '>' + escH(ALB[x].t) + '<small>' + ALB[x].items.length + '</small></button>';
    }).join('');
    $('#albumGrid').innerHTML = a.items.map(function (it, i) {
      return '<button type="button" class="album__it" data-i="' + i + '" aria-label="' + escH(it.alt) + (it.k === 'v' ? ' (видео)' : '') + '"><img src="' + escH(it.th) + '" alt="" loading="lazy">' + (it.k === 'v' ? '<span class="album__play">' + playIco + '</span>' : '') + '</button>';
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
      m.src = it.full; m.poster = it.th; m.controls = true; m.playsInline = true; m.loop = true; m.muted = true;
      if (!still()) m.autoplay = true;
      m.setAttribute('aria-label', it.alt);
    } else {
      m = d.createElement('img'); m.src = it.full; m.alt = it.alt;
    }
    stage.appendChild(m);
    $('#lbCap').textContent = it.alt + '  ·  ' + (lbIndex + 1) + ' из ' + lbList.length;
    if (m.tagName === 'VIDEO' && !still()) tryPlay(m);
  }
  $$('[data-lb]').forEach(function (b) { b.addEventListener('click', function () { lbShow(lbIndex + (+b.dataset.lb)); }); });
  addEventListener('keydown', function (e) {
    var lb = $('#lightbox');
    if (!lb || !lb.open) return;
    if (e.key === 'ArrowRight') lbShow(lbIndex + 1);
    if (e.key === 'ArrowLeft') lbShow(lbIndex - 1);
  });
  (function () {  /* свайп в просмотре на телефоне */
    var lb = $('#lightbox'); if (!lb) return;
    var x0 = null, y0 = 0;
    lb.addEventListener('touchstart', function (e) { var t = e.touches[0]; x0 = t.clientX; y0 = t.clientY; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var t = e.changedTouches[0], dx = t.clientX - x0, dy = t.clientY - y0; x0 = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) lbShow(lbIndex + (dx < 0 ? 1 : -1));
    }, { passive: true });
  })();

  /* ---------------- отзывы: листание кнопками ---------------- */
  $$('.carousel').forEach(function (c) {
    var tr = $('.carousel__track', c), nav = $('.carousel__nav', c);
    /* стрелки нужны, только если отзывы не помещаются */
    var fit = function () { if (nav) nav.hidden = tr.scrollWidth <= tr.clientWidth + 2; };
    fit(); addEventListener('resize', fit);
    $$('.carousel__nav button', c).forEach(function (b) {
      b.addEventListener('click', function () {
        var card = tr.firstElementChild, step = card ? card.getBoundingClientRect().width + 12 : 300;
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
        var meta = (n.tag ? '<span class="ncard__tag">' + esc(n.tag) + '</span>' : '') + (n.date ? '<time datetime="' + esc(n.date) + '">' + esc(fmtDate(n.date)) + '</time>' : '');
        return '<article class="ncard is-in' + (n.pin ? ' is-pin' : '') + '">' +
          (n.image ? '<img src="' + esc(n.image) + '" alt="" loading="lazy">' : '') +
          (meta ? '<p class="ncard__meta">' + meta + '</p>' : '') +
          '<h3 class="ncard__t">' + esc(n.title) + '</h3><p class="ncard__x">' + esc(n.text) + '</p>' +
          (n.link ? '<a class="lnk" href="' + esc(n.link) + '"' + (/^https?:/.test(n.link) ? ' target="_blank" rel="noopener"' : '') + '>' + esc(n.link_text || 'Подробнее') + arrow + '</a>' : '') +
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
      setTimeout(function () { dots.remove(); item.a.forEach(function (a) { bub(a); }); }, reduce ? 0 : 500);
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
      if (on) $$('main video').forEach(function (v) { v.pause(); });
      else { seqs.forEach(function (q) { q.size(); q.load(); }); }
      frame();
    });
  });
  syncA11y();

  /* ---------------- карта в подвале: грузим, когда подвал рядом ---------------- */
  var map = $('.foot__map iframe');
  if (map) new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { map.src = map.dataset.src; o.disconnect(); } }, { rootMargin: '400px 0px' }).observe(map);
})();
