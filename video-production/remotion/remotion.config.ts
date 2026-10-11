import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(94);
Config.setCodec('h264');
Config.setPixelFormat('yuv420p');
Config.setVideoBitrate('5500k');
Config.setAudioBitrate('128k');
Config.setOverwriteOutput(true);
Config.setConcurrency(4);
Config.setBrowserExecutable('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe');
