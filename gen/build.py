# -*- coding: utf-8 -*-
"""Собирает index.html сайта IPROSCHOOL, версия A «День под солнцем».
Сюжет одного школьного дня: солнце из логотипа открывает видео, утро у особняка (3D-пролёт),
дальше разделы идут по часам — 08:30 уроки, 12:40 обед, 14:30 после уроков, 18:00 домой —
а небо за страницей меняется от утра к ночи. Все разделы и тексты — как на нынешнем сайте."""
import html, json, os, re, sys, hashlib, shutil
sys.path.insert(0, os.path.dirname(__file__))
from content import *  # noqa

OUT = sys.argv[1]  # папка сайта
HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, 'icons')                 # иконки Lucide (ISC), которые использует сайт
LUCIDE_FULL = '/home/claude/npm/lucide/icons'        # полный набор, если есть: новые иконки докопируются в gen/icons
USED = set()


def e(s):
    return html.escape(str(s), quote=True)


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


def ss(name, sizes):
    """srcset с уменьшенной копией *-sm.jpg: телефон берёт лёгкую картинку, если ему её хватает."""
    from PIL import Image
    full = os.path.join(OUT, 'assets/img', name + '.jpg')
    sm = os.path.join(OUT, 'assets/img', name + '-sm.jpg')
    if not (os.path.exists(full) and os.path.exists(sm)):
        return ''
    with Image.open(full) as a, Image.open(sm) as b:
        wf, ws = a.size[0], b.size[0]
    if ws >= wf:
        return ''
    return f' srcset="assets/img/{name}-sm.jpg {ws}w, assets/img/{name}.jpg {wf}w" sizes="{sizes}"'


def small(path):
    """Уменьшенная копия *-sm.jpg, если она есть."""
    sm = path[:-4] + '-sm.jpg'
    return sm if os.path.exists(os.path.join(OUT, sm)) else path


def I(name, cls=''):
    USED.add(name)
    return f'<svg class="i{(" " + cls) if cls else ""}" aria-hidden="true"><use href="#i-{name}"/></svg>'


def kick(text, tag='p'):
    return f'<{tag} class="kick">{e(text)}</{tag}>'


def h2(title, em='', cls='h2'):
    t = e(title) + (f' <em>{e(em)}</em>' if em else '')
    longest = max(len(w) for w in (title + ' ' + em).split())
    if longest >= 14 and 'h2--xl' not in cls:  # «Профессиональная», «образовательная»: на телефоне такое слово не влезет в строку крупным кеглем
        cls += ' h2--long'
    return f'<h2 class="{cls}" data-split>{t}</h2>'


def more(label='Подробнее', tag='span', attrs='', cls=''):
    t = ' type="button"' if tag == 'button' else ''
    return f'<{tag} class="more{(" " + cls) if cls else ""}"{t}{attrs}>{e(label)}{I("arrow-right")}</{tag}>'


def aud(p):
    return f"{p['audience']}, {p['ages']}" if p['audience'] else p['ages']


def video(name, cls='', label='', autoplay=False):
    poster = small(f'assets/img/posters/{name}.jpg')  # лёгкий кадр: видео заменит его, как только дойдёт прокрутка
    attrs = 'muted loop playsinline' + (' autoplay preload="auto"' if autoplay else ' preload="none"')
    al = f' aria-label="{e(label)}"' if label else ' aria-hidden="true"'
    return f'<video class="{cls}" src="assets/video/{name}.mp4" poster="{poster}" {attrs}{al}></video>'


def ilist(items, cls=''):
    """Список с мини-иконками: тонкая иконка и текст школы, без плашек."""
    lis = ''.join(f'<li>{I(ic)}<span>{e(t)}</span></li>' for ic, t in items)
    return f'<ul class="il{(" " + cls) if cls else ""}">{lis}</ul>'


SUN_RAYS = ''.join(f'<path d="M{x1} {y1}L{x2} {y2}"/>' for x1, y1, x2, y2 in
                   [(0, -62, 0, -90), (0, 62, 0, 90), (-62, 0, -90, 0), (62, 0, 90, 0),
                    (44, -44, 63, -63), (-44, 44, -63, 63), (44, 44, 63, 63), (-44, -44, -63, -63)])


def sun_svg(cls=''):
    return (f'<svg class="sun{(" " + cls) if cls else ""}" viewBox="-100 -100 200 200" aria-hidden="true">'
            f'<circle r="44" fill="#FCC41C"/><g class="sun__rays" stroke="#FCC41C" stroke-width="10" stroke-linecap="round">{SUN_RAYS}</g></svg>')


# место солнца на дуге для каждого часа: доля пути с востока на запад
ARC_AT = {'08:30': .2, '12:40': .5, '14:30': .66, '18:00': .9}


def arc_point(t):
    """Точка на дуге солнца (та же кривая, что в th__arc): доли ширины и высоты."""
    u = 1 - t
    return u * u * .01 + 2 * u * t * .5 + t * t * .99, u * u * .9667 - 2 * u * t * .4667 + t * t * .9667


