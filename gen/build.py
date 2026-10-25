# -*- coding: utf-8 -*-
"""Собирает index.html сайта Ай Про (IPROSCHOOL), версия A.

Один день в школе: главы дня отмечены временем (08:30 уроки, 12:40 обед, 14:30 после уроков, 18:00 домой),
по нему же идёт шкала дня в шапке. Тихая плоская система: светлые главы, тёмно-синий — только безопасность
и запись, жёлтый — кнопки и метки времени. Запуск: python3 gen/build.py <папка сайта>"""
import html, json, os, re, sys, hashlib, shutil
sys.path.insert(0, os.path.dirname(__file__))
from content import *  # noqa

OUT = sys.argv[1]  # папка сайта (репозиторий ipro-a)
HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, 'icons')                 # иконки Lucide (ISC), которые использует сайт
LUCIDE_FULL = '/home/claude/npm/lucide/icons'        # полный набор, если есть: новые иконки докопируются в gen/icons
USED = set()


def e(s):
    return html.escape(str(s), quote=True)


def nb(s):
    """Текст без переносов по дефису и внутри диапазонов: «Брейк-данс», «4–7 лет», «8:30–18:00»."""
    t = e(s)
    t = re.sub(r'(?<![\w-])([\wЁёА-Яа-я]+(?:-[\wЁёА-Яа-я]+)+)', r'<span class="nw">\1</span>', t)
    t = re.sub(r'(\d[\d:,.]*\s?–\s?\d[\d:,.]*(?:\s(?:лет|года?|классы?))?)', r'<span class="nw">\1</span>', t)
    return t


def add_dims(h):
    """Проставляет width/height всем картинкам из assets — чтобы страница не прыгала при загрузке."""
    from PIL import Image

    def rep(m):
        tag = m.group(0)
        if ' width=' in tag:
            return tag
        try:
            with Image.open(os.path.join(OUT, m.group(1))) as im:
                w, hh = im.size
        except Exception:
            return tag
        return tag.replace('<img ', f'<img width="{w}" height="{hh}" ', 1)
    return re.sub(r'<img [^>]*?src="(assets/[^"?]+)[^"]*"[^>]*>', rep, h)


def I(name, cls=''):
    USED.add(name)
    return f'<svg class="i{(" " + cls) if cls else ""}" aria-hidden="true"><use href="#i-{name}"/></svg>'


def mins(t):
    h, m = t.split(':')
    return int(h) * 60 + int(m)


def day_at(t):
    """Положение времени на шкале дня 08:30 → 18:00 (0…1)."""
    a, b = mins(DAY[0]), mins(DAY[1])
    return round((mins(t) - a) / (b - a), 4)


def lnk(label, href='', attrs='', tag='a', cls=''):
    """Текстовая кнопка: подпись и стрелка."""
    h = f' href="{e(href)}"' if tag == 'a' else ' type="button"'
    return f'<{tag} class="lnk{(" " + cls) if cls else ""}"{h}{attrs}>{e(label)}{I("arrow-right")}</{tag}>'


def vbtn(cls=''):
    """Кнопка паузы у зацикленного видео (WCAG 2.2.2)."""
    return (f'<button class="vbtn{(" " + cls) if cls else ""}" type="button" data-vtoggle aria-label="Остановить видео" aria-pressed="false">'
            f'{I("pause", "vbtn__pause")}{I("play", "vbtn__play")}</button>')


def video_fig(name, label, cls='', cap=True):
    """Видео-карточка: постер сразу, видео грузится, только когда видно; подпись и кнопка паузы."""
    v = (f'<video src="assets/video/{name}.mp4" data-poster="assets/img/posters/{name}.jpg" data-poster-sm="assets/img/posters/{name}-sm.jpg" muted loop playsinline preload="none" '
         f'aria-label="{e(label)}"></video>')
    c = f'<figcaption class="media__cap">{I("play", "media__ico")}{e(label)}</figcaption>' if cap else ''
    return f'<figure class="media media--video rv{(" " + cls) if cls else ""}">{v}{vbtn()}{c}</figure>'


SIZES = {  # какой ширины картинка на экране — браузер берёт уменьшенную копию *-sm.jpg, где хватает
    'half': '(min-width: 600px) 50vw, 100vw',
    'pcard': '(min-width: 1024px) 280px, (min-width: 600px) 340px, 50vw',
    'person': '(min-width: 1024px) 280px, (min-width: 600px) 25vw, 50vw',
    'dcard': '(min-width: 1024px) 380px, (min-width: 600px) 33vw, 76vw',
    'ep': '(min-width: 1024px) 380px, (min-width: 600px) 340px, 78vw',
    'alb': '(min-width: 1024px) 220px, (min-width: 600px) 32vw, 58vw',
    'pm': '(min-width: 1024px) 420px, 100vw',
}
_W = {}


def img(name, alt='', size='half', cls='', lazy=True):
    """<img> с уменьшенной копией для телефонов (srcset) — см. media.py, *-sm.jpg."""
    from PIL import Image
    full = f'assets/img/{name}.jpg'
    if name not in _W:
        with Image.open(os.path.join(OUT, full)) as im:
            _W[name] = im.size[0]
    sm = f'assets/img/{name}-sm.jpg'
    srcset = f' srcset="{sm} 640w, {full} {_W[name]}w" sizes="{SIZES[size]}"' if os.path.exists(os.path.join(OUT, sm)) else ''
    c = f' class="{cls}"' if cls else ''
    return f'<img{c} src="{full}"{srcset} alt="{e(alt)}"{" loading=" + chr(34) + "lazy" + chr(34) if lazy else ""}>'


