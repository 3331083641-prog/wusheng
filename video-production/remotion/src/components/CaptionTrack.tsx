import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {useProductionData} from '../ProductionData';
import {clamp, font, palette} from '../theme';

// Captions use the official Caption JSON format. Sentence-level timing is shared
// with the SRT; this bottom safe area stays outside the captured application.
export const CaptionTrack: React.FC<{offsetSeconds: number}> = ({offsetSeconds}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {captions} = useProductionData();
  const timeMs = (frame / fps + offsetSeconds) * 1000;
  const cue = captions.find((caption) => timeMs >= caption.startMs && timeMs < caption.endMs);
  if (!cue) return null;
  const local = (timeMs - cue.startMs) / 1000 * fps;
  return (
    <div style={{position: 'absolute', left: 145, right: 145, bottom: 30, minHeight: 76, display: 'flex', justifyContent: 'center', alignItems: 'center', pointerEvents: 'none'}}>
      <div style={{fontFamily: font, color: palette.ink, background: 'rgba(247,248,242,0.98)', border: `1px solid ${palette.line}`, borderRadius: 16, padding: '11px 30px 13px', maxWidth: 1570, fontSize: 34, lineHeight: 1.42, fontWeight: 500, textAlign: 'center', whiteSpace: 'pre-line', textWrap: 'balance', opacity: interpolate(local, [0, 3], [0.5, 1], clamp), boxShadow: '0 4px 22px rgba(23,60,44,0.035)'}}>
        {cue.text.trim()}
      </div>
    </div>
  );
};
