# Cadenza · Stoller Hall

A standalone macOS presentation app for an operator-led orchestral listening experiment. Two PySide6/QML windows share a YAML-driven sequence. The included programme follows the Audience Booklet for the Cadenza–Camerata Research Concert on 29 October 2026.

## Project layout

```text
config/
  show.yaml             # editable event programme
  caption-config.yaml   # local audio/Speechmatics settings (Git-ignored)
docs/
  preview.png           # operator screenshot
src/cadenza/            # application code and QML
tests/                 # automated checks
```

Run commands from the project root: the default configuration paths are relative to the current working directory. For another directory or a packaged installation, pass explicit `--show` and `--caption-config` paths. The editable configuration files are not bundled into the Python package.

`src/*.egg-info`, `.venv`, and `__pycache__` are generated development files, already ignored by Git; `uv.lock` is the dependency lockfile and should be kept.

## Run now

The existing live-caption environment already contains the required libraries:

```sh
cd /Users/jon/projects/cadenza-stoller-hall
PYTHONPATH=src /Users/jon/projects/live-caption/.venv/bin/python -m cadenza.app
```

This starts **demo mode**, with synthetic captions and no microphone/network access.

For an independent environment and the `cadenza` command:

```sh
cd /Users/jon/projects/cadenza-stoller-hall
uv sync
uv run cadenza
```

To use live Speechmatics transcription:

```sh
uv run cadenza --live
```

Cadenza reads `config/caption-config.yaml` by default. This local file is ignored by Git because it may contain an API key. You can also use `SPEECHMATICS_API_KEY` instead of storing the key in YAML. Pass `--caption-config /absolute/path/to/config.yaml` to use another configuration. macOS must grant microphone access to the launching terminal/application. The caption worker uses the existing live-caption `.venv/bin/python`; use `--live-caption /path/to/live-caption` to change the checkout. A source failure appears on the operator display without interrupting slides.

Replay an existing raw live-caption JSONL recording:

```sh
uv run cadenza --replay /absolute/path/to/session.jsonl
```

## Operation

- Choose the audience monitor and select **Present full screen**. The operator window stays on its current screen. Escape returns the audience window to windowed mode.
- **Next/Back**, Right/Left arrows, and Space (next) advance the sequence. Navigation stops at the first and last slide.
- **AUTO** follows each slide's `captions` setting; **ON/OFF** overrides it. Changing slides or overrides clears old text. Caption text expires after eight seconds without updates.
- Countdown and count-up slides share one Timer row with two buttons. Both wait for Start on entry. Start/Pause/Resume controls the current run; Stop freezes it and changes to Restart, which starts a fresh run. At countdown zero, use Restart or advance manually. Revisiting a timer slide resets it and waits for Start.
- Captions being hidden does **not** stop microphone capture or transcription. Live mode streams continuously until the application closes.
- Close the operator window to quit both windows and stop the caption process. Closing the audience window alone allows it to be reopened with the display controls.

## Custom programme

Edit `config/show.yaml`, or copy it and pass `--show /path/to/programme.yaml`. Each slide needs a unique string `id`, `kind`, and text `title`. Supported kinds: `intro`, `mc`, `experiment`, `music`, `response`, `countup`, `closing`. Optional fields: `body`, `notes` (operator only), `captions` (boolean, default false), `passage`, `page`. Response slides require a positive `duration` in seconds.

The audience view uses the title/body, persistent excerpt (`passage`) and booklet `page` labels on every applicable slide, response ring and digital countdown, and a separate caption band. Music slides are presentation states: they do not play audio or cue external equipment. Use short titles/body text and rehearse the actual content on the venue display.

## Architecture and checks

`model.py` validates YAML and owns monotonic timers. `app.py` exposes shared state to two QML windows. `bridge.py` runs in a separate process, importing live-caption ASR/config/recording/processing modules, and sends JSON-lines events to the presentation. No overlay UI is loaded, and caption credentials remain in the local configuration or environment. The adapter forwards processed partial/final events to the presentation. The Qt process imports only live-caption’s shared renderers, measuring text in the audience font. Both apps use the shared caption processor before rendering.

