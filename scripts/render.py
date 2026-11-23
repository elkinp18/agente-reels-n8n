import os
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
OUT = ROOT / 'reel.mp4'
DURATION = 10
FPS = 30


def run(args):
    subprocess.run(args, check=True, cwd=ROOT)

frases = [os.environ.get(f'FRASE{i}', '').strip() for i in range(1, 4)]
for i, frase in enumerate(frases, 1):
    if not frase:
        raise SystemExit(f'Falta la frase {i}')
    if len(frase) > 140:
        raise SystemExit(f'La frase {i} es muy larga: maximo 140 caracteres')
    if not (ASSETS / f'escena{i}.png').is_file():
        raise SystemExit(f'Falta assets/escena{i}.png')
if not (ASSETS / 'musica.mp3').is_file():
    raise SystemExit('Falta assets/musica.mp3')

clips = []
for i, frase in enumerate(frases, 1):
    image = ASSETS / f'escena{i}.png'
    text = ROOT / f'frase{i}.txt'
    text.write_text('\n'.join(textwrap.wrap(frase, 23, break_long_words=False)), encoding='utf-8')
    clip = ROOT / f'escena{i}.mp4'
    # Fotos verticales u horizontales: recorte central, zoom suave, fondo oscuro y texto.
    vf = (
        'scale=900:1600:force_original_aspect_ratio=increase,'
        'crop=900:1600,'
        "zoompan=z='min(zoom+0.00028,1.10)':"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        'd=1:s=720x1280:fps=30,'
        'format=yuv420p,'
        'drawbox=x=0:y=0:w=iw:h=ih:color=black@0.38:t=fill,'
        f'drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile={text.name}:'
        'fontcolor=white:fontsize=44:line_spacing=16:'
        'x=(w-text_w)/2:y=(h-text_h)/2:'
        'box=1:boxcolor=black@0.36:boxborderw=26,'
        'fade=t=in:st=0:d=0.7,'
        'fade=t=out:st=9.3:d=0.7'
    )
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
         '-loop', '1', '-framerate', str(FPS), '-i', str(image),
         '-vf', vf, '-t', str(DURATION), '-an',
         '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
         '-pix_fmt', 'yuv420p', str(clip)])
    clips.append(clip)

listfile = ROOT / 'clips.txt'
listfile.write_text(''.join(f"file '{p.name}'\n" for p in clips), encoding='utf-8')
run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
     '-f', 'concat', '-safe', '0', '-i', str(listfile),
     '-stream_loop', '-1', '-i', str(ASSETS / 'musica.mp3'),
     '-map', '0:v:0', '-map', '1:a:0',
     '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
     '-af', 'volume=0.20,afade=t=in:st=0:d=1,afade=t=out:st=28:d=2',
     '-t', '30', '-movflags', '+faststart', str(OUT)])
print(f'Video creado: {OUT}')
