import React from 'react';
import {ProductionDataProvider} from '../ProductionData';
import {SceneFrame} from '../components/SceneFrame';
import {RealClip} from '../components/RealClip';

export const Chapter05: React.FC = () => (
  <ProductionDataProvider>
    <SceneFrame number="05" title="设备和耗材，形成持续管理" note="库存 → 消耗记录 → 趋势 → 补货与维护提醒" offsetSeconds={129} duration={1050}>
      <RealClip clip="ch05" duration={1050} />
    </SceneFrame>
  </ProductionDataProvider>
);
