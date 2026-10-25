"""Готовит фото, постеры, видео и кадры 3D-макета для сайта Ай Про, версия A.

Видео пережимаются в H.264 (CRF 28, не больше 1280 px по длинной стороне, без звука, faststart):
главное видео первого экрана — короткий фрагмент обзора школы, 1,5–3 МБ.
Запуск: python3 gen/media.py <папка assets сайта> [photos|video|all]"""
import os, shutil, subprocess, sys
from PIL import Image, ImageEnhance

SRC = '/home/claude/src/site/assets'
TOUR_SRC = '/home/claude/video/tour_hd.mp4'  # обзор школы 1080p (85 с) — для первого экрана берём 30 с
SUMMER_CLUB_SRC = '/home/claude/video/summer_club_70.mp4'  # летний клуб, 70 с (как было на сайте)
# видео в блоках и альбомах
VIDEOS = ['terr_overview', 'clubs_dance', 'hero_live', 'terr_walk', 'club_wood', 'summer_yard', 'lessons',
          'gal_craft_birdhouse', 'gal_club_judo', 'club_sand', 'gal_event_lastbell', 'moment', 'summer_club']
OUT = sys.argv[1]
WHAT = sys.argv[2] if len(sys.argv) > 2 else 'all'
os.makedirs(OUT, exist_ok=True)


