import React from 'react';
import {OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {ProductionDataProvider, useProductionData} from '../ProductionData';
import {SceneFrame} from '../components/SceneFrame';
import {RealClip} from '../components/RealClip';
import {palette, type FilmProps} from '../theme';

const AIContent: React.FC = () => {
  const frame = useCurrentFrame();
  const {qwenModel} = useProductionData();
  return (
    <SceneFrame number="06" title="双层助手，同一份物品证据" note={frame < 840 ? 'EvidenceProvider · 无需大模型' : '本地 Qwen3-VL 4B · 实际模型增强'} offsetSeconds={164} duration={1920}>
      <Sequence name="EvidenceProvider 真实问答" from={0} durationInFrames={840}>
        <RealClip clip="ch06-evidence" duration={840} zoom={{frames: [0, 100, 130, 250, 280, 380, 410, 540, 570, 660, 690, 839], scales: [1, 1, 1.25, 1.25, 1, 1, 1.25, 1.25, 1, 1, 1.25, 1.25], x: 0.44, y: 0.56}} />
      </Sequence>
      <Sequence name="两种实际录像并置对照" from={840} durationInFrames={120}>
        <div style={{position: 'absolute', inset: 0, background: palette.paper, display: 'flex', padding: '32px 24px', gap: 22, boxSizing: 'border-box'}}>
          <div style={{width: '50%', height: '100%', background: 'white', borderRadius: 15, border: `1px solid ${palette.line}`, overflow: 'hidden'}}>
            <div style={{padding: '22px 28px 0', fontSize: 29, color: palette.ink, fontWeight: 600}}>EvidenceProvider</div>
            <div style={{padding: '10px 28px', fontSize: 21, color: palette.body}}>本地档案规则 · 可追溯证据</div>
            <OffthreadVideo src={staticFile('media/ch06-evidence.mp4')} trimBefore={720} muted style={{width: '100%', height: 620, objectFit: 'contain'}} />
          </div>
          <div style={{width: '50%', height: '100%', background: 'white', borderRadius: 15, border: `1px solid ${palette.line}`, overflow: 'hidden'}}>
            <div style={{padding: '22px 28px 0', fontSize: 29, color: palette.ink, fontWeight: 600}}>本地 Qwen3-VL 4B</div>
            <div style={{padding: '10px 28px', fontSize: 21, color: palette.body}}>物品上下文 · 自然语言表达增强</div>
            <OffthreadVideo src={staticFile('media/ch06-qwen.mp4')} muted style={{width: '100%', height: 620, objectFit: 'contain'}} />
          </div>
        </div>
      </Sequence>
      <Sequence name="本机 Qwen 真实模型返回" from={960} durationInFrames={960}>
        <RealClip clip="ch06-qwen" trimBefore={120} duration={960} zoom={{frames: [0, 570, 615, 959], scales: [1, 1, 1.42, 1.42], x: 0.44, y: 0.56}} />
      </Sequence>
      {frame >= 960 && frame < 1130 ? <div style={{position: 'absolute', left: 24, bottom: 13, padding: '7px 13px', borderRadius: 7, background: '#f8faf2f0', color: palette.body, fontSize: 17}}>实际模型：{qwenModel}</div> : null}
    </SceneFrame>
  );
};

export const Chapter06: React.FC<FilmProps> = ({qwenModel}) => (
  <ProductionDataProvider qwenModel={qwenModel || 'qwen3-vl:4b-instruct-q4_K_M'}>
    <AIContent />
  </ProductionDataProvider>
);
