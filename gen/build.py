# -*- coding: utf-8 -*-
"""Собирает index.html сайта IPROSCHOOL, версия A: день в Ай Про — подводки к блокам по часам
(08:30 уроки, 12:40 обед, 14:30 после уроков, 18:00 домой)."""
import html, json, os, re, sys, hashlib, shutil
sys.path.insert(0, os.path.dirname(__file__))
from content import *  # noqa

OUT = sys.argv[1]  # папка сайта (репозиторий ipro-b)
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


def I(name, cls=''):
    USED.add(name)
    return f'<svg class="i{(" " + cls) if cls else ""}" aria-hidden="true"><use href="#i-{name}"/></svg>'


def kicker(num, text):
    n = f'<span>{e(num)}</span>' if num else ''
    return f'<p class="kicker">{n}{e(text)}</p>'


def h2(title, em='', cls='h2'):
    t = e(title) + (f' <em>{e(em)}</em>' if em else '')
    return f'<h2 class="{cls}" data-split>{t}</h2>'


def sl(items, cls=''):
    """Спокойный список: иконка в цвет главы, жирная строка, пояснение под ней. Без коробок."""
    lis = ''
    for it in items:
        ic, b, d = (it + ('',))[:3]
        lis += f'<li>{I(ic)}<p><b>{e(b)}</b>{("<span>" + e(d) + "</span>") if d else ""}</p></li>'
    return f'<ul class="sl rv{(" " + cls) if cls else ""}">{lis}</ul>'


def more(label='Подробнее', tag='span', attrs='', cls=''):
    """Явная подпись у всего, что открывается: «Подробнее →»."""
    t = ' type="button"' if tag == 'button' else ''
    return f'<{tag} class="more{(" " + cls) if cls else ""}"{t}{attrs}>{e(label)}{I("arrow-right")}</{tag}>'


def aud(p):
    return f"{p['audience']}, {p['ages']}" if p['audience'] else p['ages']


def video(name, cls='', label='', autoplay=False, poster=None):
    poster = poster or f'assets/img/posters/{name}.jpg'
    attrs = 'muted loop playsinline' + (' autoplay preload="auto"' if autoplay else ' preload="none"')
    al = f' aria-label="{e(label)}"' if label else ' aria-hidden="true"'
    return f'<video class="{cls}" src="assets/video/{name}.mp4" poster="{poster}" {attrs}{al}></video>'


# короткие подписи главы в капсуле на телефоне (полная не помещается)
SHORT = {'news': 'Новости', 'programs': 'Программы', 'extra': 'Кружки', 'act-night': 'До встречи', 'signup': 'Запись'}


def li(key):
    """Подводка к блоку — короткая строка над заголовком: время дня и фраза."""
    if key not in LEADINS:
        return ''
    t, phrase = LEADINS[key][:2]
    tm = f'<b class="li__t" data-time="{e(t)}">{e(t)}</b>' if t else ''
    return f'<p class="eyebrow rv">{tm}<span>{e(phrase)}</span></p>'


def ilist(items, cls=''):
    """Список с мини-иконками в квадратиках (как в концепции) — по ним проще ориентироваться."""
    lis = ''.join(f'<li><span class="mi">{I(ic)}</span><span>{e(t)}</span></li>' for ic, t in items)
    return f'<ul class="ilist2{(" " + cls) if cls else ""}">{lis}</ul>'


def glist(items):
    """Список фактов на стеклянной панели: мини-иконка в квадратике и текст школы."""
    lis = ''.join(f'<li><span class="gl__ic">{I(ic)}</span><span>{e(t)}</span></li>' for ic, t in items)
    return f'<ul class="gl">{lis}</ul>'


def floats(key):
    return ''  # 3D-эмодзи убраны: живые фото, видео и 3D-макет школы — сильнее


def section(id_, pal, title, num, body, cls='', extra=''):
    num = LEADINS.get(id_, ('', ''))[0]  # в капсуле — время дня вместо номера сцены
    if id_ in SHORT:
        extra += f' data-short="{e(SHORT[id_])}"'
    return (f'<section class="sc pal-{pal}{(" " + cls) if cls else ""}" id="{id_}" data-title="{e(title)}" data-num="{e(num)}"{extra}>\n'
            f'{body}\n</section>\n')