def jpg(src, dst, maxside=1600, q=80, fix=None, sm=False):
    """JPEG для сайта; sm=True — ещё и уменьшенная копия *-sm.jpg (640 px) для телефонов и превью."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src).convert('RGB')
    im.thumbnail((maxside, maxside))
    if fix:
        im = fix(im)
    im.save(dst, quality=q, optimize=True, progressive=True)
    if sm:
        small = im.copy()
        small.thumbnail((640, 640), Image.LANCZOS)
        small.save(dst[:-4] + '-sm.jpg', quality=76, optimize=True, progressive=True)
    return im.size


def brighter(im):
    """Трансфер: исходный кадр тёмный — чуть светлее и теплее, без смены сюжета."""
    im = ImageEnhance.Brightness(im).enhance(1.22)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    return ImageEnhance.Color(im).enhance(1.08)


# фото из архива сайта (имя на сайте: файл в архиве)
photos = {
    'facade': 'img/real/terr01.jpg',  # фасад без многоэтажки за особняком
    'food': 'img/real/food_hd.jpg',
    'ped-argat': 'img/real/ped_Argat.jpg', 'ped-veselova': 'img/real/ped_Veselova.jpg',
    'ped-gordienko': 'img/real/ped_Gordienko.jpg', 'ped-melnikova': 'img/real/ped_Melnikova.jpg',
    'bus': 'img/real/chat_bus.jpg',
    'hiphop': 'img/real/chat_hiphop_team.jpg', 'judo': 'img/real/chat_judo_throw.jpg', 'court': 'img/real/sport_court.jpg',
    'chess-lesson': 'img/real/chat_chess_lesson.jpg', 'guitar': 'img/real/chat_guitar.jpg', 'theatre': 'img/real/chat_theatre_queen.jpg',
    'craft-room': 'img/real/chat_craft_room.jpg',
    'zoo': 'img/real/gal_summer_zoo.jpg', 'foam': 'img/real/g11.jpg', 'hike': 'img/real/gal_summer_hike.jpg', 'herbs': 'img/real/gal_summer_herbs.jpg',
    'flags': 'img/real/chat_summer_flags.jpg', 'pool': 'img/real/chat_terr_pool.jpg',
    'paint': 'img/real/c05.jpg', 'drawings': 'img/real/g09.jpg', 'chess-club': 'img/real/gal_club_chess.jpg', 'piano': 'img/real/club_piano.jpg',
    'recording': 'img/real/chat_recording.jpg', 'hiphop-yard': 'img/real/gal_club_hiphop.jpg', 'grotto': 'img/real/chat_terr_grotto.jpg',
    'fountain': 'img/real/gal_terr_fountain.jpg', 'stairs': 'img/real/chat_terr_stairs.jpg', 'playground': 'img/real/gal_terr_playground.jpg',
    'dance-yard': 'img/real/g16.jpg', 'september': 'img/real/gal_event_september.jpg', 'choir': 'img/real/mus01.jpg', 'round-dance': 'img/real/c02.jpg',
    'lineup': 'img/real/gal_event_lineup.jpg', 'award': 'img/real/evt01.jpg', 'costumes': 'img/real/gal_event_costumes.jpg',
    'k_main': 'img/posters/club_sand.jpg', 'p_main': 'img/real/lesson_desks.jpg', 'm_main': 'img/real/c06.jpg', 's_main': 'img/real/gal_club_chess.jpg',
}


def wordmarks():
    """Знак «Ай про» без щита: светлый — поверх видео и в подвале, тёмно-синий — для светлой шапки."""
    wm = Image.open(os.path.join(SRC, 'img/wordmark-aipro.webp')).convert('RGBA')
    wm.thumbnail((480, 480), Image.LANCZOS)
    wm.save(f'{OUT}/img/wordmark-aipro.webp', quality=92, method=6)
    px = wm.load()
    navy = (10, 44, 85)
    for y in range(wm.height):
        for x in range(wm.width):
            r, g, b, a = px[x, y]
            if a and min(r, g, b) > 150 and max(r, g, b) - min(r, g, b) < 60:  # белые буквы → синие, жёлтое солнце остаётся
                px[x, y] = navy + (a,)
    wm.save(f'{OUT}/img/wordmark-aipro-navy.webp', quality=92, method=6)


def do_photos():
    for k, f in photos.items():
        jpg(os.path.join(SRC, f), f'{OUT}/img/{k}.jpg', fix=brighter if k == 'bus' else None, sm=True)
    # постеры видео (moment — из самого видео, см. do_video)
    for v in VIDEOS:
        f = os.path.join(SRC, 'img/posters', v + '.jpg')
        if os.path.exists(f):
            jpg(f, f'{OUT}/img/posters/{v}.jpg', 1280, 76, sm=True)
    jpg(os.path.join(SRC, 'img/real/poster_hero_school.jpg'), f'{OUT}/img/posters/hero_school.jpg', 1280, 76)
    jpg(os.path.join(SRC, 'img/real/poster_hero_live.jpg'), f'{OUT}/img/posters/hero_live.jpg', 1280, 76, sm=True)
    wordmarks()
    # конец дня: ночной особняк — фон подвала
    jpg(os.path.join(SRC, 'seq/night/f_034.webp'), f'{OUT}/img/night.jpg', 1108, 80)
    # пролёт камеры днём: кадры 0–40 (дальше камера подходит слишком близко и картинка мылится)
    os.makedirs(f'{OUT}/seq/estate', exist_ok=True)
    for i in range(41):
        shutil.copy(os.path.join(SRC, f'seq/estate/f_{i:03d}.webp'), f'{OUT}/seq/estate/f_{i:03d}.webp')
    for f in ['favicon.svg', 'apple-touch-icon.png', 'og.jpg']:
        shutil.copy(os.path.join(SRC, '..', f), f'{OUT}/{f}')


def enc(src, dst, crf=28, extra_in=(), vf='', maxrate=None):
    scale = "scale='if(gt(iw,ih),min(1280,iw),-2)':'if(gt(iw,ih),-2,min(1280,ih))'"
    vf = scale + (',' + vf if vf else '')
    cmd = ['ffmpeg', '-v', 'error', '-y', *extra_in, '-i', src, '-an', '-vf', vf,
           '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-profile:v', 'high', '-pix_fmt', 'yuv420p']
    if maxrate:
        cmd += ['-maxrate', maxrate, '-bufsize', str(int(maxrate[:-1]) * 2) + 'k']
    cmd += ['-movflags', '+faststart', dst]
    subprocess.run(cmd, check=True)


def poster(video, dst, t=0.4, sm=False):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', video, '-frames:v', '1', '-q:v', '4', dst + '.tmp.jpg'], check=True)
    jpg(dst + '.tmp.jpg', dst, 1280, 76, sm=sm)
    os.remove(dst + '.tmp.jpg')


def do_video():
    os.makedirs(f'{OUT}/video', exist_ok=True)
    # первый экран, компьютер: 30 с обзора (классы, занятия, дзюдо, фортепиано, столовая) — около 2,5 МБ
    enc(TOUR_SRC, f'{OUT}/video/tour.mp4', crf=29, extra_in=('-ss', '42', '-t', '30'), maxrate='700k')
    poster(f'{OUT}/video/tour.mp4', f'{OUT}/video/tour_poster.jpg', 0.1)
    # первый экран, телефон: вертикальное видео — около 2,5 МБ
    enc(os.path.join(SRC, 'video/hero_school.mp4'), f'{OUT}/video/hero_school.mp4', crf=29, maxrate='800k')
    # видео в блоках и альбомах: 720p, не больше ~1 Мбит/с (исходники уже сжаты — без потолка CRF раздувает файл)
    for v in VIDEOS:
        if v in ('summer_club',):
            continue
        cut = ('-t', '24') if v == 'terr_walk' else ()  # прогулка по территории: первые 24 с (ворота, парк, фонтан, грот)
        enc(os.path.join(SRC, 'video', v + '.mp4'), f'{OUT}/video/{v}.mp4', crf=28, extra_in=cut, maxrate='1000k')
    # летний клуб в альбоме: прежняя 70-секундная версия, 540p
    enc(SUMMER_CLUB_SRC, f'{OUT}/video/summer_club.mp4', crf=30, vf='scale=-2:540', maxrate='600k')
    poster(f'{OUT}/video/moment.mp4', f'{OUT}/img/posters/moment.jpg', 1.0, sm=True)


if WHAT in ('photos', 'all'):
    do_photos()
if WHAT in ('video', 'all'):
    do_video()
print('ok', WHAT)
