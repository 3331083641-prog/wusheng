import React from 'react';
import {CanvasImage, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {ProductionDataProvider} from '../ProductionData';
import {Canvas} from '../components/SceneFrame';
import {CaptionTrack} from '../components/CaptionTrack';
import {RealClip} from '../components/RealClip';
import {clamp, ease, palette, stage} from '../theme';

export const Chapter09: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <ProductionDataProvider>
      <Canvas>
        <div style={{position: 'absolute', ...stage, borderRadius: 18, border: `1px solid ${palette.line}`, overflow: 'hidden', opacity: interpolate(frame, [155, 235], [1, 0], {...clamp, easing: ease})}}>
          <RealClip clip="ch09" duration={420} camera={false} />
        </div>
        <div style={{position: 'absolute', left: 240, right: 240, top: 218, textAlign: 'center', opacity: interpolate(frame, [185, 250], [0, 1], {...clamp, easing: ease}), translate: `0 ${interpolate(frame, [185, 260], [25, 0], {...clamp, easing: ease})}px`}}>
          <CanvasImage src={staticFile('images/logo.svg')} style={{width: 125, height: 125, objectFit: 'contain', margin: '0 auto'}} />
          <div style={{fontSize: 91, letterSpacing: 15, marginTop: 20, fontWeight: 600}}>物生</div>
          <div style={{fontSize: 34, color: palette.body, lineHeight: 1.8, marginTop: 14}}>从购买到维护，从维修到延续使用。</div>
          <div style={{fontSize: 44, fontWeight: 500, marginTop: 24, letterSpacing: 2}}>让每一件物品，都被好好对待。</div>
          <div style={{fontSize: 23, color: palette.green, marginTop: 50}}>github.com/3331083641-prog/wusheng</div>
          <div style={{fontSize: 19, color: palette.muted, marginTop: 20}}>2026 AIC「AI+开源」 · 物生智联</div>
        </div>
        <CaptionTrack offsetSeconds={276} />
      </Canvas>
    </ProductionDataProvider>
  );
};