def timehead(key):
    """Время дня — заголовок главы: солнце на дуге, крупные часы и короткая фраза из LEADINS.
    Солнце сразу стоит на своём месте; скрипт ведёт его туда от места предыдущей главы."""
    t, phrase, _ = LEADINS[key]
    a = ARC_AT.get(t, .5)
    x, y = arc_point(a)
    return (f'<div class="th rv" data-arc="{a}">'
            f'<div class="th__sky" aria-hidden="true"><svg class="th__arc" viewBox="0 0 1000 120" preserveAspectRatio="none"><path d="M10 116 Q500 -56 990 116"/></svg>'
            f'<span class="th__sun" style="left:{x * 100:.2f}%;top:{y * 100:.2f}%">{sun_svg()}</span></div>'
            f'<p class="th__t"><span class="th__clock" data-time="{e(t)}" aria-hidden="true">{e(t)}</span><span class="vh">{e(t)}</span></p>'
            f'<p class="th__s">{e(phrase)}</p></div>')


_SKY = {'prev': None, 'tone': None}  # небо и тон предыдущей главы — главы собираются по порядку страницы


def section(id_, title, body, sky, tone='light', cls='', extra=''):
    """Глава страницы. Небо главы — две краски сверху вниз (--s1, --s2); вверху оно перетекает из неба
    предыдущей главы (--s0). Если тон меняется (светлая ↔ тёмная), глава заходит листом (is-cut)."""
    s1, s2 = sky.split(',')
    s0 = _SKY['prev'] or s1
    cut = _SKY['tone'] is not None and _SKY['tone'] != tone
    _SKY['prev'], _SKY['tone'] = s2, tone
    classes = f'sc sc--{tone}' + (' is-cut' if cut else '') + (f' {cls}' if cls else '')
    return (f'<section class="{classes}" id="{id_}" data-title="{e(title)}" data-tone="{tone}" style="--s0:{s0};--s1:{s1};--s2:{s2}"{extra}>\n'
            f'{body}\n</section>\n')


# ---------------------------------------------------------------- шапка, меню
def header():
    return f'''<header class="hd" id="hd">
  <a class="hd__logo" href="#top" data-go="top" aria-label="Ай Про, в начало"><img class="w" src="assets/img/wordmark-aipro.webp" alt=""><img class="n" src="assets/img/wordmark-aipro-navy.webp" alt=""></a>
  <span class="hd__ch" id="chapName" aria-hidden="true"></span>
  <a class="pill pill--sun hd__cta" href="#signup" data-go="signup">Пробные дни</a>
  <button class="hd__menu" id="menuBtn" type="button" aria-haspopup="dialog" aria-controls="menu" aria-expanded="false"><span class="hd__bars" aria-hidden="true"><i></i><i></i></span><span class="hd__lbl">Меню</span></button>
</header>
'''


def menu_dialog():
    items = []
    for target, label, kind in MENU:
        if kind == 'dialog':
            items.append(f'<li><a href="#{target}" data-open="{target}" class="menu__doc">{I("file-text")}<span>{e(label)}</span></a></li>')
        else:
            items.append(f'<li><a href="#{target}" data-go="{target}"><span>{e(label)}</span>{I("arrow-right")}</a></li>')
    c = CONTACTS
    return f'''<dialog class="drawer" id="menu" aria-label="Меню разделов">
  <div class="drawer__in">
    <div class="drawer__top">
      <a class="drawer__logo" href="#top" data-go="top"><img src="assets/img/wordmark-aipro-navy.webp" alt="Ай Про"></a>
      <button class="xbtn" type="button" data-close aria-label="Закрыть меню">{I('x')}</button>
    </div>
    <nav aria-label="Разделы сайта"><ul class="menu">{''.join(items)}</ul></nav>
    <a class="drawer__cta" href="#signup" data-go="signup"><span><b>Запишитесь на бесплатный пробный день</b><small>Три дня бесплатно и без обязательств</small></span>{I('arrow-right')}</a>
    <div class="drawer__contacts">
      <a class="drawer__phone" href="{c['phone_href']}">{I('phone')}<span>{e(c['phone'])}<small>{e(c['hours'])}</small></span></a>
      <div class="socials">
        <a href="{c['wa']}" target="_blank" rel="noopener">{I('message-circle')}WhatsApp</a>
        <a href="{c['tg']}" target="_blank" rel="noopener">{I('send')}Telegram</a>
        <a href="{c['vk']}" target="_blank" rel="noopener"><b class="sb">VK</b>ВКонтакте</a>
        <a href="{c['max']}" target="_blank" rel="noopener"><b class="sb">M</b>MAX</a>
      </div>
      <a class="drawer__addr" href="{c['map']}" target="_blank" rel="noopener">{I('map-pin')}<span>{e(c['address'])}<small>Школа на Яндекс Картах</small></span></a>
      <button class="a11y-toggle" type="button" aria-pressed="false">{I('eye')}<span>Версия для слабовидящих</span></button>
    </div>
  </div>
</dialog>
'''


