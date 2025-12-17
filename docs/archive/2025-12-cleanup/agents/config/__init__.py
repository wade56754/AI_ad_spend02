"""
Flow Preset Configuration Loader

Loads YAML preset configurations for OrchestratorAgent flows.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml
import logging

logger = logging.getLogger(__name__)

# Default config directory
_CONFIG_DIR = Path(__file__).parent


def load_preset(preset_name: str, config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a flow preset by name.

    Searches for preset in all YAML files in config directory.

    Args:
        preset_name: Name of the preset (e.g., "finance_profit_backend_full")
        config_dir: Optional config directory (defaults to agents/config/)

    Returns:
        Preset configuration dict with flow, task, module, target_files, etc.

    Raises:
        ValueError: If preset not found
        FileNotFoundError: If config directory doesn't exist
    """
    config_dir = config_dir or _CONFIG_DIR

    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    # Search all YAML files in config directory
    for yaml_file in config_dir.glob("*.yaml"):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data or "flows" not in data:
                    continue

                flows = data.get("flows", {})
                if preset_name in flows:
                    preset = flows[preset_name].copy()
                    logger.info(f"Loaded preset '{preset_name}' from {yaml_file.name}")
                    return preset

        except Exception as e:
            logger.warning(f"Failed to load {yaml_file}: {e}")
            continue

    raise ValueError(
        f"Preset '{preset_name}' not found in {config_dir}. "
        f"Available presets: {list_available_presets(config_dir)}"
    )


def list_available_presets(config_dir: Optional[Path] = None) -> list[str]:
    """
    List all available preset names.

    Args:
        config_dir: Optional config directory (defaults to agents/config/)

    Returns:
        List of preset names
    """
    config_dir = config_dir or _CONFIG_DIR
    presets = []

    if not config_dir.exists():
        return presets

    for yaml_file in config_dir.glob("*.yaml"):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "flows" in data:
                    presets.extend(data["flows"].keys())
        except Exception as e:
            logger.warning(f"Failed to parse {yaml_file}: {e}")
            continue

    return sorted(presets)


def merge_preset_with_overrides(
    preset: Dict[str, Any],
    overrides: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merge preset configuration with CLI overrides.

    Overrides take precedence over preset values.

    Args:
        preset: Preset configuration dict
        overrides: CLI argument overrides

    Returns:
        Merged configuration dict
    """
    merged = preset.copy()

    # Merge overrides (overrides take precedence)
    for key, value in overrides.items():
        if value is not None:
            if key == "target_files" and isinstance(value, list):
                # For target_files, merge lists (preserve order: preset first, then overrides)
                existing = merged.get("target_files", [])
                merged["target_files"] = existing + value
            else:
                merged[key] = value

    return merged