```sh
PYTHONPATH=src /Users/jon/projects/live-caption/.venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src QT_QPA_PLATFORM=offscreen /Users/jon/projects/live-caption/.venv/bin/python -m cadenza.app --smoke-test
```

Live microphone/Speechmatics authentication and a physical second monitor need an on-site rehearsal. The first pass is a source-based application, not a signed macOS app bundle.

## Second-section music timer

The `countup` slide type displays a large digital audience timer with captions off in AUTO mode in the supplied programme. It opens at `00:00` and stays stopped while the MC explains. Press **Start** when the conductor begins; it then counts upwards with no duration limit. Minutes continue past 59 (for example, `60:00`); there is no ring or automatic advancement.

The shared **Timer** row controls either timer type. **Start** begins, **Pause** holds, and **Resume** continues the same run. **Stop** holds the final value; the second button then becomes **Restart**, which immediately begins a fresh run from zero (count-up) or the configured duration (countdown). The first button is disabled after Stop or countdown completion. Leaving the slide discards its timer; returning resets it and waits for Start. There is no separate whole-event elapsed timer.

```yaml
- id: music-2
  kind: countup
  title: Listening experiment · 02
  body: Please listen to the orchestra.
  captions: false
```

## Booklet-aligned running order

The 26-slide show opens with a photographic arrivals slide, followed by one MC introduction, ten listening/response pairs, an excerpt-rating close, a cue-marking introduction, a cue-marking timer, and a final close. Hold the opening MC slide for the event introduction and Movement I, switching captions OFF during music. Background questionnaire pages 3–4, definitions page 5, and activity instructions page 6 are covered in the MC notes.

| Excerpt | Booklet page | Focus |
| --- | --- | --- |
| 1 (trial) | 7 | Loudness |
| 2 (trial) | 8 | Loudness |
| 3 | 9 | Clarity |
| 4 | 10 | Clarity |
| 5 | 12 | Loudness and distortion |
| 6 | 14 | Loudness and distortion |
| 7 | 15 | Frequency balance and harshness |
| 8 | 16 | Frequency balance and harshness |
| 9 | 18 | Clarity |
| 10 | 19 | Clarity |

For each excerpt, select **AUTO** for the spoken introduction, stay on the same listening slide, and manually select **OFF** when the orchestra begins. When the music ends, advance to the response slide and press **Start** for 60 seconds. At zero, advance manually and restore **AUTO** for the next introduction. Overrides persist across navigation; no slide transition changes a manual ON/OFF choice.

Cue marking is optional during Movement V. Introduce page **20**, with continuation on page **21**. Advance to the count-up slide before the music starts, then press **Start** exactly when it begins. The audience records approximate **MM:SS** times and brief experiences. Press **Stop** at the end and advance to the final close when ready. Restore **AUTO** for spoken closing remarks.

Audience styling remains in `src/cadenza/qml/DisplayStyle.qml`; `qmldir` registers the singleton and is included in packaged installations. Live microphone transcription and second-monitor presentation still require a venue rehearsal.

### Arrivals screen

The show opens with the orchestra photograph and event details, using lime and pink accents from the event flier. Leave captions on AUTO while the audience takes their seats; the arrivals slide hides captions. Press Next when the event begins to show the MC introduction with captions enabled. The photograph is bundled in `src/cadenza/qml/assets/orchestra.jpg`. The `arrivals` kind uses `ArrivalsSlide.qml`; its title and repertoire text come from the show YAML.

## Export for feedback

From the project root, export the complete audience slide sequence:

```sh
uv run cadenza --export-pdf output/cadenza-review.pdf
```

Use `--show /path/to/show.yaml` to export another programme. The command creates the output directory if needed and replaces an existing PDF only after a successful export. It exits without opening presentation windows, capturing audio, or connecting to transcription.

Each landscape 16:9 page is a 1920×1080 rendering of the actual audience QML, including the arrivals photograph. This preserves the on-screen design; text in the PDF is rasterised rather than selectable. Slides appear in programme order, with countdowns at their starting duration and count-up timers at 00:00. Live captions and operator notes are omitted; use `--pdf-subtitles` below to include sample captions and a region outline. This is a static content/design review, not a recording of timer or caption behaviour.