def photo_fig(name, alt, cls=''):
    return f'<figure class="media rv{(" " + cls) if cls else ""}">{img(name, alt)}</figure>'


def meta_line(items, cls=''):
    """Строка фактов через точку — вместо списка карточек с иконками."""
    lis = ''.join(f'<li>{nb(x)}</li>' for x in items)
    return f'<ul class="metas rv{(" " + cls) if cls else ""}">{lis}</ul>'


def clock(key):
    """Подводка главы дня: крупное время и тонкая шкала дня."""
    t, phrase = CLOCKS[key]
    return (f'<div class="clock rv"><time class="clock__t" datetime="{t}">{t}</time><span class="clock__p">{e(phrase)}</span>'
            f'<span class="clock__day" style="--at:{day_at(t)}" aria-hidden="true"><i></i></span></div>')


def head(key, title, lead='', h='h2', cls=''):
    top = clock(key) if key in CLOCKS else (f'<p class="eyebrow rv">{e(EYEBROWS[key])}</p>' if key in EYEBROWS else '')
    ld = f'<p class="lead rv">{e(lead)}</p>' if lead else ''
    return f'<div class="sec__head{(" " + cls) if cls else ""}">{top}<h2 class="{h} rv">{e(title)}</h2>{ld}</div>'


SHORT = {'news': 'Новости', 'programs': 'Программы', 'extra': 'Кружки', 'gallery': 'Фото и видео', 'signup': 'Запись',
         'reviews': 'Отзывы', 'admission': 'Поступление', 'summer': 'Летний клуб'}


def section(id_, bg, title, body, cls=''):
    t = CLOCKS.get(id_, ('', ''))[0]
    return (f'<section class="sec bg-{bg}{(" " + cls) if cls else ""}" id="{id_}" data-title="{e(title)}" '
            f'data-short="{e(SHORT.get(id_, title))}" data-time="{t}">\n{body}\n</section>\n')


# ---------------------------------------------------------------- шапка, шкала дня, меню, нижняя панель
def header():
    nav = ''.join(f'<a href="#{k}" data-go="{k}">{e(t)}</a>' for k, t in NAV)
    pts = ''
    for k in ('programs', 'food', 'extra', 'transfer'):
        t, _ = CLOCKS[k]
        word = {'programs': 'Уроки', 'food': 'Обед', 'extra': 'После уроков', 'transfer': 'Домой'}[k]
        pts += f'<a class="tl__pt" href="#{k}" data-go="{k}" style="--at:{day_at(t)}"><b>{t}</b>{e(word)}</a>'
    dots = ''.join(f'<span class="rail__pt" data-t="{CLOCKS[k][0]}" style="--at:{day_at(CLOCKS[k][0])}"></span>' for k in ('programs', 'food', 'extra', 'transfer'))
    return f'''<header class="hdr" id="hdr">
  <div class="hdr__bar">
    <a class="hdr__logo" href="#top" data-go="top" aria-label="Ай Про, частная школа полного дня — в начало">
      <img class="hdr__wm hdr__wm--light" src="assets/img/wordmark-aipro.webp" alt="">
      <img class="hdr__wm hdr__wm--dark" src="assets/img/wordmark-aipro-navy.webp" alt="">
      <span class="hdr__tag">школа<br>полного дня</span>
    </a>
    <p class="hdr__ch" id="chap"><b id="chTime"></b><span id="chName"></span></p>
    <nav class="hdr__nav" aria-label="Главные разделы">{nav}</nav>
    <button class="hdr__ask" type="button" data-open="helper" aria-label="Вопросы о школе">{I('message-circle-question-mark')}<span>Вопросы</span></button>
    <button class="hdr__menu" id="menuBtn" type="button" aria-haspopup="dialog" aria-controls="menu" aria-expanded="false">{I('menu')}<span>Меню</span></button>
    <a class="btn btn--primary btn--sm hdr__cta" href="#signup" data-go="signup">Записаться</a>
  </div>
  <nav class="tl" aria-label="День в школе"><span class="tl__track" aria-hidden="true"><i class="tl__fill"></i></span>{pts}</nav>
</header>
<div class="rail" aria-hidden="true"><i class="rail__fill"></i>{dots}</div>
'''


