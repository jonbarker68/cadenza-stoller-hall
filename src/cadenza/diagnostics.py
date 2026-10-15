"""Bounded operational logs; caption transcripts are deliberately not recorded."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re


class RedactingFormatter(logging.Formatter):
    def __init__(self, secrets=()):
        super().__init__('%(asctime)s %(levelname)s %(message)s')
        self.secrets = tuple(str(s) for s in secrets if s)

    def format(self, record):
        text = super().format(record)
        for secret in self.secrets:
            text = text.replace(secret, '[REDACTED]')
        text = re.sub(r'(?i)(bearer\s+)[^\s\"\']+', r'\1[REDACTED]', text)
        text = re.sub(r"(?i)((?:api[_-]?key|token|password|secret)[\"']?\s*[:=]\s*[\"']?)[^\s,\"'}]+", r'\1[REDACTED]', text)
        return text


def configure_logging(directory, secrets=()):
    path = Path(directory).expanduser().resolve() / 'cadenza.log'
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('cadenza')
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    formatter = RedactingFormatter(secrets)
    file_handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=3, encoding='utf-8')
    console = logging.StreamHandler()
    for handler in (file_handler, console):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return path


def configured_secrets(config_path):
    """Read secret values only for redaction; never log the configuration."""
    import os
    import yaml
    secrets = [os.environ.get('SPEECHMATICS_API_KEY', '')]
    def collect(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if re.search(r'api.?key|token|password|secret', str(key), re.I) and isinstance(item, str):
                    secrets.append(item)
                else:
                    collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
    try:
        with open(config_path, encoding='utf-8') as stream:
            collect(yaml.safe_load(stream))
    except (OSError, yaml.YAMLError):
        pass
    return secrets