Movement V uses the same centred page/instruction layout as the excerpts, with `movement: V` identifying it separately. Optional-task explanations and the page 21 continuation remain in the booklet and host notes.

## Diagnosing problems on the day

Every launch writes timestamped diagnostics to `logs/cadenza.log` and the terminal. The operator window shows the absolute log path; errors appear in red with the specific caption error when available. Use `--log-dir /path/to/logs` to choose another writable location. Logs rotate at 2 MB with three backups (`cadenza.log.1` through `.3`).

Logs include startup paths/mode, slide navigation, caption overrides, source status/errors, full caption-process stderr (including Python tracebacks), process exit codes, Qt messages, and uncaught Python exceptions. The first caption received is recorded as an event without its words. Caption transcripts, audio and complete configuration contents are not deliberately recorded; known configured secrets and common credential patterns are redacted. Third-party diagnostic messages can still contain contextual data, so review logs before sharing.

If captions stop, check the operator status and inspect `logs/cadenza.log` (and `.1` if rotation occurred). A successful audio input check in macOS does not rule out a caption connection or startup error; the log identifies the failing stage.

## Measured live captions and smooth scrolling

Cadenza now defaults to the shared `bbc_live` renderer. Launch using the usual command:

```sh
uv run cadenza --live --caption-config ./config/caption-config.yaml
```

The bridge isolates microphone/transcription in its own process and sends processed speech events. Cadenza supplies Qt font measurements to the shared renderer on its GUI thread, then displays the resulting two lines without wrapping or shrinking them again. Operator preview and audience view share a reference caption width, so their line breaks match even at different window sizes. Slide navigation, manual caption overrides and the eight-second idle timeout clear renderer history as well as the visible caption. Hidden speech is not added to the renderer.

Set animation duration in your caption configuration:

```yaml
overlay:
  scroll_duration_ms: 180  # set to 0 to disable; accepted range 0–1000 ms
```

The new-line transition moves upward once; ordinary word updates remain immediate. Corrections and multi-line bursts snap to current text rather than queueing animations. Use `--caption-layout bbc` or `--caption-layout rolling` for the legacy layouts. Cadenza’s CLI layout choice defaults to `bbc_live` and takes precedence over `overlay.layout`, which remains available for the standalone live-caption app.

Audience font settings remain in `src/cadenza/qml/DisplayStyle.qml`: `captionFontFamily` (Arial) and `captionFontPx` (31, unchanged). These are reference pixels for the 1280×720 slide canvas, rather than the standalone overlay’s native macOS font size. Restart after changing them. The caption band expands if necessary to accommodate two lines at the chosen size; rehearse larger settings to check clearance from slide content.

Test without microphone/network access, using the live-caption sample recording:

```sh
uv run cadenza --replay /Users/jon/projects/live-caption/tests/fixtures/caption-layout.jsonl
```

Advance past arrivals or select captions ON before the recording begins. A new subprocess GUI regression check exercises measured wrapping, animation/off, history resets, three display sizes and replay through the real caption bridge. Use the updated live-caption checkout for the shared schema, processing and renderers.

### Caption region width in Cadenza

Cadenza reads `overlay.width_fraction` and `overlay.max_width` from the file passed with `--caption-config` (default `config/caption-config.yaml`). Restart after changing them:

```yaml
overlay:
  width_fraction: 0.60
  max_width: 900
```

The band remains centred. Width is a fraction of the 1280-wide reference slide canvas, capped by `max_width` in reference pixels, then scaled with the slide. For example, `width_fraction: 0.20` gives a 256-reference-pixel band, minus internal padding for text. Both operator preview and audience display use the same measured wrapping width. If omitted, the existing `DisplayStyle.captionSideMargin` controls width. The cap scales with the presentation; it is not a fixed physical pixel size on every display. Cadenza does not automatically read `~/.config/live-caption/config.yaml`; pass that file explicitly if desired.

### Preview subtitle placement in the review PDF

```sh
uv run cadenza --export-pdf output/cadenza-subtitle-review.pdf --pdf-subtitles
```

