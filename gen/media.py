"""Готовит фото, постеры, видео и покадровые сцены для полного сайта IPROSCHOOL."""
import os, shutil, subprocess, sys
from PIL import Image

SRC = '/home/claude/src/site/assets'
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

def jpg(src, dst, maxside=1600, q=80):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src).convert('RGB')
    im.thumbnail((maxside, maxside))
    im.save(dst, quality=q, optimize=True, progressive=True)
    return im.size

# фото из архива сайта (имя на сайте: файл в архиве)
photos = {
  'facade': 'img/real/terr02.jpg',
  'portico': 'img/real/poster_hero_live.jpg',
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
  'maquette-evening': 'img/real/maquette_evening.jpg', 'maquette-day': 'img/real/estate_day_poster.jpg',
}
for k, f in photos.items():
    jpg(os.path.join(SRC, f), f'{OUT}/img/{k}.jpg')
for k in ['dawn', 'morning', 'day', 'after', 'evening']:
    jpg(os.path.join(SRC, f'img/plates/{k}_soft.jpg'), f'{OUT}/img/plates/{k}.jpg', 960, 78)
for f in os.listdir(os.path.join(SRC, 'img/posters')):
    jpg(os.path.join(SRC, 'img/posters', f), f'{OUT}/img/posters/{f}', 1280, 76)
jpg(os.path.join(SRC, 'img/real/poster_hero_school.jpg'), f'{OUT}/img/posters/hero_school.jpg', 1280, 76)
jpg(os.path.join(SRC, 'img/real/poster_hero_live.jpg'), f'{OUT}/img/posters/hero_live.jpg', 1280, 76)
for f in ['logo-aipro.webp', 'wordmark-aipro.webp']:
    shutil.copy(os.path.join(SRC, 'img', f), f'{OUT}/img/{f}')
for f in ['favicon.svg', 'apple-touch-icon.png', 'og.jpg']:
    shutil.copy(os.path.join(SRC, '..', f), f'{OUT}/{f}')

# видео: готовые веб-версии с сайта; длинный ролик летнего клуба пережимаем в 720p
os.makedirs(f'{OUT}/video', exist_ok=True)
for v in ['hero_school', 'terr_overview', 'clubs_dance', 'hero_live', 'terr_walk', 'club_wood', 'summer_yard',
          'lessons', 'gal_craft_birdhouse', 'gal_club_judo', 'club_sand', 'gal_event_lastbell']:
    shutil.copy(os.path.join(SRC, 'video', v + '.mp4'), f'{OUT}/video/{v}.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(SRC, 'video/summer_club.mp4'), '-an', '-vf', 'scale=1280:-2',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '29', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'{OUT}/video/summer_club.mp4'], check=True)

# покадровые сцены 3D-макета: днём (подлёт к входу) и ночью (отъезд камеры)
for seq in ['estate', 'night']:
    shutil.copytree(os.path.join(SRC, 'seq', seq), f'{OUT}/seq/{seq}', dirs_exist_ok=True)
print('ok')
