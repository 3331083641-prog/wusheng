import React from 'react';
import {AbsoluteFill, CanvasImage, interpolate, useCurrentFrame} from 'remotion';
import {staticFile} from 'remotion';
import {CaptionTrack} from './CaptionTrack';
import {clamp, ease, font, palette, stage} from '../theme';

export const Canvas: React.FC<React.PropsWithChildren> = ({children}) => (
  <AbsoluteFill style={{background: palette.paper, fontFamily: font, color: palette.ink, overflow: 'hidden'}}>
    <div style={{position: 'absolute', width: 1050, height: 1050, right: -520, top: -600, borderRadius: '50%', background: '#e8efde', opacity: 0.7}} />
    <div style={{position: 'absolute', width: 700, height: 700, left: -450, bottom: -400, borderRadius: '50%', background: '#e3ecdc', opacity: 0.55}} />
    {children}
  </AbsoluteFill>
);

export const SceneFrame: React.FC<React.PropsWithChildren<{number: string; title: string; note: string; offsetSeconds: number; duration: number; footnote?: string}>> = ({number, title, note, offsetSeconds, duration, footnote, children}) => {
  const frame = useCurrentFrame();
  return (
    <Canvas>
      <div style={{position: 'absolute', left: 82, top: 34, right: 82, height: 66, display: 'flex', alignItems: 'center', gap: 18, opacity: interpolate(frame, [0, 12], [0, 1], clamp), translate: `0 ${interpolate(frame, [0, 18], [10, 0], {...clamp, easing: ease})}px`}}>
        <CanvasImage src={staticFile('images/logo.svg')} style={{width: 43, height: 43, objectFit: 'contain'}} />
        <span style={{fontSize: 20, letterSpacing: 3, color: palette.green, fontWeight: 600, marginLeft: 7}}>{number}</span>
        <div style={{height: 28, width: 1, background: palette.line}} />
        <div style={{fontSize: 32, fontWeight: 600, letterSpacing: 1}}>{title}</div>
        <div style={{marginLeft: 'auto', fontSize: 20, color: palette.body, display: 'flex', alignItems: 'center', gap: 10}}>
          <span style={{width: 7, height: 7, borderRadius: '50%', background: palette.green}} />
          {note}
        </div>
      </div>
      {footnote ? <div style={{position: 'absolute', left: 94, top: 104, fontSize: 16, color: palette.body}}>{footnote}</div> : null}
      <div style={{position: 'absolute', right: 94, top: 104, fontSize: 15, color: palette.muted}}>比赛 Demo 素材 · 真实操作录屏</div>
      <div style={{position: 'absolute', ...stage, background: palette.white, border: `1px solid ${palette.line}`, borderRadius: 18, boxShadow: '0 20px 70px rgba(35,68,42,0.10)', overflow: 'hidden', opacity: interpolate(frame, [0, 9], [0, 1], clamp), scale: interpolate(frame, [0, 18], [0.994, 1], {...clamp, easing: ease})}}>
        {children}
      </div>
      <div style={{position: 'absolute', left: 83, right: 83, top: 963, height: 2, background: palette.line}}>
        <div style={{width: `${interpolate(frame, [0, duration - 1], [0, 100], clamp)}%`, height: '100%', background: '#84a679'}} />
      </div>
      <CaptionTrack offsetSeconds={offsetSeconds} />
    </Canvas>
  );
};
