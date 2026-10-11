import React from 'react';
import {interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {ProductionDataProvider} from '../ProductionData';
import {SceneFrame} from '../components/SceneFrame';
import {RealClip} from '../components/RealClip';
import {clamp, ease, palette} from '../theme';

export const Chapter07: React.FC = () => {
  const frame = useCurrentFrame();
  const split = interpolate(frame, [190, 220, 555, 580], [0, 1, 1, 0], {...clamp, easing: ease});
  return (
    <ProductionDataProvider>
      <SceneFrame number="07" title="一物一码，延伸到手边" note="同一局域网 · 只读档案 · 授权与有效期" offsetSeconds={228} duration={750}>
        <RealClip clip="ch07" duration={750} camera={false} style={{right: split * 480}} />
        <Sequence name="移动浏览器录屏（非手机实录）" from={210} durationInFrames={360}>
          <div style={{position: 'absolute', right: 27, top: 94, bottom: 22, width: 405, borderRadius: 19, border: `2px solid ${palette.line}`, overflow: 'hidden', background: 'white', boxShadow: '0 8px 35px #173c2c0d'}}>
            <OffthreadVideo src={staticFile('media/ch07-mobile.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'contain'}} />
          </div>
          <div style={{position: 'absolute', right: 23, top: 14, width: 422, background: '#e3edda', padding: '10px 8px', boxSizing: 'border-box', borderRadius: 10, textAlign: 'center', fontSize: 22, lineHeight: 1.35, fontWeight: 600, color: palette.ink}}>移动端浏览器演示<br />待替换手机实录</div>
        </Sequence>
      </SceneFrame>
    </ProductionDataProvider>
  );
};