# ---------------------------------------------------------------- главы
def hero():
    body = f'''  <div class="pin">
    <div class="hero__win">
      <video class="intro__v" data-src-land="assets/video/tour.mp4" data-src-port="assets/video/hero_school.mp4" data-poster-land="assets/video/tour_poster.jpg" data-poster-port="assets/img/posters/hero_school.jpg" poster="assets/video/tour_poster.jpg" muted loop playsinline autoplay preload="auto" aria-label="Видео о школе: классы, занятия, территория"></video>
      <div class="hero__tint"></div>
    </div>
    <svg class="hero__ring" viewBox="-100 -100 200 200" aria-hidden="true">
      <path d="M -51.96 -30 A 60 60 0 1 1 -51.96 30" fill="none" stroke="#FCC41C" stroke-width="8" stroke-linecap="round"/>
      <g class="hero__rays" stroke="#FCC41C" stroke-width="8" stroke-linecap="round"><path d="M0 -76V-94"/><path d="M38 -65.8L47 -81.4"/><path d="M65.8 -38L81.4 -47"/><path d="M76 0H94"/><path d="M65.8 38L81.4 47"/><path d="M38 65.8L47 81.4"/><path d="M0 76V94"/></g>
    </svg>
    <p class="hero__eyebrow">{e(INTRO['eyebrow'])}<span> · частная школа полного дня в Ялте</span></p>
    <h1 class="hero__h" aria-label="{e(INTRO['title1'] + ' ' + INTRO['title2'])}"><span class="row r1"><span class="l">Ребёнку</span><span class="l">интересно,</span></span><span class="row r2"><span class="l">а вам</span><span class="l acc">спокойно</span></span></h1>
    <a class="hero__hint" href="#news" data-go="news">Листайте</a>
  </div>'''
    return section('top', 'Начало', body, '#0A2C55,#0A2C55', 'dark', 'hero')


def news():
    cards = ''.join(news_card(n) for n in NEWS_SEED)
    data = json.dumps(NEWS_SEED, ensure_ascii=False)
    body = f'''  <div class="wrap">
    <div class="news__head">{kick('Новости и объявления', 'h2')}</div>
    <div class="news__list" id="newsList">{cards}</div>
  </div>
  <script type="application/json" id="newsSeed">{data}</script>'''
    return section('news', 'Новости', body, '#FFFFFF,#F2F8FE', 'light', 'news')


def news_card(n):
    date = f'<time>{e(n["date"])}</time>' if n.get('date') else ''
    tag = f'<span class="news__tag">{e(n.get("tag", ""))}</span>' if n.get('tag') else ''
    link = f'<a class="news__more" href="{e(n["link"])}">{e(n.get("link_text") or "Подробнее")}{I("arrow-right")}</a>' if n.get('link') else ''
    img = f'<img src="{e(n["image"])}" alt="" loading="lazy">' if n.get('image') else ''
    return f'<article class="news__card rv{" is-pin" if n.get("pin") else ""}">{img}<div class="news__meta">{tag}{date}</div><h3>{e(n["title"])}</h3><p>{e(n["text"])}</p>{link}</article>'


COLLAGE = [
    [('k_main', 'Дошкольники рисуют песком на световых столах', '3/4'), ('judo', 'Двое учеников в кимоно в броске на синих матах', '4/5'),
     ('herbs', 'Дети собирают букеты из трав и цветов в парке', '1/1'), ('drawings', 'Ученики показывают свои рисунки', '3/4')],
    [('p_main', 'Ученица начальной школы пишет за партой', '4/5'), ('theatre', 'Девочка в короне поёт на летней сцене', '3/4'),
     ('chess-club', 'Педагог разбирает шахматную партию с учениками', '4/5'), ('foam', 'Пенная вечеринка в летнем клубе', '3/4')],
    [('lineup', 'Ученики машут руками на линейке первого сентября', '1/1'), ('dance-yard', 'Танец на школьном празднике во дворе', '4/5'),
     ('costumes', 'Ученики в сценических костюмах на празднике', '3/4'), ('playground', 'Девочка на качелях в парке', '1/1')],
]


def concept():
    c = CONCEPT
    cols = ''
    for ci, col in enumerate(COLLAGE):
        figs = ''.join(f'<figure style="--ar:{ar}"><img src="{small("assets/img/" + n + ".jpg")}" alt="{e(alt)}" decoding="async"></figure>' for n, alt, ar in col)
        cols += f'<div class="col" data-speed="{(-0.14, 0.1, -0.24)[ci]}">{figs}</div>'
    stats = ''
    for n, l, _ in c['stats']:
        digits = re.sub(r'[^0-9]', '', n)
        cnt = f' data-count="{digits}"' if n.isdigit() or n.endswith('+') else ''
        stats += f'<div class="num rv"><b{cnt}>{e(n)}</b><span>{e(l)}</span></div>'
    groups = ''
    for title, tone, items in c['groups']:
        groups += f'<article class="grp grp--{tone} rv"><h3>{e(title)}</h3>{ilist(items)}</article>'
    body = f'''  <div class="wrap concept__head">
    {kick(c['chip'])}
    {h2(c['title'], c['title_em'], 'h2 h2--xl')}
    <p class="lead rv">{e(c['lead'])}</p>
  </div>
  <div class="cols" aria-label="Фото из жизни школы">{cols}</div>
  <div class="wrap">
    <div class="nums">{stats}</div>
    <div class="grps">{groups}</div>
  </div>'''
    return section('concept', 'Концепция', body, '#FFFFFF,#FFFFFF', 'light', 'concept')


PINS = [(330, 452, 'Особняк в 5 этажей'), (625, 588, 'Летний бассейн'), (505, 736, 'Охраняемая территория'), (150, 560, '1 га в парке')]