def menu_dialog():
    items = ''
    for k, label in MENU:
        t = CLOCKS.get(k, ('', ''))[0]
        tm = f'<time>{t}</time>' if t else '<i aria-hidden="true"></i>'
        items += f'<li><a href="#{k}" data-go="{k}">{tm}<span>{e(label)}</span></a></li>'
    c = CONTACTS
    return f'''<dialog class="drawer" id="menu" aria-label="Меню">
  <div class="drawer__in">
    <div class="drawer__top">
      <a class="drawer__logo" href="#top" data-go="top"><img src="assets/img/wordmark-aipro-navy.webp" alt=""><span>Ай Про<small>частная школа полного дня</small></span></a>
      <button class="xbtn" type="button" data-close aria-label="Закрыть меню">{I('x')}</button>
    </div>
    <nav aria-label="Разделы сайта"><ol class="menu">{items}</ol></nav>
    <a class="btn btn--primary drawer__cta" href="#signup" data-go="signup">{e(INTRO['cta'])}{I('arrow-right')}</a>
    <div class="drawer__contacts">
      <a class="drawer__phone" href="{c['phone_href']}">{e(c['phone'])}<small>{e(c['hours'])}</small></a>
      {socials()}
      <a class="lnk lnk--plain" href="{c['map']}" target="_blank" rel="noopener">{e(c['address'])}{I('arrow-up-right')}</a>
      <a class="lnk lnk--plain" href="#docs" data-open="docs">Сведения об образовательной организации{I('arrow-right')}</a>
      <button class="a11y-toggle" type="button" aria-pressed="false">{I('eye')}<span>Версия для слабовидящих</span></button>
    </div>
  </div>
</dialog>
'''


def socials(cls=''):
    """Мессенджеры подписаны словами — общие значки «пузырь» и «самолётик» не узнаются."""
    c = CONTACTS
    return (f'<div class="socials{(" " + cls) if cls else ""}">'
            f'<a href="{c["wa"]}" target="_blank" rel="noopener">WhatsApp</a>'
            f'<a href="{c["tg"]}" target="_blank" rel="noopener">Telegram</a>'
            f'<a href="{c["vk"]}" target="_blank" rel="noopener">ВКонтакте</a>'
            f'<a href="{c["max"]}" target="_blank" rel="noopener">MAX</a></div>')


def bottom_bar():
    c = CONTACTS
    return f'''<nav class="bbar" aria-label="Запись и звонок">
  <a class="btn btn--primary bbar__go" href="#signup" data-go="signup">Записаться на 3 дня</a>
  <a class="btn btn--ghost bbar__call" href="{c['phone_href']}">{I('phone')}Позвонить</a>
</nav>
'''


# ---------------------------------------------------------------- главы
def intro():
    i = INTRO
    body = f'''  <div class="intro__media">
    <picture class="intro__poster"><source media="(orientation: portrait) and (max-width: 1023px)" srcset="assets/img/posters/hero_school.jpg"><img src="assets/video/tour_poster.jpg" alt="" fetchpriority="high"></picture>
    <video class="intro__v" data-src-land="assets/video/tour.mp4" data-src-port="assets/video/hero_school.mp4" muted loop playsinline preload="none" aria-label="Видео о школе: классы, занятия, территория"></video>
  </div>
  <div class="wrap intro__in">
    <img class="intro__wm" src="assets/img/wordmark-aipro.webp" alt="Ай Про">
    <p class="intro__kicker">{e(i['eyebrow'])}</p>
    <h1 class="h1 intro__h">{e(i['title'])} <em>{e(i['accent'])}</em></h1>
    <a class="btn btn--primary intro__cta" href="#signup" data-go="signup">{e(i['cta'])}</a>
  </div>
  {vbtn('vbtn--hero')}
  <a class="cue" href="#news">Листайте{I('arrow-down')}</a>'''
    return f'<section class="intro" id="top" data-title="Начало" data-short="Начало" data-time="">\n{body}\n</section>\n'


def news_card(n):
    date = f'<time datetime="{e(n["date"])}">{e(n["date"])}</time>' if n.get('date') else ''
    tag = f'<span class="ncard__tag">{e(n.get("tag", ""))}</span>' if n.get('tag') else ''
    meta = f'<p class="ncard__meta">{tag}{date}</p>' if (tag or date) else ''
    link = lnk(n.get('link_text') or 'Подробнее', n['link']) if n.get('link') else ''
    img = f'<img src="{e(n["image"])}" alt="" loading="lazy">' if n.get('image') else ''
    return f'<article class="ncard rv{" is-pin" if n.get("pin") else ""}">{img}{meta}<h3 class="ncard__t">{e(n["title"])}</h3><p class="ncard__x">{e(n["text"])}</p>{link}</article>'


def news():
    cards = ''.join(news_card(n) for n in NEWS_SEED)
    data = json.dumps(NEWS_SEED, ensure_ascii=False)
    body = f'''  <div class="wrap">
    <div class="sec__head"><h2 class="h3">Новости и объявления</h2></div>
    <div class="news hs" id="newsList">{cards}</div>
  </div>
  <script type="application/json" id="newsSeed">{data}</script>'''
    return section('news', 'white', 'Новости и объявления', body, 'sec--news')


def concept():
    c = CONCEPT
    acc = [f for f in c['facts'] if f[2]][0]
    rest = [f for f in c['facts'] if not f[2]]
    facts = ''.join(f'<li><b>{nb(n)}</b><span>{e(l)}</span></li>' for n, l, _ in rest)
    q, who, src = REVIEWS['items'][c['quote']]
    vname, vlabel = c['video']
    body = f'''  <div class="wrap">
    {head('concept', c['title'], c['lead'])}
    <div class="bento">
      {video_fig(vname, vlabel, 'bento__v')}
      <div class="bento__acc rv"><b>{nb(acc[0])}</b><span>{e(acc[1])}</span></div>
      <ul class="bento__facts rv">{facts}</ul>
      <figure class="bento__q rv"><blockquote>{e(q)}</blockquote><figcaption><b>{e(who)}</b> · {e(src)}</figcaption></figure>
    </div>
  </div>'''
    return section('concept', 'alt', 'Концепция', body)