# ---------------------------------------------------------------- шапка, меню
def dock():
    return f'''<header class="dock">
  <div class="dock__in">
    <a class="dock__brand" href="#top" aria-label="Ай Про, частная школа, в начало"><img src="assets/img/logo-aipro.webp" width="160" height="184" alt=""><span>Ай Про<small>школа полного дня</small></span></a>
    <button class="dock__ch" id="menuBtn" type="button" aria-haspopup="dialog" aria-controls="menu" aria-label="Открыть меню разделов">
      <b id="chapNum">00</b><span id="chapName">Начало</span>{I('menu', 'dock__burger')}
    </button>
    <a class="pill pill--blue dock__cta" href="#signup">Пробные дни</a>
    <i class="dock__bar" aria-hidden="true"></i>
  </div>
</header>
<nav class="dots" aria-label="Главы"></nav>
'''


def menu_dialog():
    items = []
    for i, (target, label, kind) in enumerate(MENU):
        if kind == 'dialog':
            items.append(f'<li><a href="#{target}" data-open="{target}" class="menu__doc">{I("file-text")}<span>{e(label)}</span></a></li>')
        else:
            items.append(f'<li><a href="#{target}" data-go="{target}"><span>{e(label)}</span>{I("arrow-right")}</a></li>')
    c = CONTACTS
    return f'''<dialog class="drawer" id="menu" aria-label="Меню разделов">
  <div class="drawer__in">
    <div class="drawer__top">
      <a class="dock__brand" href="#top" data-go="top"><img src="assets/img/logo-aipro.webp" width="160" height="184" alt=""><span>Ай Про<small>частная школа полного дня</small></span></a>
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
def intro():
    words = (INTRO['title1'] + ' ' + INTRO['title2']).split(' ')
    h = ''.join(f'<span class="w{" acc" if i >= 2 else ""}" style="--i:{i}">{e(w)}</span>' + ('<br>' if i == 1 else ' ') for i, w in enumerate(words))
    body = f'''  <div class="intro__media">
    <video class="intro__v" data-src-land="assets/video/tour.mp4" data-src-port="assets/video/hero_school.mp4" data-poster-land="assets/video/tour_poster.jpg" data-poster-port="assets/img/posters/hero_school.jpg" poster="assets/video/tour_poster.jpg" muted loop playsinline autoplay preload="auto" aria-label="Видео о школе: классы, занятия, территория"></video>
  </div>
  <div class="wrap intro__in">
    <img class="intro__mark up" src="assets/img/wordmark-aipro.webp" width="1200" height="942" alt="Ай Про">
    <p class="kicker up">{e(INTRO['eyebrow'])}</p>
    <h1 class="h1">{h.strip()}</h1>
  </div>
  <a class="cue" href="#news">Листайте{I('arrow-down')}</a>'''
    return section('top', 'dawn', 'Начало', '00', body, 'intro')



def news():
    cards = ''.join(news_card(n) for n in NEWS_SEED)
    data = json.dumps(NEWS_SEED, ensure_ascii=False)
    body = f'''  <span class="grab" aria-hidden="true"></span>
  <div class="wrap news">
    <div class="news__head"><h2 class="h3">Новости и объявления</h2></div>
    <div class="news__list hs" id="newsList">{cards}</div>
  </div>
  <script type="application/json" id="newsSeed">{data}</script>'''
    return section('news', 'morning', 'Новости и объявления', '', body, 'sc--auto drw__sheet')


def news_card(n):
    date = f'<time>{e(n["date"])}</time>' if n.get('date') else ''
    tag = f'<span class="news__tag">{e(n.get("tag", ""))}</span>' if n.get('tag') else ''
    link = f'<a class="news__more" href="{e(n["link"])}">{e(n.get("link_text") or "Подробнее")}{I("arrow-right")}</a>' if n.get('link') else ''
    img = f'<img src="{e(n["image"])}" alt="" loading="lazy">' if n.get('image') else ''
    return f'<article class="news__card rv{" is-pin" if n.get("pin") else ""}">{img}<div class="news__meta">{tag}{date}</div><h3>{e(n["title"])}</h3><p>{e(n["text"])}</p>{link}</article>'


def concept():
    """Концепция — как в прежнем варианте A: обложка, цифры плитками, бегущая строка, две группы с мини-иконками."""
    c = CONCEPT
    stats = ''.join(
        f'<div class="cst rv"><b{" data-count=" + chr(34) + re.sub(r"[^0-9]", "", n) + chr(34) if cnt else ""}>{e(n)}</b><span>{e(l)}</span></div>'
        for n, l, cnt in c['stats'])
    run = ''.join(f'<span>{e(t)}{I("sun")}</span>' for _t, _tone, items in c['groups'] for _ic, t in items)
    groups = ''
    for title, tone, items in c['groups']:
        lis = ''.join(f'<li><span class="cg__ic">{I(ic)}</span><b>{e(t)}</b></li>' for ic, t in items)
        groups += f'<article class="cg cg--{tone} rv"><h3 class="cg__t">{e(title)}</h3><ul class="cg__list">{lis}</ul></article>'
    body = f'''  <div class="wrap">
    <div class="chero rv">
      <img class="chero__ph" src="assets/img/{c['photo']}.jpg" alt="Исторический особняк школы в парке Ялты" loading="lazy">
      <div class="chero__in"><span class="chip">{I('sparkles')}{e(c['chip'])}</span><h2 class="h2" data-split>{e(c['title'])} <mark>{e(c['title_em'])}</mark></h2><p>{e(c['lead'])}</p></div>
    </div>
    <div class="cstats">{stats}</div>
  </div>
  <div class="mq" aria-hidden="true"><div class="mq__band"><div class="mq__track">{run}{run}</div></div></div>
  <div class="wrap"><div class="cgs">{groups}</div></div>'''
    return section('concept', 'morning', 'Концепция', '01', body, 'sc--stack')


def about():
    a = ABOUT
    vids = ''.join(f'<figure class="trio__v rv">{video(v, "", label)}</figure>' for v, label in a['videos'])
    body = f'''  <div class="seq seq--estate" data-seq="estate" data-frames="61" data-path="assets/seq/estate" data-ext="webp">
    <div class="seq__stage">
      <div class="wrap seq__grid">
        <div class="sh seq__txt">{li('about')}{h2(a['title'], a['title_em'])}</div>
        <div class="seq__frame"><canvas aria-hidden="true"></canvas><img class="seq__poster" src="assets/seq/estate/f_000.webp" alt="3D-макет особняка школы"></div>
      </div>
      <div class="seq__progress" aria-hidden="true"><i></i></div>
    </div>
  </div>
  <div class="wrap about__more">
    <div class="trio">{vids}</div>
    <div class="director rv">
      <span class="director__mk">{I('quote')}</span>
      <blockquote>{e(a['quote'])}</blockquote>
      <p class="director__sign">{e(a['sign'])}</p>
    </div>
  </div>'''
    return section('about', 'mist', 'О школе', '02', body, 'sc--seq')


def sun_arc(pos, moon=False):
    ico = I('moon' if moon else 'sun')
    return f'<div class="arc" data-arc="{pos}" aria-hidden="true"><svg viewBox="0 0 220 120"><path d="M10 112 A100 100 0 0 1 210 112" /></svg><span class="arc__arm"><span class="arc__sun">{ico}</span></span></div>'


def act_top(a, moon=False):
    arc = sun_arc(1 if moon else a['sun'], moon) if (moon or a.get('sun') is not None) else ''
    tm = f'<p class="act__time">{e(a["time"])}</p>' if a.get('time') else ''
    return f'<div class="act__top">{arc}{tm}</div>' if (arc or tm) else ''


def act(key, cls=''):
    a = ACTS[key]
    body = f'''  <div class="act__plate" style="background-image:url(assets/img/plates/{a['plate']}.jpg)" aria-hidden="true"></div>
  <div class="wrap act__in">
    <span class="act__num" aria-hidden="true">{a['num']}</span>
    {act_top(a)}
    <h2 class="act__name" data-split>{e(a['name'])}</h2>
  </div>'''
    pal = {'morning': 'sky', 'after': 'amber', 'evening': 'twilight'}[key]
    title = f"{a['time']} · {a['name']}" if a['time'] else a['name']
    return section(f'act-{key}', pal, title, '', body, 'act ' + cls)


def programs():
    P = PROGRAMS_INTRO
    tiles = ''
    for p in PROGRAMS:
        tiles += f'''<a class="tile rv" data-k="{p['key']}" href="#m-{p['key']}" data-open="m-{p['key']}" aria-label="{e(p['title'])}, {e(aud(p))}: подробнее о программе">
      <span class="tile__lvl">{e(p['level'])}</span>
      <span class="tile__photo"><img src="assets/img/{p['img']}.jpg" alt="" loading="lazy"></span>
      <div class="tile__txt"><h3>{e(p['title'])}</h3><p>{e(aud(p))}</p></div>
      {more()}
    </a>'''
    body = f'''  <div class="wrap">
    <div class="sh">{li('programs')}{h2(P['title'], P['title_em'])}{('<p class="lead rv">' + e(P['lead']) + '</p>') if P['lead'] else ''}</div>
    <div class="tiles">{tiles}</div>
  </div>'''
    return section('programs', 'paper', 'Программы и расписание', '03', body)


def food():
    f = FOOD
    body = f'''  <div class="wrap">
    <div class="split split--food">
      <div class="sh">{li('food')}{h2(f['title'], f['title_em'])}{ilist(f['items'], 'rv')}</div>
      <figure class="frame rv"><img src="assets/img/food.jpg" alt="Дети выбирают еду на шведском столе" loading="lazy"></figure>
    </div>
  </div>'''
    return section('food', 'warm', 'Питание', '04', body)


def teachers():
    a = ACTS['day']
    t = TEACHERS
    cards = ''.join(f'<figure class="person rv"><span class="person__ph"><img src="assets/img/{img}.jpg" alt="{e(name)}" loading="lazy"></span><figcaption><b>{e(name)}</b><span>{e(role)}</span></figcaption></figure>' for img, name, role in t['people'])
    body = f'''  <div class="wrap">
    <div class="sh">{li('teachers')}{h2(t['title'], t['title_em'])}</div>
    <div class="people">{cards}</div>
  </div>'''
    return section('teachers', 'blue', 'Педагоги', '05', body)


def safety():
    s = SAFETY
    body = f'''  <div class="wrap">
    <div class="sh">{li('safety')}{h2(s['title'], s['title_em'])}</div>
    <div class="split split--safety">
      <figure class="frame rv">{video('terr_walk', '', 'Прогулка по территории школы: башня с воротами, парковые дорожки, детская площадка')}<figcaption class="badge"><b>{e(s['area'][0])}</b>{e(s['area'][1])}</figcaption></figure>
      {ilist(s['items'], 'rv')}
    </div>
  </div>'''
    return section('safety', 'deep', 'Безопасность', '06', body)


def extra():
    x = EXTRA
    dirs = ''
    for dr in x['directions']:
        dirs += f'''<button type="button" class="dirc rv" data-album="{dr['key']}" aria-label="{e(dr['name'])}: фото и видео">
      <span class="dirc__ph"><img src="assets/img/{dr['cover']}.jpg" alt="" loading="lazy"><span class="dirc__cap"><b class="dirc__t">{e(dr['name'])}</b>{more('Фото и видео')}</span></span>
      <span class="dirc__list">{e(' · '.join(dr['list']))}</span>
    </button>'''
    guests = ''.join(f'<article class="guest rv"><span class="mi mi--lg">{I(ill)}</span><div><b>{e(n)}</b><span class="guest__what">{e(w)}</span><p>{e(c)}</p></div></article>' for n, w, ill, c in x['guests'])
    body = f'''  <div class="wrap">
    <div class="sh">{li('extra')}{h2(x['title'], x['title_em'])}<p class="lead rv">{e(x['lead'])}</p></div>
    <div class="dirs">{dirs}</div>
    <div class="meet">
      <div class="sh sh--sm"><h3 class="h2 h2--sm" data-split>{e(x['meet_title'])}</h3><p class="lead rv">{e(x['meet_lead'])}</p></div>
      <div class="guests">{guests}</div>
    </div>
  </div>'''
    return section('extra', 'afternoon', 'Авторская программа', '07', body)


def transfer():
    t = TRANSFER
    (i1, n1), (i2, n2) = t['route']
    body = f'''  <div class="wrap">
    <div class="split split--transfer">
      <div class="sh">{li('transfer')}{h2(t['title'], t['title_em'])}<p class="lead rv">{e(t['lead'])}</p>{ilist(t['items'], 'rv')}</div>
      <figure class="frame rv"><img src="assets/img/bus.jpg" alt="Микроавтобус школьного трансфера на дорожке у парка" loading="lazy"></figure>
    </div>
    <div class="route rv" data-route aria-hidden="true">
      <svg viewBox="0 0 1000 160" preserveAspectRatio="none"><path class="route__line" d="M40 120 C 220 120, 260 40, 420 50 S 640 140, 780 90 S 920 40, 960 40"/><path class="route__done" d="M40 120 C 220 120, 260 40, 420 50 S 640 140, 780 90 S 920 40, 960 40"/></svg>
      <span class="route__pt route__pt--a">{I(i1)}<b>{e(n1)}</b></span>
      <span class="route__pt route__pt--b">{I(i2)}<b>{e(n2)}</b></span>
      <span class="route__bus">{I('bus')}</span>
    </div>
  </div>'''
    return section('transfer', 'mist', 'Трансфер', '08', body)


def summer():
    s = SUMMER
    eps = ''.join(f'''<article class="ep rv"><span class="ep__ph"><img src="assets/img/{img}.jpg" alt="{e(alt)}" loading="lazy"></span>
      <div class="ep__txt"><p class="ep__k">{e(mon)}</p><h3>{e(title)}</h3><p>{text}</p></div></article>''' for n, mon, title, text, img, alt in s['episodes'])
    body = f'''  <div class="wrap">
    <div class="split split--summer">
      <div class="sh">{h2(s['title'], s['title_em'])}<p class="lead rv">{e(s['lead'])}</p></div>
      <figure class="frame frame--round rv">{video('summer_yard', '', 'Летний клуб во дворе школы: рисунки мелками и танцы')}</figure>
    </div>
    {ilist(s['facts'], 'ilist2--2 rv')}
    <div class="eps">{eps}</div>
    {more('Смотреть фото и видео лета', 'button', ' data-album="summer"', 'more--pill rv')}
  </div>'''
    return section('summer', 'sun', 'Летний клуб', '09', body)


def reviews():
    r = REVIEWS
    hi = r.get('hero', -1)
    who = lambda n, src: f'<figcaption><span class="review__ava" aria-hidden="true">{e(n[0])}</span><span><b>{e(n)}</b><small>{e(src)}</small></span></figcaption>'
    big = ''
    if 0 <= hi < len(r['items']):
        q, n, src = r['items'][hi]
        big = f'<figure class="bigq rv"><blockquote>{q}</blockquote>{who(n, src)}</figure>'
    cards = ''.join(f'<figure class="review"><blockquote>{q}</blockquote>{who(n, src)}</figure>' for i, (q, n, src) in enumerate(r['items']) if i != hi)
    stars = ''.join(I('star', 'st') for _ in range(5))
    lead = f'<p class="lead rv">{e(r["lead"])}</p>' if r.get('lead') else ''
    body = f'''  <div class="wrap">
    <div class="sh">{li('reviews')}{h2(r['title'], r['title_em'])}{lead}</div>
    {big}
    <a class="rating rv" href="{CONTACTS['map']}" target="_blank" rel="noopener"><b>{r['rating']}</b><span class="rating__st">{stars}</span><span class="rating__t">из 5 на Яндекс Картах<span class="more">Все отзывы{I('arrow-up-right')}</span></span></a>
    <div class="carousel rv">
      <div class="carousel__track hs" tabindex="0" aria-label="Отзывы родителей">{cards}</div>
      <div class="carousel__nav"><button type="button" data-dir="-1" aria-label="Предыдущий отзыв">{I('arrow-left')}</button><button type="button" data-dir="1" aria-label="Следующий отзыв">{I('arrow-right')}</button></div>
    </div>
  </div>'''
    return section('reviews', 'twilight', 'Отзывы', '10', body)


def admission():
    a = ADMISSION
    steps = ''.join(f'<li><span class="path__n">{i + 1}</span><p><b>{e(t)}</b>{e(d)}</p></li>' for i, (t, d) in enumerate(a['steps']))
    inc = ''.join(f'<li>{I("check")}{e(t)}</li>' for t in a['included'])
    lbl, head, sub = a['cost']
    body = f'''  <div class="wrap">
    <div class="sh">{li('admission')}{h2(a['title'], a['title_em'])}</div>
    <div class="adm">
      <ol class="path rv">{steps}</ol>
      <article class="price rv">
        <p class="price__lbl">{e(lbl)}</p>
        <h3 class="price__h">{e(head)}</h3>
        <p class="price__sub">{e(sub)}</p>
        <p class="price__lbl price__lbl--inc">Уже входит в стоимость</p>
        <ul class="price__inc">{inc}</ul>
        <p class="price__sale">{I('badge-percent')}<span><b>{e(a['sale'][0])}</b>{e(a['sale'][1])}</span></p>
        <a class="pill pill--blue price__go" href="#signup">Прийти на пробные дни {I('arrow-right')}</a>
      </article>
      <a class="doclink rv" href="#docs" data-open="docs">{I('file-badge')}<span><b>Лицензия и документы</b><small>госаккредитация, холдинг Mirapolis</small></span>{more()}</a>
    </div>
  </div>'''
    return section('admission', 'evening', 'Поступление', '11', body)





def plural_media(n):
    return f'{n} фото и видео'


def gallery():
    cards = ''
    for k, label in GALLERY_TABS:
        cards += f'''<button type="button" class="alb rv" data-album="{k}" aria-label="{e(label)}: фото и видео">
      <span class="alb__ph"><img src="assets/img/{GALLERY_COVERS[k]}.jpg" alt="" loading="lazy"></span>
      <span class="alb__cap"><b>{e(label)}</b>{more('Смотреть')}</span>
    </button>'''
    body = f'''  <div class="wrap">
    <div class="sh">{li('gallery')}{h2('Фото и видео', 'школы')}</div>
    <div class="albs">{cards}</div>
  </div>'''
    return section('gallery', 'evening2', 'Галерея', '', body)


def night():
    a = ACTS['night']
    body = f'''  <div class="seq seq--night" data-seq="night" data-frames="55" data-path="assets/seq/night" data-ext="webp">
    <div class="seq__stage">
      <div class="wrap seq__grid">
        <div class="seq__txt">
          <h2 class="act__name" data-split>{e(a['name'])}</h2>
        </div>
        <div class="seq__frame"><canvas aria-hidden="true"></canvas><img class="seq__poster" src="assets/seq/night/f_000.webp" alt="Особняк школы вечером, в окнах горит свет"></div>
      </div>
    </div>
  </div>'''
    return section('act-night', 'night', a['name'], '', body, 'act sc--seq')


def signup():
    s = SIGNUP
    c = CONTACTS
    body = f'''  <div class="wrap">
    <div class="split split--signup">
      <div class="sh">{li('signup')}{h2(s['title'], s['title_em'])}<p class="lead rv">{e(s['lead'])}</p></div>
      <div class="formcard rv">
        <form class="form" id="signupForm" novalidate data-endpoint="">
          <label class="field" for="f-name"><span>Имя <i>*</i></span><input id="f-name" name="name" autocomplete="name" placeholder="Как вас зовут" required><small class="field__err">Напишите имя, чтобы мы знали, к кому обращаться.</small></label>
          <label class="field" for="f-age"><span>Возраст ребёнка</span><input id="f-age" name="age" inputmode="numeric" placeholder="Например, 8"></label>
          <label class="field" for="f-phone"><span>Телефон <i>*</i></span><input id="f-phone" name="phone" type="tel" autocomplete="tel" placeholder="+7 (978) 000-00-00" required><small class="field__err">Введите номер телефона, чтобы мы могли перезвонить.</small></label>
          <button class="pill pill--blue form__go" type="submit">Записаться {I('arrow-right')}</button>
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
    return section('signup', 'night', 'Запись на пробные дни', '', body)


