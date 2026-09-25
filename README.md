# Cadenza · Stoller Hall

A standalone macOS presentation app for an operator-led orchestral listening experiment. Two PySide6/QML windows share a YAML-driven sequence. The included programme is an example; passage A, page 3, and all wording must be replaced with the real event content.

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

The audience view uses the title/body, experiment passage/page, response ring and digital countdown, and caption band. Music slides are presentation states: they do not play audio or cue external equipment. Use short titles/body text and rehearse the actual content on the venue display.

## Architecture and checks

`model.py` validates YAML and owns monotonic timers. `app.py` exposes shared state to two QML windows. `bridge.py` runs in a separate process, importing only existing live-caption ASR/config/recording modules, and sends JSON-lines events to the presentation. No existing live-caption files are changed, no overlay UI is loaded, and caption credentials remain in the local configuration or environment. This adapter currently renders raw partial/final transcripts; it does not apply live-caption's optional text-processing filters.

```sh
PYTHONPATH=src /Users/jon/projects/live-caption/.venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src QT_QPA_PLATFORM=offscreen /Users/jon/projects/live-caption/.venv/bin/python -m cadenza.app --smoke-test
```

Live microphone/Speechmatics authentication and a physical second monitor need an on-site rehearsal. The first pass is a source-based application, not a signed macOS app bundle.

## Second-section music timer

The `countup` slide type displays a large digital audience timer with captions off in AUTO mode in the example programme. It opens at `00:00` and stays stopped while the MC explains. Press **Start** when the conductor begins; it then counts upwards with no duration limit. Minutes continue past 59 (for example, `60:00`); there is no ring or automatic advancement.

The shared **Timer** row controls either timer type. **Start** begins, **Pause** holds, and **Resume** continues the same run. **Stop** holds the final value; the second button then becomes **Restart**, which immediately begins a fresh run from zero (count-up) or the configured duration (countdown). The first button is disabled after Stop or countdown completion. Leaving the slide discards its timer; returning resets it and waits for Start. There is no separate whole-event elapsed timer.

```yaml
- id: music-2
  kind: countup
  title: Listening experiment · 02
  body: Please listen to the orchestra.
  captions: false
```
