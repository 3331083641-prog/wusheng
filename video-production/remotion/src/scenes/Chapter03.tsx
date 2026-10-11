import React from 'react';
import {ProductionDataProvider} from '../ProductionData';
import {SceneFrame} from '../components/SceneFrame';
import {RealClip} from '../components/RealClip';

export const Chapter03: React.FC = () => (
  <ProductionDataProvider>
    <SceneFrame number="03" title="从多张资料，到一份新档案" note="上传 → RapidOCR → 来源追溯 → 人工确认 → 保存" footnote="真实操作 · 识别等待已压缩" offsetSeconds={42} duration={1710}>
      <RealClip clip="ch03" duration={1710} />
    </SceneFrame>
  </ProductionDataProvider>
);
