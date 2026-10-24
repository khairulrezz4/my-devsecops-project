"""Validate immutable GitHub Actions references and tracked JSON files."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
USES_PATTERN = re.compile(r"^\s*uses:\s*([^\s#]+)")
WORKFLOW_SUFFIXES = (".yml", ".yaml")


def tracked_files(pattern: str) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--", pattern],
        check=True,
        capture_output=True,
        text=True,
    )
    return [path for line in result.stdout.splitlines() if line and (path := Path(line)).exists()]


def validate_json() -> None:
    failures: list[str] = []
    for path in tracked_files("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"{path}: invalid JSON ({error})")
    if failures:
        raise SystemExit("\n".join(failures))
    print("JSON validation passed.")


def verify_commit(repository: str, commit: str) -> None:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "pipeline-validator"}

    def get_object(object_type: str) -> dict:
        url = f"https://api.github.com/repos/{repository}/git/{object_type}/{commit}"
        request = Request(url, headers=headers)
        with urlopen(request, timeout=15) as response:
            if response.status != 200:
                raise SystemExit(f"{repository}@{commit}: GitHub returned HTTP {response.status}")
            return json.load(response)

    try:
        get_object("commits")
    except HTTPError as error:
        if error.code not in (404, 422):
            raise SystemExit(f"{repository}@{commit}: commit could not be verified ({error})") from error
        try:
            tag = get_object("tags")
        except (HTTPError, URLError, TimeoutError) as tag_error:
            raise SystemExit(f"{repository}@{commit}: commit or annotated tag could not be verified ({tag_error})") from tag_error
        if tag.get("object", {}).get("type") != "commit":
            raise SystemExit(f"{repository}@{commit}: reference does not resolve to a commit")
    except (HTTPError, URLError, TimeoutError) as error:
        raise SystemExit(f"{repository}@{commit}: commit could not be verified ({error})") from error


def validate_references() -> None:
    references: set[tuple[str, str]] = set()
    failures: list[str] = []
    workflow_files = [
        path
        for path in tracked_files("*")
        if path.suffix in WORKFLOW_SUFFIXES
        and (".github" in path.parts or "test" in path.parts)
    ]

    for path in workflow_files:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = USES_PATTERN.match(line)
            if not match:
                continue
            target = match.group(1)
            if target.startswith("./"):
                if "@" in target:
                    failures.append(f"{path}:{line_number}: local action/workflow must not include a ref")
                elif not Path(target).exists():
                    failures.append(f"{path}:{line_number}: local action/workflow does not exist: {target}")
                continue
            if "@" not in target:
                failures.append(f"{path}:{line_number}: action/workflow reference is missing a commit SHA")
                continue
            repository_path, commit = target.split("@", 1)
            repository_parts = repository_path.split("/")
            if len(repository_parts) < 2 or not SHA_PATTERN.fullmatch(commit):
                failures.append(f"{path}:{line_number}: reference is not pinned to a full 40-character SHA: {target}")
                continue
            references.add(("/".join(repository_parts[:2]), commit))

    if failures:
        raise SystemExit("\n".join(failures))
    for repository, commit in sorted(references):
        verify_commit(repository, commit)
    print(f"Verified {len(references)} immutable action/workflow commit reference(s).")


def main() -> int:
    validate_json()
    validate_references()
    return 0


if __name__ == "__main__":
    sys.exit(main())
