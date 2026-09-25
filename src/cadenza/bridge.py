"""Process-only adapter for live-caption's existing source/replay workers.

Runs using live-caption's interpreter; never imports its overlay or GUI.
Stdout is a JSON-lines protocol, with library output redirected to stderr.
"""
import contextlib
import json
from pathlib import Path
import queue
import signal
import sys


def main():
    root, config_path, replay_path = sys.argv[1:4]
    sys.path.insert(0, str(Path(root) / 'src' / 'live_caption'))
    protocol = sys.stdout
    def emit(kind, text):
        protocol.write(json.dumps({'kind': kind, 'text': text}) + '\n')
        protocol.flush()
    with contextlib.redirect_stdout(sys.stderr):
        from config import load_config
        from recording import ReplayWorker
        raw, status = queue.Queue(), queue.Queue()
        if replay_path:
            worker = ReplayWorker(replay_path, raw, status)
        else:
            from asr import SpeechmaticsWorker
            worker = SpeechmaticsWorker(raw, status, load_config(config_path))
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
                emit(event.kind, event.text)
        finally:
            worker.stop()
            worker.join(timeout=2)


if __name__ == '__main__':
    main()