def about():
    a = ABOUT
    vids = ''.join(f'<figure class="trio__v rv">{video(v, "", label)}<figcaption>{e(label)}</figcaption></figure>' for v, label in a['videos'])
    pins = ''.join(f'<li data-x="{x}" data-y="{y}"><span>{e(t)}</span></li>' for x, y, t in PINS)
    body = f'''  <div class="estate" data-seq="estate" data-frames="61" data-path="assets/seq/estate" data-ext="webp">
    <div class="pin">
      <canvas aria-hidden="true"></canvas>
      <img class="seq__poster" src="assets/seq/estate/f_000.webp" alt="3D-макет особняка школы: дом, сад, бассейн и ворота">
      <div class="estate__veil" aria-hidden="true"></div>
      <div class="wrap estate__head">{kick(LEADINS['about'][1])}{h2(a['title'], a['title_em'])}</div>
      <ul class="pins" aria-label="Что есть на территории">{pins}</ul>
      <div class="wrap estate__arrive"><b>Добро пожаловать</b><p>Школа ждёт ребёнка с 8:30 до 18:00</p></div>
    </div>
  </div>
  <div class="wrap about__more">
    <div class="trio">{vids}</div>
    <figure class="director rv">
      <blockquote>{e(a['quote'])}</blockquote>
      <figcaption>{e(a['sign'])}</figcaption>
    </figure>
  </div>'''
    return section('about', 'О школе', body, '#FFFFFF,#F4F9FE', 'light', 'about')


def programs():
    P = PROGRAMS_INTRO
    cards = ''
    for i, p in enumerate(PROGRAMS):
        cards += f'''<a class="lvl lvl--{p['key']}" style="--i:{i}" href="#m-{p['key']}" data-open="m-{p['key']}" aria-label="{e(p['title'])}, {e(aud(p))}: подробнее о программе">
      <span class="lvl__top"><span class="lvl__n">0{p['step']}</span><span class="lvl__lvl">{e(p['level'])}</span></span>
      <span class="lvl__txt"><b class="lvl__t">{e(p['title'])}</b><span class="lvl__a">{e(aud(p))}</span></span>
      <span class="lvl__ph"><img src="assets/img/{p['img']}.jpg"{ss(p['img'], '(max-width: 900px) 90vw, 560px')} alt="" loading="lazy"></span>
      {more('Программа и расписание')}
    </a>'''
    body = f'''  <div class="wrap">
    {timehead('programs')}
    {h2(P['title'], P['title_em'])}
    <div class="stack">{cards}</div>
  </div>'''
    return section('programs', 'Программы и расписание', body, '#CFE7FB,#FFF3DA', 'light', 'programs')


def food():
    f = FOOD
    body = f'''  <div class="wrap split">
    <div class="split__txt">{timehead('food')}{h2(f['title'], f['title_em'])}{ilist(f['items'], 'rv')}</div>
    <figure class="ph ph--tall rv"><img src="assets/img/food.jpg" alt="Дети выбирают еду на шведском столе" loading="lazy"></figure>
  </div>'''
    return section('food', 'Питание', body, '#8AC8F5,#DDEFFD', 'light', 'food')


def teachers():
    t = TEACHERS
    cards = ''.join(f'<figure class="person rv"><span class="person__ph"><img src="assets/img/{img}.jpg"{ss(img, "(max-width: 900px) 46vw, 300px")} alt="{e(name)}" loading="lazy"></span><figcaption><b>{e(name)}</b><span>{e(role)}</span></figcaption></figure>' for img, name, role in t['people'])
    body = f'''  <div class="wrap">
    {kick(LEADINS['teachers'][1])}
    {h2(t['title'], t['title_em'])}
    <div class="people">{cards}</div>
  </div>'''
    return section('teachers', 'Педагоги', body, '#A5D3F6,#EAF5FD', 'light', 'teachers')


def safety():
    s = SAFETY
    body = f'''  <div class="wrap">
    {kick(LEADINS['safety'][1])}
    {h2(s['title'], s['title_em'])}
    <div class="split split--safety">
      <figure class="ph rv">{video('terr_walk', '', 'Прогулка по территории школы: башня с воротами, парковые дорожки, детская площадка')}<figcaption class="area"><b>{e(s['area'][0])}</b>{e(s['area'][1])}</figcaption></figure>
      {ilist(s['items'], 'il--big rv')}
    </div>
  </div>'''
    return section('safety', 'Безопасность', body, '#1F5A96,#2A70B4', 'dark', 'safety')


def extra():
    x = EXTRA
    dirs = ''
    for dr in x['directions']:
        dirs += f'''<button type="button" class="dirc rv" data-album="{dr['key']}" aria-label="{e(dr['name'])}: фото и видео">
      <span class="dirc__ph"><img src="assets/img/{dr['cover']}.jpg"{ss(dr['cover'], '(max-width: 900px) 92vw, 30vw')} alt="" loading="lazy"></span>
      <span class="dirc__cap"><b>{e(dr['name'])}</b><span>{e(' · '.join(dr['list']))}</span>{more('Фото и видео')}</span>
    </button>'''
    guests = ''.join(f'<article class="guest rv"><span class="guest__mono" aria-hidden="true">{e(n[0])}</span><div><b>{e(n)}</b><span class="guest__what">{e(w)}</span><p>{e(c)}</p></div></article>' for n, w, ill, c in x['guests'])
    body = f'''  <div class="wrap">
    {timehead('extra')}
    {h2(x['title'], x['title_em'])}
    <p class="lead rv">{e(x['lead'])}</p>
    <div class="dirs">{dirs}</div>
    <div class="meet">
      <h3 class="h3" data-split>{e(x['meet_title'])}</h3>
      <p class="lead rv">{e(x['meet_lead'])}</p>
      <div class="guests">{guests}</div>
    </div>
  </div>'''
    return section('extra', 'Авторская программа', body, '#FFD36A,#FFF0C4', 'light', 'extra')


