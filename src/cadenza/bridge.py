"""Process-only adapter for live-caption's existing source/replay workers.

Runs using live-caption's interpreter; never imports its overlay or GUI.
Stdout is a JSON-lines protocol, with library output redirected to stderr.

Caption transcript rendering is delegated to live-caption's renderer
implementations so that layouts such as "rolling" and "bbc" behave exactly
as they do in live-caption.
"""

import contextlib
import json
from pathlib import Path
import queue
import signal
import sys


def main():
    root, config_path, replay_path = sys.argv[1:4]
    sys.path.insert(0, str(Path(root) / "src" / "live_caption"))

    protocol = sys.stdout

    def emit(kind, text):
        protocol.write(
            json.dumps({"kind": kind, "text": text}) + "\n"
        )
        protocol.flush()

    with contextlib.redirect_stdout(sys.stderr):
        from config import load_config
        from recording import ReplayWorker
        from renderers import make_renderer

        config = load_config(config_path)

        # Renderer selection lives in the overlay section, but the renderer
        # itself needs the complete caption configuration (e.g. config["bbc"]).
        overlay_config = config.get("overlay", {})
        layout = overlay_config.get("layout", "rolling")

        # Preserve the complete configuration while also making overlay
        # settings available at top level, as they are in live-caption's
        # resolved overlay configuration.
        renderer_config = dict(config)
        renderer_config.update(overlay_config)

        renderer = make_renderer(layout, renderer_config)

        raw = queue.Queue()
        status = queue.Queue()

        if replay_path:
            worker = ReplayWorker(replay_path, raw, status)
        else:
            from asr import SpeechmaticsWorker

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

                if event.kind == "partial":
                    emit(
                        "caption",
                        renderer.update_partial(event.text),
                    )

                elif event.kind == "final":
                    emit(
                        "caption",
                        renderer.add_final(event.text),
                    )
                else:
                    emit(event.kind, event.text)

        finally:
            worker.stop()
            worker.join(timeout=2)


if __name__ == "__main__":
    main()
