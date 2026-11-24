"""Render the public cover and two short motion studies. Requires Pillow and FFmpeg."""
import argparse
import json
import subprocess
import tempfile
import wave
from array import array
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
W, H, FPS = 960, 540, 24
SHOT = 6
INK, PAPER, BLUE, ORANGE, MUTED = '#171d28', '#f2eddf', '#a6bfff', '#ff925b', '#a4aea9'
SAMPLE = ROOT / 'examples/speech/thanks.wav'
REVIEW = ROOT / 'examples/speech/review'


@lru_cache
def font(size):
    for path in (FONT, '/System/Library/Fonts/Hiragino Sans GB.ttc', 'NotoSansCJK-Regular.ttc'):
        if path:
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                pass
    raise RuntimeError('Supply a Chinese and Japanese font with --font')


def text(d, x, y, s, size, color=PAPER):
    d.text((round(x), round(y)), s, font=font(size), fill=color, anchor='lt')


def ease(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def wave_peaks():
    with wave.open(str(SAMPLE)) as f:
        assert f.getsampwidth() == 2
        pcm = array('h', f.readframes(f.getnframes()))[::f.getnchannels()]
    n = 146
    values = [max(abs(x) for x in pcm[i*len(pcm)//n:(i+1)*len(pcm)//n]) for i in range(n)]
    return [v / max(values) for v in values]


def wave_plot(d, peaks, x, y, width, height, progress):
    for i, value in enumerate(peaks):
        a = x + i * width / len(peaks)
        h = max(2, value * height)
        d.line((a, y-h, a, y+h), BLUE if i/len(peaks) <= progress else '#697384', width=3)


def tile(d, x, y, size, depth, color):
    top = [(x-size,y), (x,y-size*.45), (x+size,y), (x,y+size*.45)]
    for a,b,shade in [(top[0],top[3],'#bc613d'),(top[3],top[2],'#793f32')]:
        d.polygon([a,b,(b[0],b[1]+depth),(a[0],a[1]+depth)],fill=shade)
    d.polygon(top, fill=color)


def cover(peaks):
    im = Image.new('RGB', (W,H), INK)
    d = ImageDraw.Draw(im)
    text(d,44,35,'EDIT  &  CODEX',24,BLUE)
    text(d,42,112,'对白与剪辑',91)
    text(d,49,242,'十集收音到审片字幕   /   游戏广告剪辑与补声',29)
    wave_plot(d, peaks,50,396,515,72,1)
    d.line((535,396,598,396,694,300,916,300),fill=BLUE,width=3)
    for j in range(3):
        tile(d,662+j*84,367-j*43,49,25,ORANGE)
    d.line((48,497,910,497),fill='#525d6e',width=1)
    return im


EDIT_TITLES = ['同一条评论，什么时候看全？','等到出料，再说「做到了」','现有录音少了一句','只改开头，后面保留','同一句，换种念法','把导出的声音对回画面']
EDIT_CAPTIONS = ['截自同一支广告的两次导出。上面逐句换，下面一次读完。','42.83 秒还推不进。到 47.70 秒，成品才出来。','用获准的参考录音补一句日语。我先听同一个人怎么说话。','开头想再平一点。两条线取自实际试听文件的音高。','我喜欢 Qwen 的音色，也想保留 v5 的说话节奏。','回到剪辑案例，分轨修正后复测 40 个起音。']


@lru_cache(maxsize=1)
def comment_frames():
    with Image.open(ROOT / 'examples/edit/comment-revision.gif') as animation:
        return [frame.convert('RGB') for frame in ImageSequence.Iterator(animation)]


def edit_frame(sec, pitch_data):
    part = min(len(EDIT_TITLES)-1, int(sec / SHOT))
    u = sec - part * SHOT
    bg, fg, accent = PAPER, INK, '#b54520'
    im = Image.new('RGB', (W,H), bg)
    d = ImageDraw.Draw(im)
    text(d,42,32,'游戏广告剪辑'+'   /   '+('0%d' % (part+1)),22,accent)
    text(d,42,83,EDIT_TITLES[part],49,fg)
    if part == 0:
        samples = comment_frames()
        im.paste(samples[min(int(u * 10), len(samples) - 1)], (72,161))
    elif part == 1:
        p=ease((u-.9)/2.4)
        d.line((95,339,813,339),fill=fg,width=5)
        for j in range(20):
            x=97+j*35
            d.line((x,341,x-10,358),fill='#bcb5a6',width=3)
        tile(d,197+477*p,295,51,24,ORANGE)
        text(d,67,177,'42.83 s',28,fg)
        text(d,639,177,'47.70 s',28,fg)
        if p>=.99:
            text(d,607,218,'できた！',44,accent)
        text(d,69,392,'按剪点记录重绘',19,fg)
    elif part == 2:
        text(d,47,171,'GPT-SoVITS v5 Turbo   /   同一句追加口播',24,fg)
        for i,(name,seconds) in enumerate([('用片头语气',7.44),('换片尾直视镜头的语气',8.48)]):
            y=242+i*87
            text(d,47,y,name,26,fg)
            d.line((390,y+14,390+45*seconds*ease((u-i*.85)/1.5),y+14),fill=accent,width=10)
            text(d,797,y,'%.2f s' % seconds,25,fg)
        text(d,48,397,'台词和语速设置保持一致，只更换参考录音。',23,fg)
    elif part == 3:
        for i,(key,name) in enumerate([('before','调整前'),('after','调整后')]):
            y=231+i*95
            text(d,45,y-15,name,26,fg)
            d.line((194,y,887,y),fill='#b5ada0')
            points=pitch_data[key]
            last=None
            for j,v in enumerate(points):
                x=201+j*19
                if v is None or j/(len(points)-1)>min(1,u/2.16):
                    last=None
                    continue
                point=(x,y-v*4.1)
                if last: d.line([last,point],fill=accent if i else fg,width=4)
                last=point
        text(d,48,397,'只动开头 2.16 秒，后面的声音逐采样相同。',23,fg)
    elif part == 4:
        for i,(name,seconds) in enumerate([('旧 Qwen',2.50),('v5 语气示范',1.88),('新版 Qwen',1.94)]):
            y=192+70*i
            text(d,47,y,name,26,fg)
            x=295+175*seconds*ease((u-.35*i)/1.7)
            d.line((295,y+15,x,y+15),fill=accent if i==2 else '#6f766e',width=7)
            text(d,788,y,'%.2f s' % seconds,25,fg)
        text(d,47,400,'从开口到第一次明显停顿',23,fg)
    else:
        p=ease((u-1.5)/2.2)
        for i,(name,ms) in enumerate([('主对白',88),('尾卡',44)]):
            y=236+i*99
            text(d,44,y-14,name,27,fg)
            d.line((250,y,860,y),fill='#b3afa3',width=3)
            d.line((300,y-25,300,y+25),fill=fg,width=3)
            x=300+(1-p)*ms*5
            d.ellipse((x-10,y-10,x+10,y+10),fill=accent)
            text(d,750,y+12,('+' if p<1 else '')+str(round(ms*(1-p)))+' ms',24,fg)
        text(d,47,400,'复测范围   36 处对白  +  4 处尾卡',22,accent)
    d.line((42,452,918,452),fill='#747c82',width=1)
    text(d,44,476,EDIT_CAPTIONS[part],24,fg)
    return im


def render_edit(out, pitch_data):
    silent=out/'edit.mp4'
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','960x540','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(silent)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(SHOT*len(EDIT_TITLES)*FPS):
            im=edit_frame(i/FPS,pitch_data)
            if i==int(2.8*FPS):
                im.save(out/'edit.webp',quality=90)
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
        result=proc.wait()
    if result:
        raise RuntimeError('FFmpeg encoding failed')


def render_dialogue(out, tmp, stem, final_label):
    # The two portrait frames already share an aligned 540 × 480 canvas.
    headers = []
    for active in range(2):
        header = Image.new('RGB', (540, 48), INK)
        draw = ImageDraw.Draw(header)
        for index, label in enumerate(('ACOPY', final_label)):
            center = 135 + 270 * index
            draw.text((center, 24), label, font=font(22), anchor='mm',
                      fill=PAPER if active == index else MUTED)
            if active == index:
                right = center - draw.textlength(label, font=font(22)) / 2 - 9
                x = round(right) - 17
                draw.polygon([(x,21),(x+4,21),(x+9,16),(x+9,32),(x+4,27),(x,27)], fill=BLUE)
                draw.arc((x+2,17,x+16,31), -48, 48, fill=BLUE, width=2)
        path = tmp / f'{stem}-{active}.png'
        header.save(path)
        headers.append(path)

    # Play the same 4.8-second passage twice. Pad to five seconds so
    # the cut, the active speaker and the web chapter change together.
    layout = (
        '[0:v]fps=24,tpad=stop_mode=clone:stop_duration=1,trim=end_frame=120,'
        'loop=loop=1:size=120:start=0,setpts=N/(24*TB),pad=540:528:0:48[v];'
        '[v][2:v]overlay=0:0[first];'
        "[first][3:v]overlay=0:0:enable='gte(t,5)'[video];"
        '[0:a]aresample=48000,atrim=end=4.8,apad,atrim=end=5,asetpts=PTS-STARTPTS[raw];'
        '[1:a]aresample=48000,atrim=end=4.8,apad,atrim=end=5,asetpts=PTS-STARTPTS[final];'
        '[raw][final]concat=n=2:v=0:a=1[audio]'
    )
    movie = out / f'{stem}.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(REVIEW/'comparison.mp4'),
                    '-i',str(REVIEW/'scene.mp4'),'-i',str(headers[0]),'-i',str(headers[1]),
                    '-filter_complex',layout,'-map','[video]','-map','[audio]','-t','10',
                    '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac',
                    '-b:a','160k','-movflags','+faststart',str(movie)],check=True)
    still = tmp / f'{stem}-poster.png'
    subprocess.run(['ffmpeg','-v','error','-y','-ss','1','-i',str(movie),
                    '-frames:v','1',str(still)],check=True)
    with Image.open(still) as poster:
        poster.save(out / f'{stem}.webp', quality=90)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--font',help='Path to a Chinese/Japanese TrueType or OpenType font')
    args=parser.parse_args()
    FONT=args.font
    args.output.mkdir(parents=True,exist_ok=True)
    peaks=wave_peaks()
    cover(peaks).save(args.output/'cover.webp',quality=93)
    pitch_data=json.loads((ROOT/'examples/edit/intonation.json').read_text())
    with tempfile.TemporaryDirectory() as tmp:
        render_dialogue(args.output, Path(tmp), 'dialogue', '成片')
        render_dialogue(args.output, Path(tmp), 'dialogue-ja', '完成版')
    render_edit(args.output, pitch_data)