`--pdf-subtitles` adds static Lorem ipsum sample captions and a pink outline marking the full subtitle region on **every slide**, including arrivals and music slides where AUTO normally hides captions. It uses the actual caption font, padding, two-line wrapping and the width settings in `--caption-config` (default `config/caption-config.yaml`). Scrolling is frozen for the PDF. The outline is a review aid and is not shown in the live presentation.

Omit the switch for the usual export without captions. `--pdf-subtitles` requires `--export-pdf`; audio and live transcription are never started during export.

## Welcome slide logos

The `mc-introduction` slide uses `layout: welcome`. `WelcomeSlide.qml` displays its existing title and body, followed by authentic Cadenza/Camerata, university organiser, and EPSRC funder logos. Other slides retain their existing layout. The logo panel ends above the reserved caption area. Artwork is bundled locally (including packaged installs), so the welcome slide needs no network connection. Sources are recorded in `src/cadenza/qml/assets/logos/SOURCES.json`; original colours and aspect ratios are retained.

## Per-slide typography and layout

Standard text slides accept an optional `subtitle` (below the body) and a `style` mapping. Plain text stays separate from presentation; HTML markup is not needed. Existing slides keep their defaults when options are omitted. For example:

```yaml
- id: gabor-takacs-nagy
  kind: mc
  title: Beethoven at the time of writing Symphony 6
  body: Gábor Takács-Nagy
  subtitle: Conductor of the Manchester Camerata
  captions: true
  style:
    alignment: center
    spacing: 22
    body:
      font_size: 64
      bold: true
    subtitle:
      font_size: 30
      italic: true
```

`style.title`, `style.body` and `style.subtitle` each support `font_size`, `bold`, `italic` and `font_family`. The outer style supports `alignment` (`left`, `center`, `right`), `spacing` (between visible text blocks), `content_y` (top of the text column), and `side_margin` (left/right margin, below 640). All sizes and distances are reference pixels on the 1280×720 canvas and scale with the slide; they are not PowerPoint points. Unknown options or invalid types fail at show loading with an error.

These controls affect the standard text column, including excerpt slides; they do not reposition booklet labels, timers or captions. Arrivals and the logo welcome slide use dedicated layouts with their own geometry. Keep those as reusable templates; add further named layouts when a slide needs a different structure rather than accumulating arbitrary coordinates. Preview larger text with `--export-pdf ... --pdf-subtitles` to check that it clears timers and captions.

When no per-slide `font_family` is supplied, text uses the Qt application font in both live presentation and PDF export. Empty font names are not used, avoiding platform-dependent emoji-font fallback and oversized word spacing.

## Shared caption configuration and profanity handling

Both apps use `live_caption.config.load_config` / `resolve_config` and
`live_caption.processor.CaptionProcessor` from the live-caption checkout.
Speechmatics and replay events are processed before text measurement/wrapping.
Cadenza applies this in its bridge for both `--raw` (processed hypotheses) and
legacy rendered output; the presentation does not implement a second filter.
Use the same YAML file in both apps to share audio, Speechmatics, processing,
`overlay`, and `bbc` settings. Unknown/existing settings are preserved.

```yaml
processing:
  profanity:
    mode: omit
    additional_words: []
    allow_words: []
```

`omit` is the default when no profanity settings are supplied. It removes whole
words tagged as profanity by Speechmatics, plus a built-in English list including
common inflections even when tags are absent (e.g. a spurious ASR hypothesis).
Matching is case-insensitive and respects word boundaries, so `assessment` and
`Scunthorpe` are retained. `additional_words` adds whole words or phrases;
`allow_words` permits exact terms, including tagged terms. The English list lives
in `live_caption/processor.py` as `DEFAULT_PROFANITIES`; it is not an exhaustive
multilingual or obfuscated-profanity detector. Partial word fragments that do not
yet match a complete term are not guessed or delayed.

Set `mode: off` to show ASR output verbatim. The old
`processing.profanity_filter: false` remains an explicit opt-out; `true` now
means omission. An explicit `processing.profanity` mapping takes precedence over
the old flag. `profanity_replacement` is accepted for compatibility but ignored;
there is no masking/bleeping mode. Remove the legacy false flag to adopt the new
default, or explicitly select `mode: omit`.

