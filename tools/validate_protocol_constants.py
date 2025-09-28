#!/usr/bin/env python3
"""
BitTorrent Protocol Constants Validation Tool

Validates that DFakeSeeder's protocol constants match the official
BitTorrent protocol specifications (BEP-003 and related).
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path to import from d_fake_seeder
sys.path.insert(0, str(Path(__file__).parent.parent))

from d_fake_seeder.domain.torrent.bittorrent_message import BitTorrentMessage


# Official BitTorrent Protocol message types as defined in BEP-003
# https://www.bittorrent.org/beps/bep_0003.html
OFFICIAL_BITTORRENT_MESSAGES = {
    # Core protocol messages (BEP-003)
    "CHOKE": 0,
    "UNCHOKE": 1,
    "INTERESTED": 2,
    "NOT_INTERESTED": 3,
    "HAVE": 4,
    "BITFIELD": 5,
    "REQUEST": 6,
    "PIECE": 7,
    "CANCEL": 8,
    # DHT extension (BEP-005)
    "PORT": 9,
    # Extended protocol (BEP-010)
    "EXTENDED": 20,
}

# Additional protocol constants that should be stable
EXPECTED_USER_AGENTS = ["Deluge", "qBittorrent", "Transmission", "uTorrent", "Vuze", "BitTorrent", "rTorrent"]

EXPECTED_PIECE_SIZES = [
    16384,  # 16KB - common default
    32768,  # 32KB - maximum typical
    262144,  # 256KB - large files
    524288,  # 512KB - very large files
]


def validate_bittorrent_constants():
    """Validate BitTorrent protocol message constants."""
    print("=" * 60)
    print("VALIDATING BITTORRENT PROTOCOL CONSTANTS")
    print("=" * 60)

    errors = []
    warnings = []

    # Check each official message type
    for msg_name, expected_value in OFFICIAL_BITTORRENT_MESSAGES.items():
        if hasattr(BitTorrentMessage, msg_name):
            actual_value = getattr(BitTorrentMessage, msg_name)
            if actual_value != expected_value:
                errors.append(f"❌ {msg_name}: expected {expected_value}, got {actual_value}")
            else:
                print(f"✅ {msg_name}: {actual_value} (correct)")
        else:
            errors.append(f"❌ Missing constant: {msg_name}")

    # Check for unexpected constants
    for attr_name in dir(BitTorrentMessage):
        if not attr_name.startswith("_") and attr_name not in OFFICIAL_BITTORRENT_MESSAGES:
            attr_value = getattr(BitTorrentMessage, attr_name)
            if isinstance(attr_value, int):
                warnings.append(f"⚠️  Unexpected constant: {attr_name} = {attr_value}")

    return errors, warnings


def validate_user_agents():
    """Validate user agent strings for compatibility."""
    print("\n" + "=" * 60)
    print("VALIDATING USER AGENT COMPATIBILITY")
    print("=" * 60)

    try:
        # Try to load user agents from configuration
        from d_fake_seeder.domain.config.default import default_config

        agents = default_config.get("agents", [])
    except ImportError:
        # Fallback: try to read from JSON file
        import json

        config_path = Path(__file__).parent.parent / "d_fake_seeder" / "domain" / "config" / "default.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                agents = config.get("agents", [])
        else:
            print("❌ Could not load user agent configuration")
            return ["Could not load user agent configuration"], []

    errors = []
    warnings = []

    print(f"Found {len(agents)} configured user agents:")

    for agent in agents:
        print(f"  • {agent}")

        # Check if major clients are represented
        for expected_client in EXPECTED_USER_AGENTS:
            if any(expected_client.lower() in agent.lower() for agent in agents):
                continue
            else:
                warnings.append(f"⚠️  Missing user agent for: {expected_client}")

    # Validate agent string format
    for agent in agents:
        if "," not in agent:
            warnings.append(f"⚠️  Agent missing peer ID: {agent}")
        elif not agent.split(",")[1].startswith("-"):
            warnings.append(f"⚠️  Invalid peer ID format: {agent}")

    return errors, warnings


def validate_piece_sizes():
    """Validate piece size constants."""
    print("\n" + "=" * 60)
    print("VALIDATING PIECE SIZE CONSTANTS")
    print("=" * 60)

    try:
        from d_fake_seeder.lib.util.constants import DEFAULT_PIECE_SIZE, MAX_PIECE_SIZE

        errors = []
        warnings = []

        print(f"Default piece size: {DEFAULT_PIECE_SIZE} bytes")
        print(f"Maximum piece size: {MAX_PIECE_SIZE} bytes")

        # Validate default piece size
        if DEFAULT_PIECE_SIZE not in EXPECTED_PIECE_SIZES:
            warnings.append(f"⚠️  Unusual default piece size: {DEFAULT_PIECE_SIZE}")
        else:
            print(f"✅ Default piece size {DEFAULT_PIECE_SIZE} is standard")

        # Validate maximum piece size
        if MAX_PIECE_SIZE < DEFAULT_PIECE_SIZE:
            errors.append(f"❌ Max piece size ({MAX_PIECE_SIZE}) < default ({DEFAULT_PIECE_SIZE})")
        elif MAX_PIECE_SIZE > 1048576:  # 1MB
            warnings.append(f"⚠️  Very large max piece size: {MAX_PIECE_SIZE}")
        else:
            print(f"✅ Maximum piece size {MAX_PIECE_SIZE} is reasonable")

        return errors, warnings

    except ImportError as e:
        return [f"Could not import piece size constants: {e}"], []


def validate_port_ranges():
    """Validate network port ranges."""
    print("\n" + "=" * 60)
    print("VALIDATING PORT RANGES")
    print("=" * 60)

    try:
        import json

        config_path = Path(__file__).parent.parent / "d_fake_seeder" / "domain" / "config" / "default.json"

        if not config_path.exists():
            return ["Default configuration file not found"], []

        with open(config_path, "r") as f:
            config = json.load(f)

        errors = []
        warnings = []

        # Check BitTorrent listening port
        listening_port = config.get("listening_port", 6881)
        print(f"BitTorrent listening port: {listening_port}")

        if listening_port < 1024:
            warnings.append(f"⚠️  Privileged port: {listening_port}")
        elif listening_port > 65535:
            errors.append(f"❌ Invalid port: {listening_port}")
        elif 6881 <= listening_port <= 6889:
            print(f"✅ Standard BitTorrent port range: {listening_port}")
        else:
            warnings.append(f"⚠️  Non-standard BitTorrent port: {listening_port}")

        # Check seeder port ranges
        seeders_config = config.get("seeders", {})
        port_min = seeders_config.get("port_range_min", 1025)
        port_max = seeders_config.get("port_range_max", 65000)

        print(f"Seeder port range: {port_min}-{port_max}")

        if port_min < 1024:
            warnings.append(f"⚠️  Privileged ports in range: {port_min}")
        if port_max > 65535:
            errors.append(f"❌ Invalid max port: {port_max}")
        if port_min >= port_max:
            errors.append(f"❌ Invalid port range: {port_min}-{port_max}")
        else:
            print(f"✅ Valid seeder port range: {port_min}-{port_max}")

        # Check WebUI port
        webui_port = config.get("webui_port", 8080)
        print(f"WebUI port: {webui_port}")

        if webui_port == listening_port:
            errors.append(f"❌ WebUI port conflicts with BitTorrent port: {webui_port}")
        elif webui_port < 1024:
            warnings.append(f"⚠️  Privileged WebUI port: {webui_port}")
        else:
            print(f"✅ Valid WebUI port: {webui_port}")

        return errors, warnings

    except Exception as e:
        return [f"Error validating port ranges: {e}"], []


def main():
    """Run all protocol validation checks."""
    print("DFakeSeeder Protocol Constants Validation")
    print("=" * 60)

    all_errors = []
    all_warnings = []

    # Run all validation checks
    validators = [validate_bittorrent_constants, validate_user_agents, validate_piece_sizes, validate_port_ranges]

    for validator in validators:
        try:
            errors, warnings = validator()
            all_errors.extend(errors)
            all_warnings.extend(warnings)
        except Exception as e:
            all_errors.append(f"❌ Validation error in {validator.__name__}: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    if all_errors:
        print(f"❌ {len(all_errors)} ERRORS found:")
        for error in all_errors:
            print(f"   {error}")

    if all_warnings:
        print(f"⚠️  {len(all_warnings)} WARNINGS found:")
        for warning in all_warnings:
            print(f"   {warning}")

    if not all_errors and not all_warnings:
        print("✅ All protocol constants validated successfully!")
    elif not all_errors:
        print("✅ No critical errors found. All protocol constants are stable.")

    print(f"\nValidation completed: {len(all_errors)} errors, {len(all_warnings)} warnings")

    # Exit with appropriate code
    if all_errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
