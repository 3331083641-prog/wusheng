import {Easing} from 'remotion';

export const palette = {
  ink: '#173c2c',
  body: '#476253',
  green: '#347b50',
  lime: '#d6e7b5',
  muted: '#839584',
  white: '#ffffff',
  paper: '#f7f8f2',
  sage: '#e9eee2',
  line: '#dce5d6',
};

export const font = '"Microsoft YaHei", "Microsoft YaHei UI", "SimHei", sans-serif';
export const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const stage = {left: 82, top: 128, width: 1756, height: 818};

export type FilmProps = {
  qwenModel?: string;
};
