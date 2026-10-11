import React, {createContext, useContext, useEffect, useState} from 'react';
import type {Caption} from '@remotion/captions';
import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';

export type FocusPoint = {
  timeMs: number;
  x: number;
  y: number;
  kind?: string;
};

type ProductionData = {
  captions: Caption[];
  focus: Record<string, FocusPoint[]>;
  qwenModel: string;
};

const Context = createContext<ProductionData>({captions: [], focus: {}, qwenModel: '本地 Qwen'});

const normalizeFocus = (raw: unknown): Record<string, FocusPoint[]> => {
  if (!raw || typeof raw !== 'object') return {};
  const candidate = raw as Record<string, unknown>;
  const rawClips = (candidate.clips ?? candidate.focus ?? candidate) as Record<string, unknown>;
  const clips: Record<string, FocusPoint[]> = {};
  for (const [key, value] of Object.entries(rawClips)) {
    if (!Array.isArray(value)) continue;
    clips[key.replace(/\.mp4$/, '')] = value
      .filter((point) => point && typeof point === 'object')
      .map((point) => {
        const x = Number(point.x ?? point.cx ?? 0.5);
        const y = Number(point.y ?? point.cy ?? 0.5);
        return {
          timeMs: Number(point.timeMs ?? (point.time ?? point.t ?? 0) * 1000),
          x: x > 1 ? x / 1920 : x,
          y: y > 1 ? y / 1080 : y,
          kind: String(point.kind ?? point.type ?? point.interactionType ?? 'move'),
        };
      })
      .filter((point) => Number.isFinite(point.timeMs) && Number.isFinite(point.x) && Number.isFinite(point.y))
      .sort((a, b) => a.timeMs - b.timeMs);
  }
  return clips;
};

export const ProductionDataProvider: React.FC<React.PropsWithChildren<{qwenModel?: string}>> = ({children, qwenModel}) => {
  const [handle] = useState(() => delayRender('加载制作字幕与真实鼠标轨迹'));
  const [data, setData] = useState<ProductionData>({captions: [], focus: {}, qwenModel: qwenModel || '本地 Qwen'});
  useEffect(() => {
    let active = true;
    const optionalJson = async (name: string) => {
      const response = await fetch(staticFile(name));
      if (!response.ok) return {};
      return response.json();
    };
    Promise.all([
      fetch(staticFile('subtitles/captions.json')).then(async (response) => {
        if (!response.ok) throw new Error('缺少字幕 public/subtitles/captions.json；禁止无字幕正式导出。');
        return response.json();
      }),
      optionalJson('media/focus.json'),
      optionalJson('media/production.json'),
    ])
      .then(([captions, focus, metadata]) => {
        if (!active) return;
        const entries = Array.isArray(captions) ? captions : captions.captions;
        if (!Array.isArray(entries)) throw new Error('字幕 JSON 应为官方 Caption 数组。');
        setData({captions: entries, focus: normalizeFocus(focus), qwenModel: qwenModel || metadata.qwenModel || '本地 Qwen'});
        continueRender(handle);
      })
      .catch((error) => cancelRender(error));
    return () => {active = false;};
  }, [handle, qwenModel]);
  return <Context.Provider value={data}>{children}</Context.Provider>;
};

export const useProductionData = () => useContext(Context);
