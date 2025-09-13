#!/usr/bin/env python3
"""
Version management script for SIP AI Agent.
Handles version bumping, tagging, and Docker image versioning.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def get_current_version() -> str:
    """Get the current version from pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        return "0.1.0"

    with open(pyproject_path, "r") as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if match:
            return match.group(1)
    return "0.1.0"


def update_version_file(new_version: str) -> None:
    """Update version in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        print("Warning: pyproject.toml not found, skipping version update")
        return

    with open(pyproject_path, "r") as f:
        content = f.read()

    # Update version in pyproject.toml
    updated_content = re.sub(
        r'version = "[^"]+"', f'version = "{new_version}"', content
    )

    with open(pyproject_path, "w") as f:
        f.write(updated_content)

    print(f"Updated version in pyproject.toml to {new_version}")


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semantic version string into tuple of integers."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-.*)?$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch = parse_version(current_version)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def create_git_tag(version: str, message: Optional[str] = None) -> None:
    """Create a git tag for the version."""
    tag_name = f"v{version}"
    tag_message = message or f"Release version {version}"

    try:
        # Check if tag already exists
        result = subprocess.run(
            ["git", "tag", "-l", tag_name], capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            print(f"Tag {tag_name} already exists")
            return

        # Create the tag
        subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_message], check=True)
        print(f"Created tag {tag_name}")

    except subprocess.CalledProcessError as e:
        print(f"Error creating git tag: {e}")
        sys.exit(1)


def push_tag(version: str) -> None:
    """Push the git tag to remote."""
    tag_name = f"v{version}"

    try:
        subprocess.run(["git", "push", "origin", tag_name], check=True)
        print(f"Pushed tag {tag_name} to remote")
    except subprocess.CalledProcessError as e:
        print(f"Error pushing tag: {e}")
        sys.exit(1)


def get_docker_images_info(version: str) -> dict:
    """Get information about Docker images for the version."""
    registry = "ghcr.io"
    repo_name = os.environ.get("GITHUB_REPOSITORY", "sip-ai-agent")

    return {
        "registry": registry,
        "repository": repo_name,
        "version": version,
        "images": {
            "sip_agent": f"{registry}/{repo_name}:{version}",
            "sip_agent_latest": f"{registry}/{repo_name}:latest",
            "web_ui": f"{registry}/{repo_name}-web:{version}",
            "web_ui_latest": f"{registry}/{repo_name}-web:latest",
        },
    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Version management for SIP AI Agent")
    parser.add_argument(
        "action", choices=["current", "bump", "tag", "info"], help="Action to perform"
    )
    parser.add_argument(
        "--type",
        choices=["major", "minor", "patch"],
        help="Version bump type (for bump action)",
    )
    parser.add_argument("--version", help="Specific version to use (for tag action)")
    parser.add_argument("--message", help="Tag message (for tag action)")
    parser.add_argument(
        "--push", action="store_true", help="Push tag to remote (for tag action)"
    )

    args = parser.parse_args()

    if args.action == "current":
        version = get_current_version()
        print(f"Current version: {version}")

    elif args.action == "bump":
        if not args.type:
            print("Error: --type is required for bump action")
            sys.exit(1)

        current_version = get_current_version()
        new_version = bump_version(current_version, args.type)
        update_version_file(new_version)
        print(f"Bumped version from {current_version} to {new_version}")

    elif args.action == "tag":
        if args.version:
            version = args.version
        else:
            version = get_current_version()

        create_git_tag(version, args.message)

        if args.push:
            push_tag(version)

    elif args.action == "info":
        current_version = get_current_version()
        docker_info = get_docker_images_info(current_version)
        print("Docker Images Information:")
        print(json.dumps(docker_info, indent=2))


if __name__ == "__main__":
    main()