def footer():
    c = CONTACTS
    return f'''<footer class="foot">
      <div class="foot__brand"><img src="assets/img/wordmark-aipro.webp" width="1200" height="942" alt="Ай Про"><p>Частная школа полного дня в Ялте для детей 4–18 лет</p></div>
      <div class="foot__contacts">
        <a class="foot__phone" href="{c['phone_href']}">{e(c['phone'])}</a><span>{e(c['hours'])}</span>
        <a href="mailto:{c['email']}">{e(c['email'])}</a>
        <a href="{c['map']}" target="_blank" rel="noopener">{e(c['address'])}</a>
        <div class="socials socials--row">
          <a href="{c['wa']}" target="_blank" rel="noopener" aria-label="WhatsApp">{I('message-circle')}</a>
          <a href="{c['tg']}" target="_blank" rel="noopener" aria-label="Telegram">{I('send')}</a>
          <a href="{c['vk']}" target="_blank" rel="noopener" aria-label="ВКонтакте"><b class="sb">VK</b></a>
          <a href="{c['max']}" target="_blank" rel="noopener" aria-label="MAX"><b class="sb">M</b></a>
        </div>
      </div>
      <div class="foot__map">
        <iframe title="Ай Про на Яндекс Картах" src="about:blank" data-src="{c['map_embed']}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        <a class="foot__maplink" href="{c['map']}" target="_blank" rel="noopener">{I('map-pin')}Открыть на Яндекс Картах</a>
      </div>
      <div class="foot__bottom">
        <span>© 2026 Школа АЙПРО · IPROSCHOOL</span>
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
    return f'''<dialog class="pm" id="m-{k}" data-k="{k}" aria-labelledby="t-{k}">
  <div class="pm__bar"><span><b>{e(p['title'])}</b> · {e(p['level'])}</span><button class="xbtn" type="button" data-close aria-label="Закрыть">{I('x')}</button></div>
  <section class="pm__hero">
    <div class="pm__hero-in">
      <div><p class="pm__lvl">{e(p['level'])}</p><h2 class="pm__t" id="t-{k}">{e(p['title'])}</h2><p class="pm__aud">{e(aud(p))}</p></div>
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
    <div class="pm__cta"><span>Приходите на пробные дни</span><a class="pill pill--blue" href="#signup" data-close-go="signup">Записаться {I('arrow-right')}</a></div>
  </div>