Each partial replaces the preceding provisional hypothesis; every final commits
only its newly recognised clean text. Empty/fully omitted updates still clear
provisional text while retaining earlier committed speech. Omission removes
attached punctuation and empty quote/bracket pairs and closes whitespace gaps.
Filtering precedes all three renderers (`bbc_live`, `bbc`, `rolling`), so omitted
words consume no layout width. Font, alignment, line count, line width, measured
wrapping and animation settings keep their existing meanings. Cadenza retains
its presentation font and CLI layout override.

Raw `--record` JSONL files intentionally retain the original ASR text/payload,
including any profanity; replay applies the current processing settings. The
filter changes captions, not audio or recognition accuracy. Restart the app
after changing settings.

See `config/caption-config.example.yaml` for the tracked credential-free example.
The existing local `config/caption-config.yaml` remains Git-ignored. To use the
same settings as the standalone overlay:

```sh
uv run cadenza --live --caption-config ~/.config/live-caption/config.yaml
```

Cadenza imports the schema from the checkout selected by `--live-caption` and
validates it at startup; its bridge uses that same checkout/interpreter. Its
presentation state retains only `overlay` and `bbc`, excluding credentials.

## Shared ASR vocabulary file

The shared loader in `live_caption.vocabulary` accepts a UTF-8 YAML list:

```yaml
- Cadenza
- content: Stoller Hall
- content: Camerata
# Optional pronunciation hints (Speechmatics' example):
- content: gnocchi
  sounds_like: [nyohki, nokey]
```

Use `content` for the spelling to display. Omit `sounds_like` to let Speechmatics
infer pronunciation. An empty file or `[]` supplies no extra words.

Set the top-level `vocabulary_file` in your existing caption configuration:

```yaml
vocabulary_file: /Users/jon/projects/live-caption/vocabulary.yaml
```

Config paths resolve relative to the containing config file; `~` is expanded.
A CLI `--vocabulary FILE` (alias `--vocabulary-file`) overrides this path and
resolves relative to the launch directory. No file is loaded implicitly: omit
the setting or set it to `null` to use only inline vocabulary/default ASR.
Both apps use the same live-caption loader, validator and Speechmatics worker.
Cadenza passes the CLI override through to its caption subprocess.

Existing `speechmatics.additional_vocab` entries are combined with the file's
entries (inline first), with exact duplicates removed. Different pronunciation
entries are preserved. Files are read at application startup; restart after
editing. The list is sent as `additional_vocab` when live recognition starts;
it does not rewrite existing transcripts or affect replayed recognition results,
caption layout or the profanity filter. Replay still validates configured files.