def transfer():
    t = TRANSFER
    (i1, n1), (i2, n2) = t['route']
    body = f'''  <div class="wrap">
    <div class="split">
      <div class="split__txt">{timehead('transfer')}{h2(t['title'], t['title_em'])}<p class="lead rv">{e(t['lead'])}</p>{ilist(t['items'], 'rv')}</div>
      <figure class="ph rv"><img src="assets/img/bus.jpg" alt="Микроавтобус школьного трансфера на дорожке у парка" loading="lazy"></figure>
    </div>
    <div class="route rv" data-route aria-hidden="true">
      <svg viewBox="0 0 1000 160" preserveAspectRatio="none"><path class="route__line" d="M70 120 C 240 120, 280 40, 430 50 S 640 140, 780 90 S 900 40, 930 40"/><path class="route__done" d="M70 120 C 240 120, 280 40, 430 50 S 640 140, 780 90 S 900 40, 930 40"/></svg>
      <span class="route__pt route__pt--a">{I(i1)}<b>{e(n1)}</b></span>
      <span class="route__pt route__pt--b">{I(i2)}<b>{e(n2)}</b></span>
      <span class="route__bus">{I('bus')}</span>
    </div>
  </div>'''
    return section('transfer', 'Трансфер', body, '#F6A26C,#FFDAB4', 'light', 'transfer')


def summer():
    s = SUMMER
    eps = ''.join(f'''<article class="ep rv"><span class="ep__ph"><img src="assets/img/{img}.jpg"{ss(img, '(max-width: 900px) 92vw, 30vw')} alt="{e(alt)}" loading="lazy"></span>
      <div class="ep__txt"><p class="ep__k">{e(mon)}</p><h3>{e(title)}</h3><p>{text}</p></div></article>''' for n, mon, title, text, img, alt in s['episodes'])
    body = f'''  <div class="wrap">
    {kick('Июнь · Июль · Август')}
    {h2(s['title'], s['title_em'])}
    <p class="lead rv">{e(s['lead'])}</p>
    <figure class="ph ph--wide rv">{video('summer_yard', '', 'Летний клуб во дворе школы: рисунки мелками и танцы')}</figure>
    {ilist(s['facts'], 'il--2 rv')}
    <div class="eps">{eps}</div>
    {more('Смотреть фото и видео лета', 'button', ' data-album="summer"', 'more--pill rv')}
  </div>'''
    return section('summer', 'Летний клуб', body, '#FFE27E,#FFF6D8', 'light', 'summer')


def reviews():
    r = REVIEWS
    hi = r.get('hero', -1)
    big = ''
    if 0 <= hi < len(r['items']):
        q, n, src = r['items'][hi]
        big = f'<figure class="bigq"><blockquote data-split>«{q}»</blockquote><figcaption>{e(n)}, {e(src)}</figcaption></figure>'
    cards = ''.join(f'<figure class="review rv"><blockquote>{q}</blockquote><figcaption><span class="review__ava" aria-hidden="true">{e(n[0])}</span><span><b>{e(n)}</b><small>{e(src)}</small></span></figcaption></figure>' for i, (q, n, src) in enumerate(r['items']) if i != hi)
    st5 = ''.join(I('star', 'st') for _ in range(5))
    stars = f'<span class="stars" style="--v:{r["rating_value"] / 5:.3f}"><span class="stars__bg">{st5}</span><span class="stars__fg">{st5}</span></span>'
    body = f'''  <div class="wrap">
    {kick(r['title'] + ' ' + r['title_em'], 'h2')}
    {big}
    <a class="rating rv" href="{CONTACTS['map']}" target="_blank" rel="noopener"><b>{r['rating']}</b><span class="rating__r">{stars}<span>{e(r['count'])} на Яндекс Картах</span><span class="more">Все отзывы{I('arrow-up-right')}</span></span></a>
    <div class="revs">{cards}</div>
  </div>'''
    return section('reviews', 'Отзывы', body, '#B24F4E,#2B3F7A', 'dark', 'reviews')


def admission():
    a = ADMISSION
    steps = ''.join(f'<li class="rv"><span class="step__n">{i + 1}</span><p><b>{e(t)}</b>{e(d)}</p></li>' for i, (t, d) in enumerate(a['steps']))
    inc = ''.join(f'<li>{I("check")}{e(t)}</li>' for t in a['included'])
    lbl, head, sub = a['cost']
    body = f'''  <div class="wrap">
    {kick('Поступление')}
    {h2(a['title'], a['title_em'])}
    <div class="adm">
      <ol class="steps">{steps}</ol>
      <article class="price rv">
        <p class="price__lbl">{e(lbl)}</p>
        <h3 class="price__h">{e(head)}</h3>
        <p class="price__sub">{e(sub)}</p>
        <p class="price__lbl">Уже входит в стоимость</p>
        <ul class="price__inc">{inc}</ul>
        <p class="price__sale">{I('badge-percent')}<span><b>{e(a['sale'][0])}</b>{e(a['sale'][1])}</span></p>
        <a class="pill pill--sun price__go" href="#signup" data-go="signup">Прийти на пробные дни {I('arrow-right')}</a>
      </article>
      <a class="doclink rv" href="#docs" data-open="docs">{I('file-badge')}<span><b>Лицензия и документы</b><small>госаккредитация, холдинг Mirapolis</small></span>{I('arrow-right')}</a>
    </div>
  </div>'''
    return section('admission', 'Поступление', body, '#22356B,#162A50', 'dark', 'admission')


