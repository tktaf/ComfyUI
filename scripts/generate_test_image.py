#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib import error, request

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SERVER = "http://127.0.0.1:8188"
DEFAULT_WORKFLOW = REPO_ROOT / "workflows" / "dreamshaper_xl_coach_portrait_api.json"
BASE_DIRS = {
    "output": REPO_ROOT / "output",
    "temp": REPO_ROOT / "temp",
    "input": REPO_ROOT / "input",
}


def get_json(url: str) -> dict:
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_server(server: str, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            get_json(f"{server}/system_stats")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"ComfyUI server did not become ready at {server}: {last_error}")


def extract_output_paths(history_item: dict) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for node_output in history_item.get("outputs", {}).values():
        for items in node_output.values():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                filename = item.get("filename")
                if item_type not in BASE_DIRS or not filename:
                    continue
                subfolder = item.get("subfolder") or ""
                path = (BASE_DIRS[item_type] / subfolder / filename).resolve()
                if path not in seen:
                    seen.add(path)
                    paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Queue a ComfyUI API workflow and wait for output files.")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="ComfyUI server base URL")
    parser.add_argument("--workflow", default=str(DEFAULT_WORKFLOW), help="Path to API workflow JSON")
    parser.add_argument("--timeout", type=int, default=3600, help="Overall timeout in seconds")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="History poll interval in seconds")
    parser.add_argument("--seed", type=int, default=None, help="Optional override for node 3 seed")
    parser.add_argument("--output-prefix", default=None, help="Optional override for SaveImage filename_prefix")
    args = parser.parse_args()

    workflow_path = Path(args.workflow).resolve()
    if not workflow_path.is_file():
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

    with workflow_path.open("r", encoding="utf-8") as handle:
        prompt = json.load(handle)

    if args.seed is not None:
        prompt["3"]["inputs"]["seed"] = args.seed
    if args.output_prefix is not None:
        prompt["9"]["inputs"]["filename_prefix"] = args.output_prefix

    wait_for_server(args.server.rstrip("/"), min(args.timeout, 300))
    response = post_json(f"{args.server.rstrip('/')}/prompt", {"prompt": prompt})
    prompt_id = response.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI did not return a prompt_id: {response}")

    deadline = time.time() + args.timeout
    history_url = f"{args.server.rstrip('/')}/history/{prompt_id}"
    while time.time() < deadline:
        history_response = get_json(history_url)
        history_item = history_response.get(prompt_id)
        if history_item:
            output_paths = extract_output_paths(history_item)
            if output_paths:
                for path in output_paths:
                    print(path)
                return 0
        time.sleep(args.poll_interval)

    raise TimeoutError(f"Timed out waiting for prompt {prompt_id} to finish")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {message}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