def about():
    a = ABOUT
    vids = ''.join(video_fig(v, label) for v, label in a['videos'])
    n = a['seq_last'] + 1
    body = f'''  <div class="wrap about">
    {head('about', a['title'], a['lead'])}
    <div class="model rv" data-seq="estate" data-frames="{n}" data-path="assets/seq/estate" data-ext="webp">
      <canvas aria-hidden="true"></canvas>
      <img class="model__poster" src="assets/seq/estate/f_000.webp" alt="3D-макет особняка школы: парк, двор, бассейн">
    </div>
    <div class="about__vids hs">{vids}</div>
    <figure class="quote rv"><blockquote>{e(a['quote'])}</blockquote><figcaption>{e(a['sign'])}</figcaption></figure>
  </div>'''
    return section('about', 'white', 'О школе', body)


def programs():
    P = PROGRAMS_INTRO
    cards = ''
    for p in PROGRAMS:
        cards += f'''<a class="pcard rv" href="#m-{p['key']}" data-open="m-{p['key']}" aria-label="{e(p['title'])}, {e(p['meta'].replace(' · ', ', '))} — открыть программу и расписание">
      {img(p['img'], '', 'pcard')}
      <span class="pcard__lbl">{''.join('<span>' + nb(x) + '</span>' for x in p['meta'].split(' · '))}</span>
      <span class="pcard__t">{e(p['title'])}{I('arrow-right')}</span>
    </a>'''
    body = f'''  <div class="wrap">
    {head('programs', P['title'], P['lead'])}
    <div class="pgrid">{cards}</div>
  </div>'''
    return section('programs', 'alt', 'Программы и расписание', body)


def food():
    f = FOOD
    body = f'''  <div class="wrap split">
    <div class="sec__head">{clock('food')}<h2 class="h2 rv">{e(f['title'])}</h2>{meta_line(f['meta'])}</div>
    {photo_fig(f['photo'][0], f['photo'][1], 'media--tall')}
  </div>'''
    return section('food', 'white', 'Питание', body)


def teachers():
    t = TEACHERS
    cards = ''.join(f'<figure class="person rv">{img(ph, name, "person")}<figcaption><b>{e(name)}</b><span>{e(role)}</span></figcaption></figure>' for ph, name, role in t['people'])
    body = f'''  <div class="wrap">
    {head('teachers', t['title'])}
    <div class="people">{cards}</div>
  </div>'''
    return section('teachers', 'alt', 'Педагоги', body)


def safety():
    s = SAFETY
    facts = ''.join(f'<li class="rv"><b class="{"sf__n" if any(ch.isdigit() for ch in n) else "sf__w"}">{nb(n)}</b><span>{e(t)}</span></li>' for n, t in s['facts'])
    body = f'''  <div class="wrap split split--rev">
    <div class="sec__head">
      <p class="eyebrow rv">{e(EYEBROWS['safety'])}</p><h2 class="h2 rv">{e(s['title'])}</h2>
      <ul class="sf">{facts}</ul>
      {meta_line(s['meta'])}
    </div>
    {video_fig(s['video'][0], s['video'][1], 'media--tall', cap=False)}
  </div>'''
    return section('safety', 'navy', 'Безопасность', body)


def mono(name):
    parts = [p for p in name.split() if p]
    return ''.join(p[0] for p in parts[:2]).upper()


def extra():
    x = EXTRA
    dirs = ''.join(f'''<figure class="dcard rv"><div class="mcard">{img(d['cover'], d['alt'], 'dcard')}<span class="mcard__cap"><b class="mcard__t">{e(d['name'])}</b></span></div>
      <figcaption class="dcard__list">{' · '.join(nb(i) for i in d['list'])}</figcaption></figure>''' for d in x['directions'])
    guests = ''.join(f'<article class="guest rv"><span class="guest__mono" aria-hidden="true">{e(mono(n))}</span><div><h4>{e(n)}</h4><p class="guest__what">{nb(w)}</p><p>{e(c)}</p></div></article>' for n, w, c in x['guests'])
    body = f'''  <div class="wrap">
    {head('extra', x['title'], x['lead'])}
    <div class="dirs hs">{dirs}</div>
    <div class="meet">
      <div class="meet__head"><h3 class="h3 rv">{e(x['meet_title'])}</h3><p class="lead lead--s rv">{e(x['meet_lead'])}</p></div>
      <div class="guests hs">{guests}</div>
    </div>
  </div>'''
    return section('extra', 'white', 'Авторская программа', body)


def transfer():
    t = TRANSFER
    (i1, n1), (i2, n2) = t['route']
    body = f'''  <div class="wrap split">
    <div class="sec__head">{clock('transfer')}<h2 class="h2 rv">{e(t['title'])}</h2><p class="lead rv">{e(t['lead'])}</p>{meta_line(t['meta'])}</div>
    {photo_fig(t['photo'][0], t['photo'][1])}
    <div class="route rv" data-route aria-hidden="true">
      <svg viewBox="0 0 1000 160" preserveAspectRatio="none"><path class="route__line" d="M40 120 C 220 120, 260 40, 420 50 S 640 140, 780 90 S 920 40, 960 40"/><path class="route__done" d="M40 120 C 220 120, 260 40, 420 50 S 640 140, 780 90 S 920 40, 960 40"/></svg>
      <span class="route__pt route__pt--a">{I(i1)}<b>{e(n1)}</b></span>
      <span class="route__pt route__pt--b">{I(i2)}<b>{e(n2)}</b></span>
      <span class="route__bus">{I('bus')}</span>
    </div>
  </div>'''
    return section('transfer', 'alt', 'Трансфер', body)


