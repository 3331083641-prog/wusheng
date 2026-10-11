import React from 'react';
import {interpolate, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {useProductionData, type FocusPoint} from '../ProductionData';
import {clamp, ease, palette} from '../theme';

const cursorAt = (points: FocusPoint[], timeMs: number): FocusPoint | null => {
  if (!points.length) return null;
  let index = points.findIndex((point) => point.timeMs >= timeMs);
  if (index < 0) return points[points.length - 1];
  if (index === 0) return points[0];
  const previous = points[index - 1];
  const next = points[index];
  const amount = Math.min(1, Math.max(0, (timeMs - previous.timeMs) / Math.max(1, next.timeMs - previous.timeMs)));
  return {timeMs, x: previous.x + (next.x - previous.x) * amount, y: previous.y + (next.y - previous.y) * amount, kind: previous.kind};
};

type AnswerZoom = {frames: number[]; scales: number[]; x: number; y: number};

export const RealClip: React.FC<{clip: string; duration: number; trimBefore?: number; camera?: boolean; cursor?: boolean; zoom?: AnswerZoom; style?: React.CSSProperties}> = ({clip, duration, trimBefore = 0, camera = true, cursor = false, zoom, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {focus} = useProductionData();
  const points = focus[clip.replace(/\.mp4$/, '')] || [];
  const timeMs = (frame + trimBefore) / fps * 1000;
  const position = cursorAt(points, timeMs);
  const click = points.filter((point) => /click|down/.test(point.kind || '') && point.timeMs <= timeMs).at(-1);
  const sinceClick = click ? (timeMs - click.timeMs) / 1000 * fps : 10000;
  const clickWeight = camera ? interpolate(sinceClick, [0, 16, 70, 100], [0, 1, 1, 0], {...clamp, easing: ease}) : 0;
  const targetX = Math.min(0.8, Math.max(0.2, click?.x ?? 0.5));
  const targetY = Math.min(0.8, Math.max(0.2, click?.y ?? 0.5));
  const readingScale = zoom ? interpolate(frame, zoom.frames, zoom.scales, {...clamp, easing: ease}) : 1;
  const imageScale = zoom ? readingScale : camera ? interpolate(frame, [0, duration], [1, 1.012], clamp) + clickWeight * 0.045 : 1;
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden', background: '#fff', ...style}}>
      <div style={{position: 'absolute', inset: 0, scale: imageScale, transformOrigin: `${(zoom?.x ?? targetX) * 100}% ${(zoom?.y ?? targetY) * 100}%`}}>
        <OffthreadVideo src={staticFile(`media/${clip}.mp4`)} trimBefore={trimBefore} muted style={{width: '100%', height: '100%', objectFit: 'contain'}} />
        {cursor && position ? (
          <svg viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid meet" style={{position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none'}}>
            {sinceClick < 20 && click ? <circle cx={click.x * 1920} cy={click.y * 1080} r={interpolate(sinceClick, [0, 20], [8, 32], clamp)} fill="none" stroke={palette.green} strokeWidth="3" opacity={interpolate(sinceClick, [0, 20], [0.65, 0], clamp)} /> : null}
            <path d="M 0 0 L 0 25 L 7 19 L 13 31 L 18 28 L 12 17 L 23 16 Z" fill="#203e2c" stroke="white" strokeWidth="1.6" strokeLinejoin="round" style={{translate: `${position.x * 1920}px ${position.y * 1080}px`, filter: 'drop-shadow(0 2px 2px #0003)'}} />
          </svg>
        ) : null}
      </div>
    </div>
  );
};
