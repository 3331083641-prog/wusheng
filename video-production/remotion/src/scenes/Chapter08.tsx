import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {ProductionDataProvider} from '../ProductionData';
import {SceneFrame} from '../components/SceneFrame';
import {RealClip} from '../components/RealClip';
import {clamp, ease, palette} from '../theme';

const ArchitectureNode: React.FC<{label: string; detail: string; index: number}> = ({label, detail, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = spring({frame: frame - 450 - index * 15, fps, config: {damping: 30, stiffness: 120}});
  return (
    <div style={{position: 'relative', marginBottom: 18, opacity: progress, translate: `${(1 - progress) * 20}px 0`}}>
      <div style={{height: 65, border: `1px solid ${palette.line}`, borderRadius: 12, background: index % 2 ? '#f1f6ea' : '#fff', display: 'flex', justifyContent: 'center', flexDirection: 'column', paddingLeft: 23}}>
        <div style={{fontSize: 24, fontWeight: 600}}>{label}</div>
        <div style={{fontSize: 16, marginTop: 3, color: palette.body}}>{detail}</div>
      </div>
      {index < 5 ? <svg width="20" height="18" style={{position: 'absolute', left: '50%', top: 65}}><path d="M 10 0 L 10 15 M 6 10 L 10 15 L 14 10" fill="none" stroke="#8aa37d" strokeWidth="1.8" /></svg> : null}
    </div>
  );
};

export const Chapter08: React.FC = () => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [440, 470], [0, 1], {...clamp, easing: ease});
  return (
    <ProductionDataProvider>
      <SceneFrame number="08" title="完整业务闭环，开放复用" note="维修 · 统计 · 本地优先 · 开源可复现" offsetSeconds={253} duration={690}>
        <RealClip clip="ch08" duration={690} camera={false} style={{right: reveal * 560}} />
        <div style={{position: 'absolute', right: 18, top: 41, width: 510, opacity: reveal, translate: `${(1 - reveal) * 40}px 0`}}>
          <div style={{fontSize: 30, fontWeight: 600, marginBottom: 20}}>让资料成为持续管理的依据</div>
          <ArchitectureNode label="图片与 PDF" detail="保留原件与物品绑定" index={0} />
          <ArchitectureNode label="RapidOCR 与来源追溯" detail="开源识别 · 候选融合 · 人工确认" index={1} />
          <ArchitectureNode label="SQLite 物品档案" detail="购买 · 保修 · 维护 · 维修记录" index={2} />
          <ArchitectureNode label="生命周期与耗材预测" detail="实际记录驱动 · 无历史不给虚假天数" index={3} />
          <ArchitectureNode label="EvidenceProvider / 本地 Qwen" detail="物品级上下文 · 检索依据 · 模型增强" index={4} />
          <ArchitectureNode label="提醒 · PDF 导出 · 一物一码" detail="在日常使用中形成反馈闭环" index={5} />
          <div style={{fontSize: 16, color: palette.body, lineHeight: 1.8, marginTop: 12}}>RapidOCR、Qwen：采用的开源技术<br />Remotion：视频制作框架；业务闭环由物生实现</div>
        </div>
      </SceneFrame>
    </ProductionDataProvider>
  );
};
