"""Draw the six editorial plates from a public voice sample and an anonymous edit log."""
from pathlib import Path
import argparse
import json
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1200, 800
INK = '#202228'
PAPER = '#e6ddcb'
LIGHT = '#e8efff'
BLUE = '#a2baff'
ORANGE = '#f36431'
MONO = ['/System/Library/Fonts/Menlo.ttc','DejaVuSansMono.ttf']
SANS = ['/System/Library/Fonts/HelveticaNeue.ttc','DejaVuSans.ttf']
def font(size, mono=False):
    for path in MONO if mono else SANS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    raise RuntimeError('Install DejaVu Sans and DejaVu Sans Mono')

def label(d, xy, value, size=24, color=INK, mono=True):
    d.text(xy, value, font=font(size, mono), fill=color, anchor='lt')

def marks(d, color):
    for x in (42,W-42):
        for y in (40,H-40):
            d.line((x-8,y,x+8,y),fill=color,width=2)
            d.line((x,y-8,x,y+8),fill=color,width=2)

def voice(demo, segments):
    with wave.open(str(demo)) as f:
        samples = np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)
        signal = samples.reshape(-1,f.getnchannels()).mean(axis=1)
        rate = f.getframerate()
    spectrum = np.abs(np.fft.rfft(np.lib.stride_tricks.sliding_window_view(signal,1024)[::128]*np.hanning(1024)))
    levels = 20*np.log10(1+spectrum)
    bins = np.geomspace(1, min(180,levels.shape[1]-1), 346).astype(int)[::-1]
    heat = np.clip((levels[:,bins].T-36)/77,0,1)
    palette=np.array([[17,21,37],[38,49,81],[78,98,157],[143,171,241],[220,228,245],[248,169,124]])
    rgb=np.stack([np.interp(heat,np.linspace(0,1,len(palette)),col) for col in palette.T],axis=-1)
    chart=Image.fromarray(rgb.astype('uint8')).resize((1064,422))
    for i in range(3):
        im=Image.new('RGB',(W,H),'#131725'); d=ImageDraw.Draw(im)
        marks(d,BLUE)
        label(d,(67,46),'DIALOGUE  /  JP',23,BLUE)
        if i==0:
            label(d,(66,108),'Voiceprint',108,LIGHT,False)
            im.paste(chart,(68,260))
            for j,t in enumerate(('0.00','0.32','0.65','0.97','1.30 s')):
                label(d,(68+j*247,706),t,20,BLUE)
        elif i==1:
            label(d,(66,120),'Listen again',93,LIGHT,False)
            for row, y in enumerate([360, 555]):
                # Display the same mono excerpt at two scales to illustrate close listening.
                label(d,(69,y-14),('1x','4x')[row],24,BLUE)
                sig=signal if row==0 else signal[len(signal)//4:len(signal)//2]
                for x,part in enumerate(np.array_split(sig,930)):
                    amp=max(1,int(np.max(np.abs(part))/max(abs(signal))*88))
                    d.line((164+x,y-amp,164+x,y+amp),fill=LIGHT if row else BLUE)
            label(d,(68,704),'FULL WORD   /   DETAIL',22,BLUE)
        else:
            label(d,(68,126),'Subtitle cue',93,LIGHT,False)
            im.paste(chart.resize((1064,200)),(68,269))
            seg=segments[0]; total=len(signal)/rate
            x0,x1=[68+int(t/total*1064) for t in (seg['start'],seg['end'])]
            d.rectangle((x0,485,x1,534),fill=BLUE)
            for x,t in [(x0,seg['start']),(x1,seg['end'])]:
                d.line((x,255,x,554),fill='#ffd5bb',width=3);label(d,(x-42,575),f'{t:.3f}',28,LIGHT)
            label(d,(68,704),'IN  /  OUT     SECONDS',22,BLUE)
        yield im

def cube(draw, x, y, size, height, colors):
    a=(x,y-size//2); b=(x+size,y); c=(x,y+size//2); d=(x-size,y)
    def low(p):return (p[0],p[1]+height)
    for poly,col in [([d,c,low(c),low(d)],colors[1]),([b,c,low(c),low(b)],colors[2]),([a,b,c,d],colors[0])]:
        draw.polygon(poly,fill=col,outline=INK,width=2)

def edits(events):
    for i in range(3):
        im=Image.new('RGB',(W,H),PAPER); d=ImageDraw.Draw(im);marks(d,INK)
        label(d,(68,48),'PICTURE  /  DIALOGUE',23)
        if i==0:
            label(d,(64,112),'On cue',116,INK,False)
            for j in range(9):
                x=142+112*j;y=566-29*j
                cube(d,x,y,68,29,['#b2afa8','#777c82','#90959c'])
                if j in (2,4,6,8):
                    cube(d,x,y-48,40,43,['#ff9c70',ORANGE,'#b13e23'])
            label(d,(68,705),'ACTION',24);label(d,(827,705),'47.70 s',32)
        elif i==1:
            label(d,(66,110),'Reaction timing',91,INK,False)
            for j,(t,topic) in enumerate(events):
                y=288+j*138
                d.line((70,y+79,1130,y+79),fill='#a69f91',width=2)
                label(d,(70,y),t,55);label(d,(425,y+12),topic,34)
                d.ellipse((1070,y+10,1106,y+46),fill=ORANGE if j==2 else INK)
            label(d,(68,705),'EDIT LOG   /   SECONDS',22)
        else:
            label(d,(66,110),'Sync check',99,INK,False)
            for j,(name,ms) in enumerate([('VOICE',88),('END CARD',44)]):
                y=330+j*174; label(d,(68,y),name,28)
                d.line((420,y+20,1040,y+20),fill=INK,width=2)
                for k in range(10):
                    x=420+k*60; d.line((x,y+12,x,y+28),fill=INK,width=2)
                x=420+ms*6;d.ellipse((x-12,y+8,x+12,y+32),fill=ORANGE)
                label(d,(x-45,y+51),f'+{ms} ms',24)
            label(d,(68,705),'FIRST EXPORT   /   AUDIO DELAY',22)
        yield im

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path); out=parser.parse_args().output
    out.mkdir(exist_ok=True,parents=True)
    speech=ROOT/'examples/speech'
    events=json.loads((ROOT/'examples/edit/events.json').read_text())
    for prefix,plates in [('speech',voice(speech/'thanks.wav',json.loads((speech/'thanks.json').read_text())['segments'])),('edit',edits(events))]:
        for i,im in enumerate(plates,1):im.save(out/f'{prefix}-{i}.webp',quality=88,method=6)