def summer():
    s = SUMMER
    eps = ''.join(f'''<article class="ep rv">{img(ph, alt, 'ep')}
      <div><p class="ep__k">{e(mon)}</p><h3>{nb(title)}</h3><p>{nb(text)}</p></div></article>''' for mon, title, text, ph, alt in s['episodes'])
    body = f'''  <div class="wrap">
    <div class="split">
      <div class="sec__head"><h2 class="h2 rv">{e(s['title'])}</h2><p class="lead rv">{e(s['lead'])}</p>{meta_line(s['meta'])}</div>
      {video_fig(s['video'][0], s['video'][1])}
    </div>
    <div class="eps hs">{eps}</div>
  </div>'''
    return section('summer', 'white', 'Летний клуб', body)


def stars(v):
    s = ''.join(I('star') for _ in range(5))
    return f'<span class="stars" style="--v:{v / 5:.3f}" aria-hidden="true"><span class="stars__bg">{s}</span><span class="stars__fg">{s}</span></span>'


def reviews():
    r = REVIEWS
    hi = r['hero']
    q, n, src = r['items'][hi]
    # цитата из сетки фактов концепции на телефоне скрыта — там она идёт в ленте отзывов (rcard--m)
    cq = CONCEPT['quote']
    cards = ''.join(f'<figure class="rcard{" rcard--m" if i == cq else ""}"><blockquote>{e(q2)}</blockquote><figcaption><b>{e(n2)}</b><span>{e(s2)}</span></figcaption></figure>' for i, (q2, n2, s2) in enumerate(r['items']) if i != hi)
    body = f'''  <div class="wrap">
    {head('reviews', r['title'])}
    <figure class="bigq rv"><blockquote>{e(q)}</blockquote><figcaption><b>{e(n)}</b> · {e(src)}</figcaption></figure>
    <a class="rating rv" href="{CONTACTS['map_reviews']}" target="_blank" rel="noopener" aria-label="Рейтинг {r['rating']} из 5, {r['count']} на Яндекс Картах — открыть все отзывы">
      <b>{r['rating']}</b>{stars(r['rating_value'])}<span>{e(r['count'])} на Яндекс Картах</span><span class="lnk">Все отзывы{I('arrow-up-right')}</span>
    </a>
  </div>
  <div class="carousel rv">
    <div class="carousel__track hs" tabindex="0" aria-label="Отзывы родителей">{cards}</div>
    <div class="wrap carousel__nav"><button type="button" class="xbtn" data-dir="-1" aria-label="Предыдущий отзыв">{I('arrow-left')}</button><button type="button" class="xbtn" data-dir="1" aria-label="Следующий отзыв">{I('arrow-right')}</button></div>
  </div>'''
    return section('reviews', 'alt', 'Отзывы', body)


def admission():
    a = ADMISSION
    steps = ''.join(f'<li class="rv"><span class="steps__n">{i + 1}</span><div><b>{e(t)}</b><span>{e(d)}</span></div></li>' for i, (t, d) in enumerate(a['steps']))
    inc = ''.join(f'<li>{I("check")}{e(t)}</li>' for t in a['included'])
    lbl, h, sub = a['cost']
    body = f'''  <div class="wrap adm">
    {head('admission', a['title'])}
    <ol class="steps">{steps}</ol>
    <article class="price rv">
      <p class="eyebrow">{e(lbl)}</p>
      <h3 class="h3">{e(h)}</h3>
      <p class="price__sub">{e(sub)}</p>
      <p class="price__lbl">Уже входит в стоимость</p>
      <ul class="price__inc">{inc}</ul>
      <p class="price__sale"><b>{e(a['sale'][0])}</b> — {e(a['sale'][1])}</p>
      <a class="btn btn--primary price__go" href="#signup" data-go="signup">Прийти на пробные дни{I('arrow-right')}</a>
    </article>
    {lnk('Лицензия и документы', '#docs', ' data-open="docs"', cls='adm__docs rv')}
  </div>'''
    return section('admission', 'white', 'Поступление', body)


def count_media(k):
    items = [kind for cat, kind, *_ in GALLERY if cat == k]
    v, i = items.count('video'), items.count('img')
    parts = []
    if i:
        parts.append(f'{i} фото')
    if v:
        parts.append(f'{v} видео')
    return ' · '.join(parts)


def gallery():
    cards = ''.join(f'''<button type="button" class="mcard alb rv" data-album="{k}" aria-label="{e(label)}: {count_media(k)} — открыть альбом">
      {img(GALLERY_COVERS[k], '', 'alb')}
      <span class="mcard__cap"><b class="mcard__t">{e(label)}</b><span class="mcard__m">{count_media(k)}</span></span>
    </button>''' for k, label in GALLERY_TABS)
    body = f'''  <div class="wrap">
    {head('gallery', 'Фото и видео школы')}
    <div class="albs hs">{cards}</div>
  </div>'''
    return section('gallery', 'alt', 'Фото и видео', body)


