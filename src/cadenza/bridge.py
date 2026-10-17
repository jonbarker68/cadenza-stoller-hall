"""Process-only adapter for live-caption's existing source/replay workers.

Runs using live-caption's interpreter; never imports its overlay or GUI.
Stdout is a JSON-lines protocol, with library output redirected to stderr.

With --raw, send processed partial/final events for measured rendering in the Qt
presentation process. Without it, retain the rendered-caption protocol for
older consumers. The native live-caption overlay is never imported.
"""

import contextlib
import json
from pathlib import Path
import queue
import signal
import sys


def main():
    root, config_path, replay_path = sys.argv[1:4]
    raw_output = "--raw" in sys.argv[4:]
    sys.path.insert(0, str(Path(root) / "src"))

    protocol = sys.stdout

    def emit(kind, text):
        protocol.write(
            json.dumps({"kind": kind, "text": text}) + "\n"
        )
        protocol.flush()

    with contextlib.redirect_stdout(sys.stderr):
        from live_caption.config import load_config
        from live_caption.recording import ReplayWorker
        from live_caption.processor import CaptionProcessor
        from live_caption.renderers import make_renderer

        config = load_config(config_path)
        processor = CaptionProcessor(config)

        # Renderer selection lives in the overlay section, but the renderer
        # itself needs the complete caption configuration (e.g. config["bbc"]).
        overlay_config = config.get("overlay", {})
        layout = overlay_config.get("layout", "rolling")

        # Preserve the complete configuration while also making overlay
        # settings available at top level, as they are in live-caption's
        # resolved overlay configuration.
        renderer_config = dict(config)
        renderer_config.update(overlay_config)

        renderer = None if raw_output else make_renderer(layout, renderer_config)

        raw = queue.Queue()
        status = queue.Queue()

        if replay_path:
            worker = ReplayWorker(replay_path, raw, status)
        else:
            from live_caption.asr import SpeechmaticsWorker

            worker = SpeechmaticsWorker(raw, status, config)

        signal.signal(signal.SIGTERM, lambda *_: worker.stop())
        worker.start()

        try:
            while True:
                while not status.empty():
                    kind, text = status.get_nowait()
                    emit(kind, text)

                try:
                    event = raw.get(timeout=0.05)
                except queue.Empty:
                    continue

                if event is None:
                    while not status.empty():
                        kind, text = status.get_nowait()
                        emit(kind, text)
                    break

                output = processor.process(event)
                if output is None:
                    continue
                kind, text = output
                if raw_output:
                    emit(kind, text)
                elif kind == "partial":
                    emit(
                        "caption",
                        renderer.update_partial(text),
                    )

                elif kind == "final":
                    emit(
                        "caption",
                        renderer.add_final(text),
                    )

        finally:
            worker.stop()
            worker.join(timeout=2)


if __name__ == "__main__":
    main()