Missing/malformed files, invalid entries and unsupported entry keys produce a
startup error with the source filename/entry. Entries and pronunciation hints
must contain at most six words, each at most 4000 characters; the combined list
cannot exceed 20,000 entries. Speechmatics recommends no more than 1,000 entries
for best performance. Large dictionaries can increase session startup time;
reuse of an identical dictionary benefits from server-side caching. See the
[Speechmatics custom dictionary documentation](https://docs.speechmatics.com/speech-to-text/features/custom-dictionary).

Use live-caption's starter file as the single editable list for both projects:

```sh
uv run cadenza --live --vocabulary /Users/jon/projects/live-caption/vocabulary.yaml
```

The tracked `config/caption-config.example.yaml` references that sibling
live-caption file. Adjust the path for a different checkout location.

## Start a fresh caption line after a pause

In `bbc_live`, speech arriving after a pause starts on a fresh line even if the
previous committed line is shorter than half the caption width or has no full
stop. The default threshold is two seconds. Configure it in the shared caption
YAML and restart either app:

```yaml
bbc:
  pause_threshold_seconds: 2.0  # seconds; 0 disables pause-based breaks
```

The break appears when speech resumes, rather than inserting blank lines while
the speaker is silent. For example, `Hi.` followed by a three-second pause and
`Welcome back` displays as `Hi.` then `Welcome back` on separate lines. Normal
wrapping and the existing half-width/full-stop rule still apply.

The renderer measures the gap between non-empty caption updates using a
monotonic clock; this approximates speech pauses and includes recognition/network
delays. It does not use audio silence detection. Corrections and finalisation of
an outstanding partial stay with that hypothesis even if delayed; a pause break
previewed by a partial is committed only by its final. Empty/profanity-only
updates create no blank lines. Caption resets and font/width changes clear timing
history. The existing one-line scroll animation is used when the viewport moves.

This is implemented once in live-caption's shared renderer, so Cadenza uses the
same setting automatically. Legacy `bbc` and `rolling` layouts are unchanged.
Cadenza's existing eight-second caption expiry still clears very old text.

## Optional speaker colours for discussions

Speaker estimation (Speechmatics diarization) and displaying speaker colours are
independent settings. Estimation is **off by default**, and ordinary captions
remain white. Set session options in your existing caption YAML:

```yaml
speechmatics:
  diarization: speaker  # none disables estimation; default: none
  speaker_diarization_config:
    prefer_current_speaker: true
    # max_speakers: 3  # optional; counts EVERY speaker in the session, not just the panel
speakers:
  mode: white          # white or speakers; display default
  colours: ["#FFFFFF", "#FFE066", "#77DDF5", "#FFB3D9", "#A9E88B"]
  unknown_colour: "#FFFFFF"
```

Both CLIs accept `--diarization none|speaker` and `--speaker-colours white|speakers`;
these override the corresponding config fields at startup. For an event without
a panel, omit these settings or explicitly select `--diarization none`. For an
event with a panel, start estimation from the beginning but keep the display
white until the discussion. Changing estimation requires a new recognition
session; changing display mode does not restart recognition.

Speaker colours require `bbc_live`. Legacy `bbc` and `rolling` remain plain.
Confirmed words retain their individual speaker labels through profanity omission,
wrapping and scrolling. A confirmed speaker change starts a fresh line in colour
mode. Partials and unknown (`UU`/missing) labels stay neutral; a final can correct
a provisional line break. Such corrections snap rather than queueing scrolling.
The display toggle clears caption history so existing passages are not recoloured
or replayed. Font, measured width, line count and pause breaks keep their meanings.

IDs such as S1/S2/S3 map directly to palette positions, so a slide change, caption
expiry or display-mode reset does not change a known ID's colour. Additional IDs
cycle through the palette. IDs are anonymous estimates, not names, and a new
recognition session may assign them differently. Speaker identification accuracy
needs rehearsal with the venue audio, especially similar voices and interruptions.
No local voice model is run. Speaker labels are retained in raw recordings and
can be replayed; older recordings without labels continue working neutrally.

Parsing, filtering, colours, speaker-turn layout and structured caption data are
implemented once in live-caption. The AppKit overlay and Cadenza Qt view only
apply those shared colours to their native text controls. Caption text is escaped
before Qt styled-text rendering. The existing JSON bridge `kind`/`text` fields
remain, with an additional `runs` list carrying text and speaker labels.

Start with estimation available but white presentation captions:

```sh
uv run cadenza --live --diarization speaker
```

The operator's **Speaker colours** control has **AUTO / WHITE / SPEAKERS**.
AUTO follows each slide's `speaker_colours` boolean (defaulting to the global
`speakers.mode`, which is white). WHITE and SPEAKERS override it across slides.
This control is separate from captions AUTO/ON/OFF; it never reveals captions
on a slide where captions are hidden. It is unavailable during live sessions
started without estimation, and in legacy layouts. Restart with estimation
enabled to use it. Demo/replay allow the control without contacting Speechmatics.

Mark a discussion slide in your show YAML:

```yaml
- id: panel
  kind: mc
  title: Panel discussion
  captions: true
  speaker_colours: true
```

Omit `speaker_colours` or use false for presenter slides. See
`config/panel.example.yaml` for a minimal presenter/panel programme; the existing
concert programme is unchanged. Slide navigation, expiry, caption overrides and
font/width changes reset displayed text while retaining the ID-to-colour mapping.
