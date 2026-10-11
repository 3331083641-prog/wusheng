import React from 'react';
import {Audio} from '@remotion/media';
import {AbsoluteFill, Composition, Folder, Sequence, staticFile} from 'remotion';
import {Chapter01} from './scenes/Chapter01';
import {Chapter02} from './scenes/Chapter02';
import {Chapter03} from './scenes/Chapter03';
import {Chapter04} from './scenes/Chapter04';
import {Chapter05} from './scenes/Chapter05';
import {Chapter06} from './scenes/Chapter06';
import {Chapter07} from './scenes/Chapter07';
import {Chapter08} from './scenes/Chapter08';
import {Chapter09} from './scenes/Chapter09';
import {palette, type FilmProps} from './theme';

export const WushengAIC: React.FC<FilmProps> = ({qwenModel}) => (
  <AbsoluteFill style={{background: palette.paper}}>
    <Sequence name="01 生活痛点与物生" from={0} durationInFrames={450}>
      <Chapter01 />
    </Sequence>
    <Sequence name="02 首页与整体 UI" from={450} durationInFrames={810}>
      <Chapter02 />
    </Sequence>
    <Sequence name="03 剃须刀多来源 OCR 建档" from={1260} durationInFrames={1710}>
      <Chapter03 />
    </Sequence>
    <Sequence name="04 PDF 资料与生命周期" from={2970} durationInFrames={900}>
      <Chapter04 />
    </Sequence>
    <Sequence name="05 耗材和维护提醒" from={3870} durationInFrames={1050}>
      <Chapter05 />
    </Sequence>
    <Sequence name="06 双层 AI 真实运行" from={4920} durationInFrames={1920}>
      <Chapter06 qwenModel={qwenModel} />
    </Sequence>
    <Sequence name="07 一物一码与移动端" from={6840} durationInFrames={750}>
      <Chapter07 />
    </Sequence>
    <Sequence name="08 维修统计与开源创新" from={7590} durationInFrames={690}>
      <Chapter08 />
    </Sequence>
    <Sequence name="09 让每一件物品被好好对待" from={8280} durationInFrames={420}>
      <Chapter09 />
    </Sequence>
    <Audio src={staticFile('audio/narration-music.wav')} volume={1} />
  </AbsoluteFill>
);

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="WushengAIC" component={WushengAIC} width={1920} height={1080} fps={30} durationInFrames={8700} defaultProps={{qwenModel: 'qwen3-vl:4b-instruct-q4_K_M'}} />
    <Composition id="WushengFilm" component={WushengAIC} width={1920} height={1080} fps={30} durationInFrames={8700} defaultProps={{qwenModel: 'qwen3-vl:4b-instruct-q4_K_M'}} />
    <Folder name="Chapters">
      <Composition id="Ch01-Opening" component={Chapter01} width={1920} height={1080} fps={30} durationInFrames={450} />
      <Composition id="Ch02-Home" component={Chapter02} width={1920} height={1080} fps={30} durationInFrames={810} />
      <Composition id="Ch03-Create" component={Chapter03} width={1920} height={1080} fps={30} durationInFrames={1710} />
      <Composition id="Ch04-Documents" component={Chapter04} width={1920} height={1080} fps={30} durationInFrames={900} />
      <Composition id="Ch05-Consumables" component={Chapter05} width={1920} height={1080} fps={30} durationInFrames={1050} />
      <Composition id="Ch06-AI" component={Chapter06} width={1920} height={1080} fps={30} durationInFrames={1920} defaultProps={{qwenModel: 'qwen3-vl:4b-instruct-q4_K_M'}} />
      <Composition id="Ch07-Sharing" component={Chapter07} width={1920} height={1080} fps={30} durationInFrames={750} />
      <Composition id="Ch08-Innovation" component={Chapter08} width={1920} height={1080} fps={30} durationInFrames={690} />
      <Composition id="Ch09-Closing" component={Chapter09} width={1920} height={1080} fps={30} durationInFrames={420} />
    </Folder>
  </>
);