</dialog>
'''


def docs_dialog():
    c = CONTACTS
    docs = ''.join(f'<li>{I(ic, "sq")}<span><b>{e(t)}</b>{e(s)}</span></li>' for ic, t, s in ADMISSION['docs'])
    return f'''<dialog class="sheet" id="docs" aria-labelledby="docsT">
  <div class="sheet__bar"><h2 id="docsT">Сведения об образовательной организации</h2><button class="xbtn" type="button" data-close aria-label="Закрыть">{I('x')}</button></div>
  <div class="sheet__body">
    <p class="label">Лицензия и документы</p>
    <ul class="docs__list docs__list--col">{docs}</ul>
    <p class="label">Контакты организации</p>
    <dl class="kv">
      <dt>Адрес</dt><dd>{e(c['address'])}</dd>
      <dt>Телефон</dt><dd><a href="{c['phone_href']}">{e(c['phone'])}</a></dd>
      <dt>Электронная почта</dt><dd><a href="mailto:{c['email']}">{e(c['email'])}</a></dd>
      <dt>Режим работы</dt><dd>{e(c['hours'])}</dd>
    </dl>
    <p class="label">Реквизиты и документы</p>
    <p class="ph">Полное наименование, ИНН, ОГРН, сканы лицензии и уставных документов разместим здесь по данным школы.</p>
  </div>