def gallery():
    cards = ''
    for i, (k, label) in enumerate(GALLERY_TABS):
        n = sum(1 for g in GALLERY if g[0] == k)
        cards += f'''<button type="button" class="alb rv" data-album="{k}" aria-label="{e(label)}: {n} фото и видео">
      <span class="alb__ph"><img src="assets/img/{GALLERY_COVERS[k]}.jpg"{ss(GALLERY_COVERS[k], '(max-width: 900px) 92vw, 40vw')} alt="" loading="lazy"></span>
      <span class="alb__cap"><b>{e(label)}</b><small>{n} фото и видео</small></span>
    </button>'''
    body = f'''  <div class="wrap">
    {kick('Галерея')}
    {h2('Фото и видео', 'школы')}
    <div class="albs">{cards}</div>
  </div>'''
    return section('gallery', 'Галерея', body, '#152A52,#0F2040', 'dark', 'gallery')


def night():
    a = ACTS['night']
    body = f'''  <div class="nightseq" data-seq="night" data-frames="55" data-path="assets/seq/night" data-ext="webp">
    <div class="pin">
      <canvas aria-hidden="true"></canvas>
      <img class="seq__poster" src="assets/seq/night/f_054.webp" alt="Особняк школы вечером, в окнах горит свет">
      <h2 class="night__bye">{e(a['name'])}</h2>
      <div class="night__cta wrap">
        <a class="badge" href="#signup" data-go="signup" aria-label="Записаться на 3 бесплатных пробных дня">
          <svg class="badge__ring" viewBox="0 0 100 100" aria-hidden="true"><defs><path id="badgeCirc" d="M50 50m-38 0a38 38 0 1 1 76 0a38 38 0 1 1-76 0"/></defs><text><textPath href="#badgeCirc">ЗАПИСАТЬСЯ · 3 ДНЯ БЕСПЛАТНО ·</textPath></text></svg>
          {I('arrow-up-right', 'badge__arrow')}
        </a>
        <p>Ждём вас и ребёнка на пробных днях: 3 дня бесплатно и без обязательств</p>
      </div>
    </div>
  </div>'''
    return section('act-night', a['name'], body, '#0A121C,#0A121C', 'dark', 'night')


def signup():
    s = SIGNUP
    c = CONTACTS
    body = f'''  <div class="wrap">
    <div class="split split--signup">
      <div class="split__txt">{kick('Запись')}{h2(s['title'], s['title_em'])}<p class="lead rv">{e(s['lead'])}</p>
        <p class="signup__call">Или позвоните: <a href="{c['phone_href']}">{e(c['phone'])}</a></p></div>
      <div class="formcard rv">
        <form class="form" id="signupForm" novalidate data-endpoint="">
          <label class="field" for="f-name"><span>Имя <i>*</i></span><input id="f-name" name="name" autocomplete="name" placeholder="Как вас зовут" required><small class="field__err">Напишите имя, чтобы мы знали, к кому обращаться.</small></label>
          <label class="field" for="f-age"><span>Возраст ребёнка</span><input id="f-age" name="age" inputmode="numeric" placeholder="Например, 8"></label>
          <label class="field" for="f-phone"><span>Телефон <i>*</i></span><input id="f-phone" name="phone" type="tel" autocomplete="tel" placeholder="+7 (978) 000-00-00" required><small class="field__err">Введите номер телефона, чтобы мы могли перезвонить.</small></label>
          <button class="pill pill--sun form__go" type="submit">Записаться {I('arrow-right')}</button>
          <p class="form__note">{e(s['note'])}</p>
        </form>
        <div class="sent" id="signupSent" hidden tabindex="-1">
          <span class="sent__ok">{I('check')}</span>
          <h3 id="sentTitle">Остался один шаг</h3>
          <p id="sentText">Отправьте заявку в удобный мессенджер — текст уже готов. Или позвоните, мы подберём даты пробных дней.</p>
          <div class="sent__btns">
            <a class="pill pill--green" id="sentWa" href="{c['wa']}" target="_blank" rel="noopener">{I('message-circle')} Отправить в WhatsApp</a>
            <a class="msgr" href="{c['tg']}" target="_blank" rel="noopener">{I('send')}Telegram</a>
            <a class="msgr" href="{c['max']}" target="_blank" rel="noopener"><b class="sb">M</b>MAX</a>
            <a class="msgr" href="{c['phone_href']}">{I('phone')}{e(c['phone'])}</a>
          </div>
          <button class="linkbtn" type="button" id="sentBack">Изменить данные</button>
        </div>
      </div>
    </div>
    {footer()}
  </div>'''
    return section('signup', 'Запись на пробные дни', body, '#0A121C,#0A121C', 'dark', 'signup')


