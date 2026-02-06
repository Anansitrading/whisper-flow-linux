"""Configuration management for WhisperFlow."""

import os
import yaml

DEFAULT_CONFIG = {
    "hotkey": "ctrl+shift",
    "model": "base.en",
    "compute_type": "int8",
    "audio_device": "auto",
    "sample_rate": 16000,
    "typing_delay_ms": 10,
    "prepend_space": True,
    "min_duration": 0.3,
    "language": "en",
}

CONFIG_DIR = os.path.expanduser("~/.config/whisperflow")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.yaml")


def load_config(config_path=None):
    """Load config from file, falling back to defaults."""
    config = DEFAULT_CONFIG.copy()

    path = config_path or CONFIG_PATH
    if os.path.exists(path):
        with open(path) as f:
            user_config = yaml.safe_load(f) or {}
        config.update(user_config)
    else:
        # Create default config file
        ensure_config_exists()

    return config


def ensure_config_exists():
    """Create default config file if it doesn't exist."""
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