def signup():
    s = SIGNUP
    c = CONTACTS
    body = f'''  <div class="wrap split split--signup">
    {head('signup', s['title'], s['lead'])}
    <div class="formcard rv">
      <form class="form" id="signupForm" novalidate data-endpoint="">
        <label class="field" for="f-name"><span>Имя <i>*</i></span><input id="f-name" name="name" autocomplete="name" placeholder="Как вас зовут" required><small class="field__err">Напишите имя, чтобы мы знали, к кому обращаться.</small></label>
        <label class="field" for="f-age"><span>Возраст ребёнка</span><input id="f-age" name="age" inputmode="numeric" placeholder="Например, 8"></label>
        <label class="field" for="f-phone"><span>Телефон <i>*</i></span><input id="f-phone" name="phone" type="tel" autocomplete="tel" placeholder="+7 978 000-00-00" required><small class="field__err">Введите номер телефона, чтобы мы могли перезвонить.</small></label>
        <button class="btn btn--primary form__go" type="submit">Записаться{I('arrow-right')}</button>
        <p class="form__note">{e(s['note'])}</p>
      </form>
      <div class="sent" id="signupSent" hidden tabindex="-1">
        <span class="sent__ok">{I('check')}</span>
        <h3 class="h3" id="sentTitle">Остался один шаг</h3>
        <p id="sentText">Отправьте заявку в удобный мессенджер — текст уже готов. Или позвоните, мы подберём даты пробных дней.</p>
        <div class="sent__btns">
          <a class="btn btn--primary" id="sentWa" href="{c['wa']}" target="_blank" rel="noopener">Отправить в WhatsApp</a>
          <a class="btn btn--ghost" href="{c['tg']}" target="_blank" rel="noopener">Telegram</a>
          <a class="btn btn--ghost" href="{c['max']}" target="_blank" rel="noopener">MAX</a>
          <a class="btn btn--ghost" href="{c['phone_href']}">{I('phone')}{e(c['phone'])}</a>
        </div>
        <button class="lnk lnk--plain" type="button" id="sentBack">Изменить данные</button>
      </div>
    </div>
  </div>'''
    return section('signup', 'navy', 'Запись на пробные дни', body)


def footer():
    c = CONTACTS
    return f'''<footer class="foot" id="contacts">
  <div class="foot__night">
    <img src="assets/img/night.jpg" alt="Особняк школы ночью: в окнах горит свет" loading="lazy">
    <p class="foot__bye h2">{e(FAREWELL)}</p>
  </div>
  <div class="wrap foot__grid">
    <div class="foot__brand"><img src="assets/img/wordmark-aipro.webp" alt="Ай Про" loading="lazy"><p>Частная школа полного дня в Ялте для детей 4–18 лет</p></div>
    <div class="foot__contacts">
      <a class="foot__phone" href="{c['phone_href']}">{e(c['phone'])}</a>
      <span>{e(c['hours'])}</span>
      <a href="mailto:{c['email']}">{e(c['email'])}</a>
      <a href="{c['map']}" target="_blank" rel="noopener">{e(c['address'])}</a>
      {socials('socials--dark')}
    </div>
    <div class="foot__map">
      <iframe title="Ай Про на Яндекс Картах" src="about:blank" data-src="{c['map_embed']}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
      <a class="btn btn--primary btn--sm foot__maplink" href="{c['map']}" target="_blank" rel="noopener">{I('map-pin')}Открыть на Яндекс Картах</a>
    </div>
    <div class="foot__bottom">
      <span>© 2026 Ай Про (IPROSCHOOL)</span>
      <a href="#docs" data-open="docs">Сведения об образовательной организации</a>
      <button type="button" class="a11y-toggle a11y-toggle--link" aria-pressed="false">{I('eye')}Версия для слабовидящих</button>
      <a href="#top" data-go="top">Наверх{I('arrow-up')}</a>
    </div>
  </div>
</footer>
'''


