import React from 'react';
import {CanvasImage, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ProductionDataProvider} from '../ProductionData';
import {Canvas} from '../components/SceneFrame';
import {CaptionTrack} from '../components/CaptionTrack';
import {clamp, ease, palette} from '../theme';

const Document: React.FC<{source: string; label: string; x: number; y: number; rotation: number; delay: number}> = ({source, label, x, y, rotation, delay}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const arrival = spring({frame: frame - delay, fps, config: {damping: 28, stiffness: 90, mass: 1.1}});
  const converge = interpolate(frame, [125, 215], [0, 1], {...clamp, easing: ease});
  return (
    <div style={{position: 'absolute', left: x + (795 - x) * converge, top: y + (230 - y) * converge, width: 330, height: 300, background: '#fff', padding: 13, boxSizing: 'border-box', borderRadius: 14, border: `1px solid ${palette.line}`, boxShadow: '0 18px 55px rgba(27,62,38,0.10)', rotate: `${rotation * (1 - converge)}deg`, scale: arrival * (1 - converge * 0.23), translate: `0 ${(1 - arrival) * 70}px`, opacity: interpolate(frame, [190, 230], [1, 0], clamp)}}>
      <CanvasImage src={staticFile(`images/${source}.png`)} style={{width: '100%', height: 234, objectFit: 'contain', borderRadius: 6}} />
      <div style={{fontSize: 23, color: palette.body, margin: '9px 9px 0', fontWeight: 500}}>{label}</div>
    </div>
  );
};

export const Chapter01: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <ProductionDataProvider>
      <Canvas>
        <div style={{position: 'absolute', left: 105, top: 64, color: palette.green, fontSize: 22, letterSpacing: 4, opacity: interpolate(frame, [0, 18, 190, 220], [0, 1, 1, 0], clamp)}}>购买 · 使用 · 维护 · 延续</div>
        <Document source="order" label="购买资料" x={185} y={200} rotation={-9} delay={5} />
        <Document source="manual_image" label="使用说明" x={620} y={110} rotation={5} delay={12} />
        <Document source="warranty" label="保修与凭证" x={1350} y={205} rotation={9} delay={19} />
        <Document source="cleaner" label="耗材与维护" x={1070} y={565} rotation={-5} delay={26} />
        <div style={{position: 'absolute', left: 255, top: 606, color: palette.body, fontSize: 43, lineHeight: 1.6, opacity: interpolate(frame, [20, 45, 125, 160], [0, 1, 1, 0], clamp)}}>资料容易散落，<br />照顾可以延续。</div>
        <div style={{position: 'absolute', left: 630, top: 220, width: 660, height: 600, textAlign: 'center', opacity: interpolate(frame, [195, 240], [0, 1], clamp), translate: `0 ${interpolate(frame, [195, 240], [30, 0], {...clamp, easing: ease})}px`}}>
          <CanvasImage src={staticFile('images/logo.svg')} style={{width: 130, height: 130, objectFit: 'contain', margin: '0 auto'}} />
          <div style={{fontSize: 103, letterSpacing: 18, marginTop: 15, fontWeight: 600}}>物生</div>
          <div style={{fontSize: 29, lineHeight: 1.6, marginTop: 16, color: palette.body}}>AI 驱动的家庭物品<br />全生命周期智能管理平台</div>
          <div style={{fontSize: 20, color: palette.green, marginTop: 32, letterSpacing: 3}}>2026 AIC「AI+开源」 · 物生智联</div>
        </div>
        <div style={{position: 'absolute', top: 800, left: 220, right: 220, textAlign: 'center', fontSize: 42, letterSpacing: 3, fontWeight: 500, opacity: interpolate(frame, [310, 345], [0, 1], clamp)}}>让每一件物品，都被好好对待。</div>
        <CaptionTrack offsetSeconds={0} />
      </Canvas>
    </ProductionDataProvider>
  );
};
