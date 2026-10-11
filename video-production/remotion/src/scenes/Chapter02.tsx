import React from 'react';
import {ProductionDataProvider} from '../ProductionData';
import {SceneFrame} from '../components/SceneFrame';
import {RealClip} from '../components/RealClip';

export const Chapter02: React.FC = () => (
  <ProductionDataProvider>
    <SceneFrame number="02" title="一份档案，持续照顾" note="启动物生.cmd → 浏览器 · 数据库驱动首页" offsetSeconds={15} duration={810}>
      <RealClip clip="ch02" duration={810} />
    </SceneFrame>
  </ProductionDataProvider>
);
