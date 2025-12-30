"""
API Configuration Module for NewCo
Loads API keys from a secure config file.

Usage:
    from api_config import load_api_keys

    keys = load_api_keys()
    attom_key = keys['ATTOM_API_KEY']
    rentcast_key = keys['RENTCAST_API_KEY']
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


# Config file search paths (in priority order)
CONFIG_PATHS = [
    Path('/mnt/c/Users/mbklu/.config/newco/api_keys.json'),  # WSL mount of Windows
    Path.home() / '.config' / 'newco' / 'api_keys.json',     # Linux home (~)
    Path('/home/user/.config/newco/api_keys.json'),          # /home/user fallback
    Path('/home/claude/.config/newco/api_keys.json'),        # /home/claude fallback
]

# Default config dir for writing new keys
CONFIG_DIR = Path.home() / '.config' / 'newco'
API_KEYS_FILE = CONFIG_DIR / 'api_keys.json'


def _find_config_file() -> Optional[Path]:
    """Find the first existing config file from the search paths."""
    for path in CONFIG_PATHS:
        if path.exists():
            return path
    return None


def load_api_keys() -> Dict[str, str]:
    """
    Load API keys from environment variables or config file.

    Priority:
    1. Environment variables (ATTOM_API_KEY, RENTCAST_API_KEY, etc.)
    2. Config file from multiple paths (WSL mount, home dir, fallbacks)

    Returns:
        Dict containing API keys

    Raises:
        FileNotFoundError: If no config source found
    """
    config = {}

    # Priority 1: Check environment variables
    env_keys = ['ATTOM_API_KEY', 'RENTCAST_API_KEY', 'GOOGLE_MAPS_API_KEY', 'BRAVE_SEARCH_API_KEY']
    for key in env_keys:
        env_value = os.environ.get(key)
        if env_value:
            config[key] = env_value

    # If we have the essential keys from env, return early
    if 'ATTOM_API_KEY' in config and 'RENTCAST_API_KEY' in config:
        return config

    # Priority 2: Try config files in order
    config_file = _find_config_file()
    if config_file:
        with open(config_file, 'r', encoding='utf-8') as f:
            file_config = json.load(f)
            # Merge file config (env vars take precedence)
            for k, v in file_config.items():
                if k not in config:
                    config[k] = v
        return config

    # No config found
    if not config:
        paths_tried = '\n  '.join(str(p) for p in CONFIG_PATHS)
        raise FileNotFoundError(
            f"API keys not found. Tried:\n  {paths_tried}\n"
            f"Or set environment variables: ATTOM_API_KEY, RENTCAST_API_KEY"
        )

    return config


def get_api_key(key_name: str) -> Optional[str]:
    """
    Get API key from environment variable or config file.

    Checks:
    1. Environment variable (e.g., ATTOM_API_KEY)
    2. Config files at multiple paths (WSL mount, home dir, fallbacks)

    Args:
        key_name: Name of the key (e.g., 'ATTOM_API_KEY', 'RENTCAST_API_KEY')

    Returns:
        The API key value, or None if not found
    """
    # Try environment variable first
    env_value = os.environ.get(key_name)
    if env_value:
        return env_value

    # Try config files in order
    config_file = _find_config_file()
    if not config_file:
        return None

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return config_data.get(key_name)

    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in {config_file}: {e}")
        return None
    except Exception as e:
        print(f"Warning: Error reading {config_file}: {e}")
        return None


def update_api_key(key_name: str, key_value: str) -> None:
    """
    Update or add an API key to the config file.

    Args:
        key_name: Name of the key to update
        key_value: New value for the key
    """
    # Load existing config or create new one
    if API_KEYS_FILE.exists():
        with open(API_KEYS_FILE, 'r') as f:
            config = json.load(f)
    else:
        config = {}

    # Update the key
    config[key_name] = key_value
    config['last_updated'] = '2025-11-24'

    # Ensure directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Save updated config
    with open(API_KEYS_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    # Set secure permissions (owner read/write only)
    os.chmod(API_KEYS_FILE, 0o600)

    print(f"✓ Updated {key_name} in {API_KEYS_FILE}")


def list_api_keys() -> None:
    """Print all configured API keys (masked for security)."""
    try:
        keys = load_api_keys()
        print("\nConfigured API Keys:")
        print("-" * 40)
        for key, value in keys.items():
            if key.endswith('_API_KEY'):
                # Mask the key value for security
                masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                print(f"  {key}: {masked}")
            else:
                print(f"  {key}: {value}")
        print("-" * 40)
    except FileNotFoundError:
        print("No API keys configured yet.")


if __name__ == '__main__':
    # Test the module
    print("Testing API Configuration Module")
    print("=" * 40)
    list_api_keys()
