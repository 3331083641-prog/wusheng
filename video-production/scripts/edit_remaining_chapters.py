"""Edit actual Playwright recordings; EDL preserves their provenance."""
from pathlib import Path
import json, subprocess, shutil, hashlib
ROOT=Path(__file__).resolve().parents[1]
FF=Path('D:/Python code/.venv/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe')
OUT=ROOT/'remotion/public/media';OUT.mkdir(parents=True,exist_ok=True)
def report(stage):return json.loads((ROOT/f'reports/capture-{stage}-raw.json').read_text(encoding='utf-8'))
# Each segment is a real capture and its source start/end seconds.
plans={
 'ch05':(35,[('consumable-create',3.2,7.8),('consumable-create',9.8,14.6),('consumables',2.3,16.7),('consumables',18.8,23.2),('consumables',27.8,33.8),('consumables',35.0,39.4)]),
 'ch06-evidence':(28,[('evidence',2.25,32.23)]),
 'ch06-qwen':(36,[('qwen',2.2,33.84)]),
 'ch07':(25,[('share',2.4,20.3)]),
 'ch07-mobile':(12,[('mobile',1.8,15.8)]),
 'ch08':(23,[('repairs',2.2,15.2),('repairs',15.5,19.5),('github',8.0,14.0)]),
 'ch09':(14,[('close',2.3,16.3)]),
}
focus={};edl=[]
for clip,(target,segments) in plans.items():
 inputs=list(dict.fromkeys(report(s)['video'] for s,_,_ in segments))
 def source_duration(stage):
  probe='D:/Codex/temp/day200-tools/ffmpeg-9.0.2-essentials_build/bin/ffprobe.exe'
  return float(subprocess.check_output([probe,'-v','error','-show_entries','format=duration','-of','csv=p=0',report(stage)['video']],text=True).strip())
 segments=[(s,a,min(b,source_duration(s)-0.04)) for s,a,b in segments]
 duration=sum(b-a for _,a,b in segments);ratio=target/duration
 args=[str(FF),'-hide_banner','-loglevel','error','-y']
 for p in inputs:args+=['-i',p]
 filters=[];points=[];cursor=0
 for index,(stage,a,b) in enumerate(segments):
  r=report(stage);source=inputs.index(r['video']);filters.append(f'[{source}:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{index}]')
  for m in r.get('marks',[]):
   if a<=m['time']<b and 'x' in m:points.append({'timeMs':round((cursor+m['time']-a)*ratio*1000),'x':m['x'],'y':m['y'],'kind':'click'})
  cursor+=b-a
 filters.append(''.join(f'[v{i}]' for i in range(len(segments)))+f'concat=n={len(segments)}:v=1:a=0,setpts={ratio}*PTS,fps=30,settb=expr=1/15360,setpts=N/(30*TB),tpad=stop_mode=clone:stop_duration=0.2,trim=duration={target},format=yuv420p[out]')
 output=OUT/f'{clip}.mp4'
 args+=['-filter_complex',';'.join(filters),'-map','[out]','-an','-frames:v',str(target*30),'-c:v','h264_nvenc','-preset','p4','-b:v','5M','-maxrate','7M','-bufsize','10M','-movflags','+faststart',str(output)]
 subprocess.run(args,check=True)
 focus[clip]=points;edl.append({'clip':clip,'seconds':target,'playbackTimeScale':ratio,'segments':segments,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
 print(clip,target,'seconds',round(output.stat().st_size/1e6,2),'MB',flush=True)
focusfile=OUT/'focus.json';existing=json.loads(focusfile.read_text()) if focusfile.exists() else {};existing.setdefault('clips',{}).update(focus);focusfile.write_text(json.dumps(existing,indent=2),encoding='utf-8')
(ROOT/'reports/remaining-chapters-edit.json').write_text(json.dumps(edl,indent=2),encoding='utf-8')
for dest in ['audio','subtitles']:(ROOT/f'remotion/public/{dest}').mkdir(exist_ok=True)
shutil.copyfile(ROOT/'audio/narration-music.wav',ROOT/'remotion/public/audio/narration-music.wav')
shutil.copyfile(ROOT/'subtitles/captions.json',ROOT/'remotion/public/subtitles/captions.json')
