/* =====================================================================
   Ай Про · IPROSCHOOL — сценарий сайта, версия A «День под солнцем»
   Всё листается только вниз. Солнце из логотипа раскрывается в видео, камера подлетает к особняку,
   главы дня отмечены часами (солнце идёт по дуге, часы «доходят» до своего времени),
   карточки программ ложатся стопкой, автобус едет по маршруту, ночью камера отъезжает от особняка.
   Плюс окна программ, меню, сведения, альбомы, форма записи, новости, помощник, версия для слабовидящих.
   ===================================================================== */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');
  var reduce = reduceMQ.matches;
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return [].slice.call((c || d).querySelectorAll(s)); };
  var clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var ease = function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  var easeOut = function (t) { return 1 - (1 - t) * (1 - t); };
  var seg = function (p, a, b) { return clamp((p - a) / (b - a), 0, 1); };
  var isA11y = function () { return root.classList.contains('a11y'); };
  var still = function () { return reduce || isA11y(); };  /* без движения: настройка системы или версия для слабовидящих */
  var tryPlay = function (v) { var p = v.play(); if (p && p.catch) p.catch(function () {}); };
  var hasIO = 'IntersectionObserver' in window;
  function watch(els, opts, cb) {
    if (!hasIO) { els.forEach(function (el) { cb(el, true, null); }); return null; }
    var o = new IntersectionObserver(function (es) { es.forEach(function (e) { cb(e.target, e.isIntersecting, o); }); }, opts);
    els.forEach(function (el) { o.observe(el); });
    return o;
  }
  var vw = innerWidth, vh = innerHeight, wide = vw >= 900;

  /* ---------------- первый экран: вертикальное видео на телефоне, горизонтальное на компьютере ---------------- */
  var introV = $('.intro__v');
  (function () {
    if (!introV) return;
    var mq = matchMedia('(orientation: portrait) and (max-width: 820px)');
    var pick = function () {
      var port = mq.matches, src = port ? introV.dataset.srcPort : introV.dataset.srcLand;
      if (introV.getAttribute('src') === src) return;
      introV.setAttribute('poster', port ? introV.dataset.posterPort : introV.dataset.posterLand);
      introV.src = src; introV.muted = true; tryPlay(introV);
    };
    pick();
    if (mq.addEventListener) mq.addEventListener('change', pick);
  })();

  /* ---------------- главы: название в шапке, пункт меню, цвет полосы браузера ---------------- */
  var scenes = $$('main > .sc'), hd = $('#hd'), chapName = $('#chapName'), menuBtn = $('#menuBtn'), ask = $('.ask');
  var themeMeta = $('meta[name="theme-color"]');
  var MENU_OF = { concept: 'concept', about: 'concept', programs: 'programs', food: 'food', teachers: 'teachers', safety: 'safety', extra: 'extra', transfer: 'transfer', summer: 'summer', reviews: 'reviews', news: 'news', gallery: 'gallery' };
  var active = -1;
  function setActive(i) {
    if (i < 0 || i === active) return;
    active = i;
    var s = scenes[i];
    if (chapName) chapName.textContent = s.id === 'top' ? '' : (s.dataset.title || '');
    var m = MENU_OF[s.id];
    $$('.menu a[data-go]').forEach(function (a) { a.setAttribute('aria-current', a.dataset.go === m ? 'true' : 'false'); });
    if (themeMeta) themeMeta.setAttribute('content', s.style.getPropertyValue('--s1').trim() || '#0A2C55');
    if (ask) ask.classList.toggle('is-hidden', s.id === 'top' || s.id === 'act-night' || s.id === 'signup');
  }
  /* активная глава — последняя (по порядку) из тех, что пересекают середину экрана */
  var crossing = [];
  if (hasIO) {
    var sceneIO = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        var k = crossing.indexOf(e.target);
        if (e.isIntersecting && k < 0) crossing.push(e.target);
        if (!e.isIntersecting && k >= 0) crossing.splice(k, 1);
      });
      var idx = -1;
      scenes.forEach(function (s, i) { if (crossing.indexOf(s) >= 0) idx = i; });
      setActive(idx);
    }, { rootMargin: '-50% 0px -49% 0px' });
    scenes.forEach(function (s) { sceneIO.observe(s); });
  }
  setActive(0);

  function go(target) {
    var el = typeof target === 'string' ? d.getElementById(target) : target;
    if (!el) return;
    if (el.id === 'top') { scrollTo({ top: 0, behavior: still() ? 'auto' : 'smooth' }); return; }
    el.scrollIntoView({ behavior: still() ? 'auto' : 'smooth', block: 'start' });
  }

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
  if (hasIO) {
    watch($$('.rv, [data-split]'), { rootMargin: '0px 0px -8% 0px', threshold: 0.12 }, function (el, on, o) {
      if (on) { el.classList.add('is-in'); o.unobserve(el); }
    });
    root.classList.add('rv-ready');
  }

  /* ---------------- видео: играет только то, что на экране ---------------- */
  watch($$('main video').filter(function (v) { return v !== introV; }), { threshold: 0.25 }, function (v, on) {
    v.muted = true;
    if (on && !reduce) { if (v.paused) tryPlay(v); }
    else if (!v.paused) v.pause();
  });
  /* видео первого экрана видно в круге-солнце (clip-path), поэтому следим за всей сценой, а не за самим видео */
  var heroSc = $('.hero');
  if (introV && heroSc) watch([heroSc], { threshold: 0 }, function (el, on) {
    introV.muted = true;
    if (on) { if (introV.paused) tryPlay(introV); }
    else if (!introV.paused) introV.pause();
  });

  /* ---------------- цифры набегают ---------------- */
  watch($$('[data-count]'), { threshold: 0.6 }, function (el, on, o) {
    if (!on) return;
    if (o) o.unobserve(el);
    if (still()) return;
    var to = +el.dataset.count, from = to > 1000 ? to - 25 : 0, suffix = el.textContent.replace(/[0-9]/g, ''), t0 = performance.now();
    (function tick(now) {
      var p = Math.min(1, (now - t0) / 1400);
      el.textContent = Math.round(lerp(from, to, easeOut(p))) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    })(t0);
  });

  /* ---------------- покадровые сцены 3D-макета: утро (подлёт) и ночь (отъезд) ---------------- */
  function Seq(el, bg) {
    this.el = el; this.c = $('canvas', el); this.ctx = this.c.getContext('2d');
    this.n = +el.dataset.frames; this.path = el.dataset.path; this.ext = el.dataset.ext || 'webp'; this.bg = bg;
    this.imgs = []; this.cur = 0; this.drawn = -1; this.fit = -1; this.w = 0; this.h = 0; this.dpr = 1;
    this.offX = 0; this.offY = 0; this.box = null;
    var n = this.n, order = [0, n - 1], seen = {};
    for (var k = 2; k < n; k *= 2) for (var j = 1; j < k; j++) order.push(Math.round(j * (n - 1) / k));
    for (var i = 0; i < n; i++) order.push(i);
    this.order = order.filter(function (x) { if (seen[x]) return false; seen[x] = 1; return true; });
  }
  Seq.prototype.start = function () {
    if (this.started) return;
    this.started = true;
    var self = this, q = this.order.slice();
    var next = function () {
      if (!q.length) return;
      var i = q.shift(), im = new Image();
      im.decoding = 'async';
      im.onload = function () { self.imgs[i] = im; if (i === self.cur || self.drawn < 0) { self.drawn = -1; kick(); } next(); };
      im.onerror = next;
      im.src = self.path + '/f_' + String(i).padStart(3, '0') + '.' + self.ext;
    };
    for (var c = 0; c < 4; c++) next();
  };
  Seq.prototype.size = function () {
    /* кадры 780 px в ширину: на большом экране они и так растянуты, лишние пиксели холста только тормозят */
    var dpr = Math.min(devicePixelRatio || 1, wide ? 1.25 : 2), cw = this.c.clientWidth, ch = this.c.clientHeight;
    var w = Math.round(cw * dpr), h = Math.round(ch * dpr);
    this.dpr = cw ? w / cw : dpr;
    if (w !== this.w || h !== this.h) { this.c.width = this.w = w; this.c.height = this.h = h; this.drawn = -1; }
  };
  /* края кадра, попавшие внутрь экрана, растворяются в фоне — без резкой границы у тени макета */
  Seq.prototype.feather = function (x, y, dw, dh) {
    var c = this.ctx, W = this.w, H = this.h, bg = this.bg, clear = this.bgClear, g, f;
    if (!clear) {
      var hx = bg.replace('#', '');
      clear = this.bgClear = 'rgba(' + [0, 2, 4].map(function (k) { return parseInt(hx.substr(k, 2), 16); }).join(',') + ',0)';
    }
    var band = function (x0, y0, x1, y1, rx, ry, rw, rh) {
      g = c.createLinearGradient(x0, y0, x1, y1); g.addColorStop(0, bg); g.addColorStop(1, clear);
      c.fillStyle = g; c.fillRect(rx, ry, rw, rh);
    };
    f = Math.min(dw * .16, 180 * this.dpr);
    if (x > 0) band(x, 0, x + f, 0, x - 1, y, f + 1, dh);
    if (x + dw < W) band(x + dw, 0, x + dw - f, 0, x + dw - f, y, f + 1, dh);
    f = Math.min(dh * .1, 120 * this.dpr);
    if (y > 0) band(0, y, 0, y + f, x, y - 1, dw, f + 1);
    if (y + dh < H) band(0, y + dh, 0, y + dh - f, x, y + dh - f, dw, f + 1);
  };
  Seq.prototype.nearest = function (i) {
    if (this.imgs[i]) return i;
    for (var k = 1; k < this.n; k++) { if (this.imgs[i - k]) return i - k; if (this.imgs[i + k]) return i + k; }
    return -1;
  };
  /* fit: 0 — макет целиком (contain), 1 — на весь экран (cover); box — где лежит кадр, в пикселях страницы */
  Seq.prototype.draw = function (i, fit) {
    var j = this.nearest(i);
    if (j < 0 || !this.w) return;
    if (j === this.drawn && Math.abs(fit - this.fit) < .002 && this.offX === this._ox && this.offY === this._oy) return;
    var im = this.imgs[j], W = this.w, H = this.h, iw = im.naturalWidth, ih = im.naturalHeight;
    var s = lerp(Math.min(W / iw, H / ih), Math.max(W / iw, H / ih), clamp(fit, 0, 1));
    var dw = iw * s, dh = ih * s, x = (W - dw) / 2 + this.offX * W, y = (H - dh) / 2 + this.offY * H;
    this.ctx.fillStyle = this.bg; this.ctx.fillRect(0, 0, W, H);
    this.ctx.drawImage(im, x, y, dw, dh);
    this.feather(x, y, dw, dh);
    this.drawn = j; this.fit = fit; this._ox = this.offX; this._oy = this.offY;
    this.box = { x: x / this.dpr, y: y / this.dpr, s: s / this.dpr };
    if (!this.live) { this.live = true; this.el.classList.add('is-live'); }
  };
  Seq.prototype.sleep = function () { this.live = false; this.drawn = -1; this.el.classList.remove('is-live'); };

  var estate = $('.estate'), estatePin = estate && $('.pin', estate), sDay = estate && new Seq(estate, '#ffffff');
  var pins = estate ? $$('.pins li', estate) : [], pinsDirty = true;
  var night = $('.nightseq'), nightPin = night && $('.pin', night), sNight = night && new Seq(night, '#0A121C');
  var seqs = [sDay, sNight].filter(Boolean);
  watch(seqs.map(function (s) { return s.el; }), { rootMargin: '150% 0px' }, function (el, on) {
    if (!on || still()) return;
    var s = el === estate ? sDay : sNight;
    s.size(); s.start(); kick();
  });

  /* метки на особняке: точка привязана к месту на макете, подпись — в сторону от края экрана */
  function measurePins() {
    pins.forEach(function (li) { li._w = li.offsetWidth; li._h = li.offsetHeight; });
    pinsDirty = false;
  }
  function placePins(box, pe, all) {
    pins.forEach(function (li, idx) {
      li.classList.toggle('on', all || (pe > .02 + idx * .05 && pe < .3));
      if (!box || !li._w) return;
      var x = box.x + (+li.dataset.x) * box.s, y = box.y + (+li.dataset.y) * box.s, left = x > vw / 2;
      li.classList.toggle('l', left);
      li.style.left = (left ? x - li._w + 7 : x - 7).toFixed(1) + 'px';
      li.style.top = (y - li._h / 2).toFixed(1) + 'px';
    });
  }

  /* ---------------- время дня: солнце по дуге, часы «доходят» от предыдущей главы ---------------- */
  var toMin = function (t) { var m = /^(\d{1,2}):(\d{2})$/.exec(t || ''); return m ? (+m[1]) * 60 + (+m[2]) : 0; };
  var fmtT = function (m) { m = Math.round(m); return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); };
  var bez = function (t) { var u = 1 - t; return [u * u * .01 + 2 * u * t * .5 + t * t * .99, u * u * .9667 - 2 * u * t * .4667 + t * t * .9667]; };
  var heads = $$('.th').map(function (el, i, all) {
    var clock = $('.th__clock', el), prev = i > 0 ? all[i - 1] : null;
    var a1 = parseFloat(el.dataset.arc) || .5, a0 = prev ? parseFloat(prev.dataset.arc) : Math.max(.02, a1 - .16);
    var t1 = toMin(clock.dataset.time), t0 = prev ? toMin($('.th__clock', prev).dataset.time) : t1 - 30;
    return { el: el, sun: $('.th__sun', el), clock: clock, a0: a0, a1: a1, t0: t0, t1: t1, last: -1 };
  });

  /* ---------------- трансфер: автобус едет по маршруту ---------------- */
  var route = $('[data-route]'), rPath, rDone, rBus, rSvg, rLen = 0, stopW = -1, stopLen = 0;
  if (route) {
    rPath = $('.route__line', route); rDone = $('.route__done', route); rBus = $('.route__bus', route); rSvg = $('svg', route);
    rLen = rPath.getTotalLength(); rDone.setAttribute('pathLength', '1'); rDone.style.strokeDasharray = '1 1';
  }
  function updRoute(r, sr) {
    var p = still() ? 1 : clamp((vh * .92 - r.top) / (vh * .62), 0, 1);
    rDone.style.strokeDashoffset = (1 - p).toFixed(4);
    var sx = sr.width / 1000, sy = sr.height / 160;
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
    rBus.style.setProperty('--br', clamp(ang, -25, 25).toFixed(1) + 'deg');
  }

  /* ---------------- кадр прокрутки: сначала всё измеряем, потом всё двигаем ---------------- */
  var hero = $('.hero'), heroPin = hero && $('.pin', hero), lines = $$('.hero__h .l');
  var colsBox = $('.cols'), cols = $$('.cols .col'), cards = $$('.stack .lvl');
  var sm = { hero: -1, estate: -1, night: -1 }, running = false, tPrev = 0;
  var progress = function (r) { return clamp(-r.top / Math.max(1, r.height - vh), 0, 1); };
  var near = function (r) { return r.bottom > -vh * .5 && r.top < vh * 1.5; };
  function kick() { if (!running) { running = true; requestAnimationFrame(frame); } }
  function smooth(key, target, k) {  /* мягкое догоняние прокрутки; true — ещё в пути */
    var v = sm[key];
    if (v < 0 || k >= 1 || Math.abs(target - v) < .0004) { sm[key] = target; return false; }
    sm[key] = lerp(v, target, k);
    return true;
  }
  function frame(now) {
    running = false;
    var dt = tPrev ? Math.min(64, now - tPrev) : 16.7; tPrev = now;
    var calm = still(), k = calm ? 1 : 1 - Math.pow(1 - .16, dt / 16.7), moving = false;
    /* --- измерения --- */
    if (pinsDirty && pins.length) measurePins();
    var tone = 'dark', overHero = true;
    for (var i = scenes.length - 1; i >= 0; i--) {
      var rs = scenes[i].getBoundingClientRect();
      if (rs.top <= 34 && rs.bottom > 34) { tone = scenes[i].dataset.tone; overHero = scenes[i] === hero; break; }
    }
    var rHero = hero && hero.getBoundingClientRect(), rEst = estate && estate.getBoundingClientRect(), rNight = night && night.getBoundingClientRect();
    var rCols = colsBox && colsBox.getBoundingClientRect();
    var rHeads = heads.map(function (h) { return h.el.getBoundingClientRect(); });
    var rCards = calm ? [] : cards.map(function (c) { return c.getBoundingClientRect(); });
    var rRoute = route && route.getBoundingClientRect(), rSvgBox = route && rSvg.getBoundingClientRect();
    var pinBox = null;
    if (calm && estatePin && !isA11y() && near(rEst)) {  /* без движения: метки по неподвижной картинке макета */
      var pw = estatePin.clientWidth, ph = estatePin.clientHeight, ps = Math.min(pw / 780, ph / 1040);
      pinBox = { x: (pw - 780 * ps) / 2, y: (ph - 1040 * ps) / 2, s: ps };
    }

    /* --- шапка --- */
    hd.classList.toggle('is-light', tone === 'light');
    hd.classList.toggle('is-solid', !overHero || (rHero && rHero.bottom < vh * .98));  /* видео уходит вверх — шапке нужна подложка */

    if (!calm) {
      /* 1. солнце раскрывается в видео */
      if (hero) {
        moving = smooth('hero', progress(rHero), k) || moving;
        if (near(rHero)) {
          var p = sm.hero, open = ease(seg(p, 0, .78));
          var r0 = Math.min(vw, vh) * (wide ? .155 : .2), r1 = Math.hypot(vw, vh) * .62, R = lerp(r0, r1, open);
          var hs = heroPin.style;
          hs.setProperty('--r', R.toFixed(1) + 'px');
          hs.setProperty('--s', (R / .27).toFixed(1) + 'px');
          hs.setProperty('--tint', (.36 * (1 - seg(p, 0, .4))).toFixed(3));
          hs.setProperty('--ringop', (1 - seg(p, .45, .75)).toFixed(3));
          hs.setProperty('--shade', seg(p, .5, .85).toFixed(3));
          hs.setProperty('--hint', (1 - seg(p, 0, .12)).toFixed(3));
          hs.setProperty('--eye', (1 - seg(p, .12, .36)).toFixed(3));
          var spread = ease(seg(p, 0, .7));
          if (lines.length === 4) {
            lines[0].style.transform = 'translate3d(0,' + (-spread * vh * .035).toFixed(1) + 'px,0)';
            lines[1].style.transform = 'translate3d(' + (spread * vw * .04).toFixed(1) + 'px,' + (-spread * vh * .035).toFixed(1) + 'px,0)';
            lines[2].style.transform = 'translate3d(' + (-spread * vw * .06).toFixed(1) + 'px,' + (spread * vh * .02).toFixed(1) + 'px,0)';
            lines[3].style.transform = 'translate3d(0,' + (spread * vh * .02).toFixed(1) + 'px,0)';
          }
        }
      }

      /* 2. особняк утром: метки, потом подлёт камеры к воротам */
      if (sDay) {
        moving = smooth('estate', progress(rEst), k) || moving;
        if (near(rEst) && sDay.started) {
          var pe = sm.estate, fly = ease(seg(pe, .3, .92)), fi = Math.round(fly * (sDay.n - 1));
          sDay.offY = (wide ? .06 : .05) * (1 - fly);
          sDay.offX = wide ? .2 * (1 - fly) : 0;
          sDay.cur = fi; sDay.draw(fi, wide ? lerp(.25, 1, fly) : lerp(.32, 1, fly));
          estatePin.style.setProperty('--headop', (1 - seg(pe, .28, .4)).toFixed(3));
          estatePin.style.setProperty('--arr', seg(pe, .86, .97).toFixed(3));
          placePins(sDay.box, pe, false);
        }
      }

      /* 3. коллаж: колонки едут с разной скоростью */
      if (rCols && rCols.bottom > -200 && rCols.top < vh + 200) {
        var lp = (vh - rCols.top) / (vh + rCols.height);
        cols.forEach(function (c) { c.style.transform = 'translate3d(0,' + ((lp - .5) * (+c.dataset.speed) * rCols.height).toFixed(1) + 'px,0)'; });
      }

      /* 4. программы: следующая карточка накрывает предыдущую, та чуть отступает в глубину */
      for (var c = 0; c < cards.length - 1; c++) {
        var a = rCards[c], b = rCards[c + 1];
        if (a.bottom < -50 || a.top > vh) continue;
        var q = clamp((a.bottom - b.top) / Math.max(1, a.height), 0, 1);
        cards[c].style.setProperty('--q', q.toFixed(3));
      }

      /* 6. ночь: камера отъезжает, прощание сменяется записью */
      if (sNight) {
        moving = smooth('night', progress(rNight), k) || moving;
        if (near(rNight) && sNight.started) {
          var pn = sm.night, back = ease(seg(pn, .05, .8)), ni = Math.round(back * (sNight.n - 1));
          sNight.offY = (wide ? -.07 : -.06) * back;
          sNight.offX = wide ? .2 * back : 0;
          sNight.cur = ni; sNight.draw(ni, wide ? lerp(1, .45, back) : lerp(1, .15, back));
          nightPin.style.setProperty('--bye', (1 - seg(pn, .35, .55)).toFixed(3));
          nightPin.style.setProperty('--cta', seg(pn, .62, .85).toFixed(3));
          nightPin.classList.add('is-run');
          nightPin.classList.toggle('cta-on', pn > .68);
        }
      }
    } else if (pinBox) placePins(pinBox, 1, true);

    /* 5. время дня в заголовках глав */
    heads.forEach(function (h, i) {
      var r = rHeads[i];
      if (r.bottom < -100 || r.top > vh + 100) return;
      var p = calm ? 1 : ease(clamp((vh - r.top) / (vh * .6), 0, 1));
      if (Math.abs(p - h.last) < .0005) return;
      h.last = p;
      var pt = bez(lerp(h.a0, h.a1, p));
      h.sun.style.left = (pt[0] * 100).toFixed(2) + '%';
      h.sun.style.top = (pt[1] * 100).toFixed(2) + '%';
      var txt = p >= 1 ? h.clock.dataset.time : fmtT(lerp(h.t0, h.t1, p));
      if (h.clock.textContent !== txt) h.clock.textContent = txt;
    });

    /* трансфер */
    if (route && rRoute.bottom > -100 && rRoute.top < vh + 100) updRoute(rRoute, rSvgBox);

    if (moving) kick();
  }
  addEventListener('scroll', kick, { passive: true });
  addEventListener('resize', function () {
    vw = innerWidth; vh = innerHeight; wide = vw >= 900;
    seqs.forEach(function (s) { if (s.started) s.size(); s.drawn = -1; });
    pinsDirty = true; stopW = -1;
    heads.forEach(function (h) { h.last = -1; });
    kick();
  });
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(function () { pinsDirty = true; kick(); });
  addEventListener('load', kick);

  /* при переходе в «без движения» снимаем всё, что подвинул скрипт */
  function calmDown() {
    lines.forEach(function (l) { l.style.transform = ''; });
    cols.forEach(function (c) { c.style.transform = ''; });
    cards.forEach(function (c) { c.style.removeProperty('--q'); });
    if (heroPin) ['--r', '--s', '--tint', '--ringop', '--shade', '--hint', '--eye'].forEach(function (v) { heroPin.style.removeProperty(v); });
    if (estatePin) ['--headop', '--arr'].forEach(function (v) { estatePin.style.removeProperty(v); });
    if (nightPin) { ['--bye', '--cta'].forEach(function (v) { nightPin.style.removeProperty(v); }); nightPin.classList.remove('is-run', 'cta-on'); }
    seqs.forEach(function (s) { s.sleep(); });
    heads.forEach(function (h) { h.last = -1; });
    sm.hero = sm.estate = sm.night = -1;
  }
  function wake() {
    seqs.forEach(function (s) {
      var r = s.el.getBoundingClientRect();
      if (r.bottom > -vh * 1.5 && r.top < vh * 2.5) { s.size(); s.start(); }
    });
    heads.forEach(function (h) { h.last = -1; });
    kick();
  }
  if (reduceMQ.addEventListener) reduceMQ.addEventListener('change', function (e) { reduce = e.matches; if (reduce) calmDown(); else wake(); kick(); });
  if (still()) calmDown();
  kick();

  /* ---------------- окна: меню, программы, сведения, альбомы, помощник ---------------- */
  function anyOpen() { return $('dialog[open]'); }
  function openD(id) {
    var dl = d.getElementById(id);
    if (!dl || dl.tagName !== 'DIALOG') return;
    if (id !== 'lightbox') $$('dialog[open]').forEach(function (x) { if (x !== dl) closeD(x); });
    if (!dl.open) { if (dl.showModal) dl.showModal(); else dl.setAttribute('open', ''); }
    if (dl.classList.contains('pm')) { dl.scrollTop = 0; try { history.replaceState(null, '', '#' + id); } catch (e) {} }
    if (id === 'docs') { try { history.replaceState(null, '', '#docs'); } catch (e) {} }
    root.classList.add('modal-open');
    if (id === 'menu' && menuBtn) menuBtn.setAttribute('aria-expanded', 'true');
    $$('video', dl).forEach(function (v) { v.muted = true; tryPlay(v); });
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
    });
    dl.addEventListener('click', function (e) { if (e.target === dl) closeD(dl); });  /* клик по затемнению */
  });
  if (menuBtn) menuBtn.addEventListener('click', function () { openD('menu'); });
  d.addEventListener('click', function (e) {
    var t = e.target.closest('[data-open],[data-close],[data-close-go],[data-go],[data-jump],[data-album]');
    if (!t) return;
    if (t.hasAttribute('data-open')) { e.preventDefault(); openD(t.getAttribute('data-open')); return; }
    if (t.hasAttribute('data-jump')) {
      e.preventDefault();
      var tg = d.getElementById(t.getAttribute('href').slice(1));
      if (tg) tg.scrollIntoView({ behavior: still() ? 'auto' : 'smooth', block: 'start' });
      return;
    }
    if (t.hasAttribute('data-album')) { e.preventDefault(); openAlbum(t.getAttribute('data-album')); return; }
    if (t.hasAttribute('data-close')) { e.preventDefault(); closeD(t.closest('dialog')); return; }
    var target = t.getAttribute('data-go') || t.getAttribute('data-close-go');
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
    var a = ALB[k];
    if (!a) return false;
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
    var dlg = $('#album');
    if (!dlg) return;
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
    var it = lbList[lbIndex], stage = $('#lbStage'), m;
    stage.innerHTML = '';
    if (it.k === 'v') {
      m = d.createElement('video');
      m.src = it.full; m.poster = it.pf || it.th; m.controls = true; m.playsInline = true; m.loop = true; m.autoplay = true; m.muted = true;
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
  (function () {  /* свайп в просмотре на телефоне */
    var lb = $('#lightbox');
    if (!lb) return;
    var x0 = null, y0 = 0;
    lb.addEventListener('touchstart', function (e) { var t = e.touches[0]; x0 = t.clientX; y0 = t.clientY; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var t = e.changedTouches[0], dx = t.clientX - x0, dy = t.clientY - y0;
      x0 = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) lbShow(lbIndex + (dx < 0 ? 1 : -1));
    }, { passive: true });
  })();

  /* ---------------- новости и объявления: assets/data/news.json ---------------- */
  (function () {
    var list = $('#newsList'), sec = $('#news');
    if (!list) return;
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
        var go = /^#[\w-]+$/.test(n.link) ? ' data-go="' + escH(n.link.slice(1)) + '"' : '';
        return '<article class="news__card is-in' + (n.pin ? ' is-pin' : '') + '">' +
          (n.image ? '<img src="' + escH(n.image) + '" alt="" loading="lazy">' : '') +
          '<div class="news__meta">' + (n.tag ? '<span class="news__tag">' + escH(n.tag) + '</span>' : '') + (n.date ? '<time datetime="' + escH(n.date) + '">' + escH(fmtDate(n.date)) + '</time>' : '') + '</div>' +
          '<h3>' + escH(n.title) + '</h3><p>' + escH(n.text) + '</p>' +
          (n.link ? '<a class="news__more" href="' + escH(n.link) + '"' + go + (/^https?:/.test(n.link) ? ' target="_blank" rel="noopener"' : '') + '>' + escH(n.link_text || 'Подробнее') + arrow + '</a>' : '') +
          '</article>';
      }).join('');
    }
    var seed = [];
    try { seed = JSON.parse($('#newsSeed').textContent); } catch (e) {}
    if (location.protocol === 'file:' || !window.fetch) { render(seed); return; }
    fetch('assets/data/news.json', { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(render).catch(function () { render(seed); });
  })();

  /* ---------------- форма записи ---------------- */
  (function () {
    var form = $('#signupForm'), sent = $('#signupSent');
    if (!form) return;
    var WA = 'https://wa.me/79781600505';
    var field = function (name) { return form.elements.namedItem(name); };
    function showSent(ok, text) {
      form.hidden = true; sent.hidden = false;
      if (ok) { $('#sentTitle').textContent = 'Заявка отправлена'; $('#sentText').textContent = 'Перезвоним в течение рабочего дня. Хотите быстрее — напишите нам:'; }
      $('#sentWa').href = WA + '?text=' + encodeURIComponent(text);
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
      var btn = $('.form__go', form);
      btn.disabled = true;
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
      var b = e.target.closest('button[data-q]');
      if (!b) return;
      var item = data[+b.dataset.q];
      if (!item) return;
      bub(item.q, true);
      var dots = d.createElement('p');
      dots.className = 'bub bub--dots'; dots.setAttribute('aria-label', 'Помощник печатает'); dots.innerHTML = '<i></i><i></i><i></i>';
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
      if (on) calmDown(); else if (!reduce) wake();
      kick();
    });
  });
  syncA11y();

  /* ---------------- карта в подвале: грузим, когда подвал рядом ---------------- */
  var map = $('.foot__map iframe');
  if (map) watch([map], { rootMargin: '400px 0px' }, function (el, on, o) { if (on) { el.src = el.dataset.src; if (o) o.disconnect(); } });
})();