# ---------------------------------------------------------------- окна
def program_dialog(p, prev, nxt):
    k = p['key']
    L = LABELS
    base = ''.join(f'<li class="{"hl" if len(b) > 2 and b[2] else ""}">{I("sparkles" if len(b) > 2 and b[2] else "check")}<span><b>{nb(b[0])}</b>{("<small>" + nb(b[1]) + "</small>") if len(b) > 1 and b[1] else ""}</span></li>' for b in p['base'])
    dl = lambda xs, cls='': f'<ul class="dl2{(" " + cls) if cls else ""}">' + ''.join(f'<li>{nb(x)}</li>' for x in xs) + '</ul>'
    req = (f'<p class="sub"><span class="tag tag--fill">{L["required"]}</span></p>' + dl(p['author_required'], 'dl2--fill')) if p['author_required'] else ''
    choice = f'<p class="sub"><span class="tag">{L["choice"]}</span></p>' + dl(p['author_choice'])
    ind = dl(p['individual'])
    day = ''.join(f'<li><time>{e(t)}</time><span>{nb(w)}</span></li>' for t, w in p['day'])
    toc = [(f'{k}-base', L['base']), (f'{k}-author', L['author']), (f'{k}-ind', L['individual']), (f'{k}-day', p['day_title'])]
    toc_h = ''.join(f'<a href="#{a}" data-jump><b>0{i + 1}</b>{e(t)}</a>' for i, (a, t) in enumerate(toc))
    return f'''<dialog class="pm" id="m-{k}" data-k="{k}" aria-labelledby="t-{k}">
  <div class="pm__bar"><span><b>{e(p['title'])}</b> · {nb(p['meta'])}</span><button class="xbtn" type="button" data-close aria-label="Закрыть">{I('x')}</button></div>
  <section class="pm__hero">
    <div class="pm__hero-in">
      <div><p class="eyebrow">{nb(p['meta'])}</p><h2 class="pm__t h1" id="t-{k}">{e(p['title'])}</h2></div>
      <span class="pm__ph">{img(p['img'], p['alt'], 'pm')}</span>
    </div>
  </section>
  <nav class="pm__toc" aria-label="Оглавление программы">{toc_h}</nav>
  <div class="pm__body">
    <section class="dsec" id="{k}-base"><h3 class="h3">{L['base']}</h3><ul class="bl">{base}</ul></section>
    <section class="dsec" id="{k}-author"><div class="dsec__h"><h3 class="h3">{L['author']}</h3><span class="note">{L['author_note']}</span></div>{req}{choice}</section>
    <section class="dsec" id="{k}-ind"><div class="dsec__h"><h3 class="h3">{L['individual']}</h3><span class="note">{L['individual_note']}</span></div>{ind}</section>
    <section class="dsec" id="{k}-day"><h3 class="h3">{e(p['day_title'])}</h3><ol class="times">{day}</ol></section>
    <nav class="pn" aria-label="Другие программы">
      <a href="#m-{prev['key']}" data-open="m-{prev['key']}"><small>← {nb(prev['meta'])}</small><b>{e(prev['title'])}</b></a>
      <a href="#m-{nxt['key']}" data-open="m-{nxt['key']}"><small>{nb(nxt['meta'])} →</small><b>{e(nxt['title'])}</b></a>
    </nav>
    <div class="pm__cta"><span>Приходите на пробные дни</span><a class="btn btn--primary" href="#signup" data-close-go="signup">Записаться{I('arrow-right')}</a></div>
  </div>
</dialog>
'''


def docs_dialog():
    c = CONTACTS
    docs = ''.join(f'<li>{I("file-badge")}<span><b>{e(t)}</b>{(" " + e(s)) if s else ""}</span></li>' for t, s in ADMISSION['docs'])
    return f'''<dialog class="sheet" id="docs" aria-labelledby="docsT">
  <div class="sheet__bar"><h2 id="docsT">Сведения об образовательной организации</h2><button class="xbtn" type="button" data-close aria-label="Закрыть">{I('x')}</button></div>
  <div class="sheet__body">
    <p class="eyebrow">Лицензия и документы</p>
    <ul class="docs">{docs}</ul>
    <p class="eyebrow">Контакты организации</p>
    <dl class="kv">
      <dt>Адрес</dt><dd>{e(c['address'])}</dd>
      <dt>Телефон</dt><dd><a href="{c['phone_href']}">{e(c['phone'])}</a></dd>
      <dt>Электронная почта</dt><dd><a href="mailto:{c['email']}">{e(c['email'])}</a></dd>
      <dt>Режим работы</dt><dd>{e(c['hours'])}</dd>
    </dl>
    <p class="eyebrow">Реквизиты</p>
    <p class="ph">Полное наименование, ИНН, ОГРН, сканы лицензии и уставных документов разместим здесь по данным школы.</p>
  </div>
</dialog>
'''


def media_item(kind, src, alt):
    if kind == 'video':
        th = f'assets/img/posters/{src}-sm.jpg'
        return {'k': 'v', 'full': f'assets/video/{src}.mp4', 'th': th if os.path.exists(os.path.join(OUT, th)) else f'assets/img/posters/{src}.jpg', 'alt': alt}
    th = f'assets/img/{src}-sm.jpg'
    return {'k': 'i', 'full': f'assets/img/{src}.jpg', 'th': th if os.path.exists(os.path.join(OUT, th)) else f'assets/img/{src}.jpg', 'alt': alt}


def album_dialog():
    data = {}
    for k, label in GALLERY_TABS:
        data[k] = {'t': label, 'items': [media_item(kind, src, alt) for cat, kind, src, alt in GALLERY if cat == k]}
    js = json.dumps(data, ensure_ascii=False)
    return f'''<dialog class="album" id="album" aria-labelledby="albumT">
  <div class="album__bar"><h2 id="albumT">Фото и видео</h2><button class="xbtn" type="button" data-close aria-label="Закрыть">{I('x')}</button></div>
  <nav class="album__tabs hs" id="albumTabs" aria-label="Разделы"></nav>
  <div class="album__grid" id="albumGrid"></div>
  <template id="albumPlay">{I('play')}</template>
  <script type="application/json" id="albumData">{js}</script>
</dialog>
'''


def lightbox():
    return f'''<dialog class="lightbox" id="lightbox" aria-label="Просмотр фото и видео">
  <button class="xbtn lightbox__x" type="button" data-close aria-label="Закрыть">{I('x')}</button>
  <div class="lightbox__stage" id="lbStage"></div>
  <p class="lightbox__cap" id="lbCap"></p>
  <button class="xbtn lightbox__nav lightbox__nav--prev" type="button" data-lb="-1" aria-label="Предыдущее">{I('chevron-left')}</button>
  <button class="xbtn lightbox__nav lightbox__nav--next" type="button" data-lb="1" aria-label="Следующее">{I('chevron-right')}</button>
</dialog>
'''