def footer():
    c = CONTACTS
    return f'''<footer class="foot">
      <div class="foot__brand"><img src="assets/img/wordmark-aipro.webp" width="480" height="377" alt="Ай Про"><p>Частная школа полного дня в Ялте для детей 4–18 лет</p></div>
      <div class="foot__contacts">
        <a class="foot__phone" href="{c['phone_href']}">{e(c['phone'])}</a><span>{e(c['hours'])}</span>
        <a href="mailto:{c['email']}">{e(c['email'])}</a>
        <a href="{c['map']}" target="_blank" rel="noopener">{e(c['address'])}</a>
        <div class="socials socials--row">
          <a href="{c['wa']}" target="_blank" rel="noopener">WhatsApp</a>
          <a href="{c['tg']}" target="_blank" rel="noopener">Telegram</a>
          <a href="{c['vk']}" target="_blank" rel="noopener">ВКонтакте</a>
          <a href="{c['max']}" target="_blank" rel="noopener">MAX</a>
        </div>
      </div>
      <div class="foot__map">
        <iframe title="Ай Про на Яндекс Картах" src="about:blank" data-src="{c['map_embed']}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        <a class="foot__maplink" href="{c['map']}" target="_blank" rel="noopener">{I('map-pin')}Открыть на Яндекс Картах</a>
      </div>
      <div class="foot__bottom">
        <span>© 2026 Ай Про (IPROSCHOOL)</span>
        <a href="#docs" data-open="docs">Сведения об образовательной организации</a>
        <button type="button" class="a11y-toggle a11y-toggle--link" aria-pressed="false">{I('eye')}Версия для слабовидящих</button>
        <a href="#top" data-go="top">Наверх {I('arrow-up')}</a>
      </div>
    </footer>'''


# ---------------------------------------------------------------- окна
def program_dialog(p, prev, nxt):
    k = p['key']
    L = LABELS
    base = ''.join(f'<li class="{"hl" if len(b) > 2 and b[2] else ""}">{I("sparkles" if len(b) > 2 and b[2] else "check")}<span><b>{e(b[0])}</b>{("<small>" + e(b[1]) + "</small>") if len(b) > 1 and b[1] else ""}</span></li>' for b in p['base'])
    dl = lambda xs, cls='': f'<ul class="dl2{(" " + cls) if cls else ""}">' + ''.join(f'<li>{e(x)}</li>' for x in xs) + '</ul>'
    req = (f'<p class="sub"><span class="tag tag--fill">{L["required"]}</span></p>' + dl(p['author_required'], 'dl2--fill')) if p['author_required'] else ''
    choice = f'<p class="sub"><span class="tag">{L["choice"]}</span></p>' + dl(p['author_choice'])
    ind = dl(p['individual'])
    day = ''.join(f'<li><time>{e(t)}</time><span>{e(w)}</span></li>' for t, w in p['day'])
    toc = [(f'{k}-base', L['base']), (f'{k}-author', 'Авторская программа'), (f'{k}-ind', L['individual']), (f'{k}-day', p['day_title'])]
    toc_h = ''.join(f'<a href="#{a}" data-jump><b>0{i + 1}</b>{e(t)}</a>' for i, (a, t) in enumerate(toc))
    return f'''<dialog class="pm pm--{k}" id="m-{k}" data-k="{k}" aria-labelledby="t-{k}">
  <div class="pm__bar"><span><b>{e(p['title'])}</b> · {e(p['level'])}</span><button class="xbtn" type="button" data-close aria-label="Закрыть">{I('x')}</button></div>
  <section class="pm__hero">
    <div class="pm__hero-in">
      <div><p class="pm__lvl">0{p['step']} · {e(p['level'])}</p><h2 class="pm__t" id="t-{k}">{e(p['title'])}</h2><p class="pm__aud">{e(aud(p))}</p></div>
      <span class="pm__ph"><img src="assets/img/{p['img']}.jpg" alt="{e(p['alt'])}" loading="lazy"></span>
    </div>
  </section>
  <div class="pm__body">
    <nav class="pm__toc" aria-label="Оглавление программы">{toc_h}</nav>
    <section class="dsec" id="{k}-base"><h3>{L['base']}</h3><ul class="bl">{base}</ul></section>
    <section class="dsec" id="{k}-author"><h3>{L['author']}</h3>{req}{choice}</section>
    <section class="dsec" id="{k}-ind"><div class="dsec__h"><h3>{L['individual']}</h3><span class="note">{L['individual_note']}</span></div>{ind}</section>
    <section class="dsec" id="{k}-day"><h3>{e(p['day_title'])}</h3><ol class="times">{day}</ol></section>
    <nav class="pn" aria-label="Другие программы">
      <a href="#m-{prev['key']}" data-open="m-{prev['key']}"><small>← {e(prev['level'])}</small><b>{e(prev['title'])}</b></a>
      <a href="#m-{nxt['key']}" data-open="m-{nxt['key']}"><small>{e(nxt['level'])} →</small><b>{e(nxt['title'])}</b></a>
    </nav>
    <div class="pm__cta"><span>Приходите на пробные дни</span><a class="pill pill--sun" href="#signup" data-close-go="signup">Записаться {I('arrow-right')}</a></div>
  </div>
</dialog>
'''


def docs_dialog():
    c = CONTACTS
    docs = ''.join(f'<li>{I(ic)}<span><b>{e(t)}</b>{e(s)}</span></li>' for ic, t, s in ADMISSION['docs'])
    return f'''<dialog class="sheet" id="docs" aria-labelledby="docsT">
  <div class="sheet__bar"><h2 id="docsT">Сведения об образовательной организации</h2><button class="xbtn" type="button" data-close aria-label="Закрыть">{I('x')}</button></div>
  <div class="sheet__body">
    <p class="label">Лицензия и документы</p>
    <ul class="docs__list">{docs}</ul>
    <p class="label">Контакты организации</p>
    <dl class="kv">
      <dt>Адрес</dt><dd>{e(c['address'])}</dd>
      <dt>Телефон</dt><dd><a href="{c['phone_href']}">{e(c['phone'])}</a></dd>
      <dt>Электронная почта</dt><dd><a href="mailto:{c['email']}">{e(c['email'])}</a></dd>
      <dt>Режим работы</dt><dd>{e(c['hours'])}</dd>
    </dl>
    <p class="label">Реквизиты и документы</p>
    <p class="ph-note">Полное наименование, ИНН, ОГРН, сканы лицензии и уставных документов разместим здесь по данным школы.</p>
  </div>
</dialog>
'''


