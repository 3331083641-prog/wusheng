# Visual and Remotion Studio review

Review scope: sampled composition PNG frames 720, 2100, 3240, 4350, 5520,
6360, 7230, 8040, 8610; opening/document design stills; an actual browser
session in Remotion Studio; and a 60-frame video render. This does not replace
the complete final MP4 QA.

- Subtitles occupy a separate bottom band. On the reviewed frames they are
  readable and do not cover the business controls or answers.
- EvidenceProvider and Qwen3-VL 4B are distinguished explicitly. The actual
  model is `qwen3-vl:4b-instruct-q4_K_M`.
- Studio was opened at `http://127.0.0.1:3060/WushengAIC`. The current-frame
  control was clicked, filled with `6720`, and confirmed with Enter. Preview
  successfully changed to `03:44.00` and displayed the actual concise Qwen
  answer. Inspector metadata: 1920x1080, 30 fps, 8700 frames.
- Studio screenshot: `../previews/studio-preview.png`. The browser console
  after the fixes reported zero errors and zero warnings.
- The answer at frame 6720 agrees with the actual API response in
  `capture-qwen-raw.json`: disconnect power before cleaning, use cold/warm
  water, next maintenance 2026-10-18, cleaner stock four bottles and SH71
  head stock three. The recorded API reports `modelInvoked=true`.
- Only the camera was changed for reading: Evidence answers at 1.25x and the
  final Qwen answer at 1.42x. The original recorded answer and Provider label
  remain in the image. No answer was rewritten or overlaid.
- Frame 7230 retains the complete QR square and permission controls. The
  inserted mobile-browser clip has a conspicuous, persistent label saying
  it is a mobile-browser demo awaiting physical-phone footage. It is not
  presented as a recording from an actual phone.
- The document chapter uses the actual recorded Edge PDF popup. Original
  PDF contents are unchanged.
- Frame 8040 is the beginning of the architecture reveal; nodes appear in
  the subsequent animation. Third-party RapidOCR/Qwen/Remotion attribution
  is visible. Closing typography, logo and repository address are readable.

## Render issue resolved

The newer `@remotion/media` Video frame extractor timed out during the full
preview despite successful still renders. All recording components now use
the official `remotion` OffthreadVideo, preserving trim offsets and image
proportions. The optional production metadata JSON is present, eliminating
its repeated 404 requests.

TypeScript passed. An independent `Ch02-Home` render of frames 0-59 completed
all 60 frames and encoding successfully:
`../previews/ch02-offthread-smoke.mp4` (960x540, 30 fps, two seconds).