def helper_dialog():
    c = CONTACTS
    qs = ''.join(f'<button type="button" data-q="{i}">{e(q)}</button>' for i, (q, _) in enumerate(HELPER))
    data = json.dumps([{'q': q, 'a': a} for q, a in HELPER], ensure_ascii=False)
    return f'''<dialog class="helper" id="helper" aria-labelledby="helperT">
  <div class="helper__bar"><span class="helper__ava"><img src="assets/img/wordmark-aipro.webp" alt=""></span><span><b id="helperT">Помощник Ай Про</b><small>Отвечаю на вопросы о школе</small></span><button class="xbtn" type="button" data-close aria-label="Закрыть помощника">{I('x')}</button></div>
  <div class="helper__log" id="helperLog" aria-live="polite"><p class="bub">Здравствуйте! Подскажу по школе Ай Про — выберите вопрос ниже.</p></div>
  <div class="helper__qs" id="helperQs">{qs}</div>
  <p class="helper__foot">Не нашли ответ? Позвоните <a href="{c['phone_href']}">{e(c['phone'])}</a>, напишите в <a href="{c['wa']}" target="_blank" rel="noopener">WhatsApp</a> или <a href="{c['tg']}" target="_blank" rel="noopener">Telegram</a>.</p>
  <script type="application/json" id="helperData">{data}</script>
</dialog>
'''


def sprite():
    out = []
    for n in sorted(USED):
        p = os.path.join(ICONS, n + '.svg')
        if not os.path.exists(p):
            os.makedirs(ICONS, exist_ok=True)
            shutil.copy(os.path.join(LUCIDE_FULL, n + '.svg'), p)
        s = open(p, encoding='utf8').read()
        inner = re.sub(r'\s+', ' ', re.search(r'>\s*(.*)</svg>', s, re.S).group(1)).strip()
        out.append(f'<symbol id="i-{n}" viewBox="0 0 24 24">{inner}</symbol>')
    return '<svg class="sprite" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">' + ''.join(out) + '</svg>'


def asset_v(path):
    try:
        return hashlib.md5(open(os.path.join(OUT, path), 'rb').read()).hexdigest()[:8]
    except FileNotFoundError:
        return 'dev'


def page():
    main = ('<div class="drw">\n' + intro() + '<div class="drw__sheet">\n' + news() + concept() + '</div></div>\n'
            + about() + programs() + food() + teachers() + safety() + extra() + transfer() + summer()
            + reviews() + admission() + gallery() + signup())
    n = len(PROGRAMS)
    dialogs = ''.join(program_dialog(p, PROGRAMS[(i - 1) % n], PROGRAMS[(i + 1) % n]) for i, p in enumerate(PROGRAMS))
    dialogs += menu_dialog() + docs_dialog() + album_dialog() + lightbox() + helper_dialog()
    hdr = header()
    foot = footer()
    bar = bottom_bar()
    desc = 'Ай Про (IPROSCHOOL) — частная школа полного дня в Ялте для детей 4–18 лет: детский сад и школа в историческом особняке, малые группы до 14 человек, языки с носителями, кружки, питание и трансфер. Три пробных дня бесплатно.'
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Ай Про · частная школа полного дня в Ялте</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0A2C55">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="Ай Про (IPROSCHOOL)">
<meta property="og:title" content="Ай Про · частная школа полного дня в Ялте">
<meta property="og:description" content="Детский сад и школа в историческом особняке: малые группы, языки с носителями, кружки, питание и трансфер. Три пробных дня бесплатно.">
<meta property="og:image" content="assets/og.jpg">
<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="preload" as="image" href="assets/img/posters/hero_school.jpg" media="(orientation: portrait) and (max-width: 1023px)" fetchpriority="high">
<link rel="preload" as="image" href="assets/video/tour_poster.jpg" media="not all and (orientation: portrait) and (max-width: 1023px)" fetchpriority="high">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@500;700;800&display=swap">
<link rel="stylesheet" href="assets/css/site.css?v={asset_v('assets/css/site.css')}">
<script>document.documentElement.classList.add('js');try{{if(localStorage.getItem('ipro-a11y')==='1')document.documentElement.classList.add('a11y')}}catch(e){{}}</script>
</head>
<body>
{{SPRITE}}
<a class="skip" href="#news">К содержанию</a>
{hdr}<main id="main">
{main}</main>
{foot}{bar}{dialogs}<script src="assets/js/site.js?v={asset_v('assets/js/site.js')}" defer></script>
</body>
</html>
'''


if __name__ == '__main__':
    html_out = page()
    html_out = html_out.replace('{SPRITE}', sprite())
    html_out = add_dims(html_out)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf8').write(html_out)
    os.makedirs(os.path.join(OUT, 'assets/data'), exist_ok=True)
    np = os.path.join(OUT, 'assets/data/news.json')
    if not os.path.exists(np) or '--reset-news' in sys.argv:
        json.dump(NEWS_SEED, open(np, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    print('index.html', len(html_out), 'bytes; icons:', len(USED))