def media_item(kind, src, alt):
    if kind == 'video':
        pf = f'assets/img/posters/{src}.jpg'
        return {'k': 'v', 'full': f'assets/video/{src}.mp4', 'th': small(pf), 'pf': pf, 'alt': alt}
    return {'k': 'i', 'full': f'assets/img/{src}.jpg', 'th': small(f'assets/img/{src}.jpg'), 'alt': alt}


def album_dialog():
    data = {}
    for k, label in GALLERY_TABS:
        data[k] = {'t': label, 'g': 'gal', 'items': [media_item(kind, src, alt) for cat, kind, src, alt in GALLERY if cat == k]}
    for dr in EXTRA['directions']:
        data[dr['key']] = {'t': dr['name'], 'g': 'dir', 'sub': ' · '.join(dr['list']), 'items': [media_item(kind, src, alt) for kind, src, alt in dr['media']]}
    js = json.dumps(data, ensure_ascii=False)
    return f'''<dialog class="album" id="album" aria-labelledby="albumT">
  <div class="album__bar"><h2 id="albumT">Фото и видео</h2><button class="xbtn" type="button" data-close aria-label="Закрыть">{I('x')}</button></div>
  <div class="album__body">
    <nav class="album__tabs" id="albumTabs" aria-label="Разделы"></nav>
    <p class="album__sub" id="albumSub" hidden></p>
    <div class="album__grid" id="albumGrid"></div>
  </div>
  <template id="albumPlay">{I('play')}</template>
  <script type="application/json" id="albumData">{js}</script>
</dialog>
'''


def lightbox():
    return f'''<dialog class="lightbox" id="lightbox" aria-label="Просмотр фото и видео">
  <button class="xbtn lightbox__x" type="button" data-close aria-label="Закрыть">{I('x')}</button>
  <div class="lightbox__stage" id="lbStage"></div>
  <p class="lightbox__cap" id="lbCap"></p>
  <button class="lightbox__nav lightbox__nav--prev" type="button" data-lb="-1" aria-label="Предыдущее">{I('chevron-left')}</button>
  <button class="lightbox__nav lightbox__nav--next" type="button" data-lb="1" aria-label="Следующее">{I('chevron-right')}</button>
</dialog>
'''


def helper_dialog():
    c = CONTACTS
    qs = ''.join(f'<button type="button" data-q="{i}">{e(q)}</button>' for i, (q, _) in enumerate(HELPER))
    data = json.dumps([{'q': q, 'a': a} for q, a in HELPER], ensure_ascii=False)
    return f'''<dialog class="helper" id="helper" aria-labelledby="helperT">
  <div class="helper__bar"><span class="helper__ava">{sun_svg()}</span><span><b id="helperT">Помощник Ай Про</b><small>Отвечаю на вопросы о школе</small></span><button class="xbtn" type="button" data-close aria-label="Закрыть помощника">{I('x')}</button></div>
  <div class="helper__log" id="helperLog" aria-live="polite"><p class="bub">Здравствуйте! Подскажу по школе Ай Про — выберите вопрос ниже.</p></div>
  <div class="helper__qs" id="helperQs">{qs}</div>
  <p class="helper__foot">Не нашли ответ? Позвоните <a href="{c['phone_href']}">{e(c['phone'])}</a>, напишите в <a href="{c['wa']}" target="_blank" rel="noopener">WhatsApp</a> или <a href="{c['tg']}" target="_blank" rel="noopener">Telegram</a>.</p>
  <script type="application/json" id="helperData">{data}</script>
</dialog>
<button class="ask" type="button" data-open="helper" aria-label="Вопросы о школе">{I('message-circle-question-mark')}<span>Вопросы?</span></button>
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
    main = (hero() + news() + concept() + about() + programs() + food() + teachers() + safety()
            + extra() + transfer() + summer() + reviews() + admission() + gallery() + night() + signup())
    n = len(PROGRAMS)
    dialogs = ''.join(program_dialog(p, PROGRAMS[(i - 1) % n], PROGRAMS[(i + 1) % n]) for i, p in enumerate(PROGRAMS))
    dialogs += menu_dialog() + docs_dialog() + album_dialog() + lightbox() + helper_dialog()
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
<meta property="og:site_name" content="Ай Про · IPROSCHOOL">
<meta property="og:title" content="Ай Про · частная школа полного дня в Ялте">
<meta property="og:description" content="Детский сад и школа в историческом особняке: малые группы, языки с носителями, кружки, питание и трансфер. Три пробных дня бесплатно.">
<meta property="og:image" content="assets/og.jpg">
<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;600;700&family=Onest:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="assets/css/site.css?v={asset_v('assets/css/site.css')}">
<script>document.documentElement.classList.add('js');try{{if(localStorage.getItem('ipro-a11y')==='1')document.documentElement.classList.add('a11y')}}catch(e){{}}</script>
</head>
<body>
{{SPRITE}}
<a class="skip" href="#concept">К содержанию</a>
{header()}<main id="main">
{main}</main>
{dialogs}<script src="assets/js/site.js?v={asset_v('assets/js/site.js')}" defer></script>
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