</dialog>
'''


def media_item(kind, src, alt):
    if kind == 'video':
        return {'k': 'v', 'full': f'assets/video/{src}.mp4', 'th': f'assets/img/posters/{src}.jpg', 'alt': alt}
    return {'k': 'i', 'full': f'assets/img/{src}.jpg', 'th': f'assets/img/{src}.jpg', 'alt': alt}


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
  <div class="helper__bar"><span class="helper__ava"><img src="assets/img/logo-aipro.webp" alt=""></span><span><b id="helperT">Помощник Ай Про</b><small>Отвечаю на вопросы о школе</small></span><button class="xbtn" type="button" data-close aria-label="Закрыть помощника">{I('x')}</button></div>
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
    main = ('<div class="drw">\n' + intro() + news() + concept() + '</div>\n' + about() + programs() + food() + teachers() + safety()
            + extra() + transfer() + summer() + reviews() + admission() + gallery() + night() + signup())
    n = len(PROGRAMS)
    dialogs = ''.join(program_dialog(p, PROGRAMS[(i - 1) % n], PROGRAMS[(i + 1) % n]) for i, p in enumerate(PROGRAMS))
    dialogs += menu_dialog() + docs_dialog() + album_dialog() + lightbox() + helper_dialog()
    head_dock = dock()
    desc = 'Ай Про (IPROSCHOOL) — частная школа полного дня в Ялте для детей 4–18 лет: детский сад и школа в историческом особняке, малые группы до 14 человек, языки с носителями, кружки, питание и трансфер. Три пробных дня бесплатно.'
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Ай Про · частная школа полного дня в Ялте</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0B2140">
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700;800;900&display=swap">
<link rel="stylesheet" href="assets/css/site.css?v={asset_v('assets/css/site.css')}">
<script>document.documentElement.classList.add('js');try{{if(localStorage.getItem('ipro-a11y')==='1')document.documentElement.classList.add('a11y')}}catch(e){{}}</script>
</head>
<body>
{{SPRITE}}
<a class="skip" href="#concept">К содержанию</a>
{head_dock}<main id="main">
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
