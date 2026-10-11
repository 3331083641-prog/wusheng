import React from 'react';
import {ProductionDataProvider} from '../ProductionData';
import {SceneFrame} from '../components/SceneFrame';
import {RealClip} from '../components/RealClip';

export const Chapter04: React.FC = () => (
  <ProductionDataProvider>
    <SceneFrame number="04" title="说明书、凭证与生命周期" note="原始 PDF · 本地持久化 · 中文档案导出" offsetSeconds={99} duration={900}>
      <RealClip clip="ch04" duration={900} />
    </SceneFrame>
  </ProductionDataProvider>
);
