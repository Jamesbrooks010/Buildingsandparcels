"""Dependency-free local web preview for Adelaide Site Finder."""

from __future__ import annotations

import argparse
import json
import mimetypes
import socket
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .engine import find_candidate_sites
from .gpkg_loader import dataset_info, load_candidate_parcels
from .models import BuildingEnvelope, Parcel

STATIC_DIR = Path(__file__).with_name("static")
EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


class ExclusiveThreadingHTTPServer(ThreadingHTTPServer):
    """Prevent stale and current previews from silently sharing one port."""

    allow_reuse_address = False
    allow_reuse_port = False

    def server_bind(self) -> None:
        exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
        if exclusive is not None:
            self.socket.setsockopt(socket.SOL_SOCKET, exclusive, 1)
        super().server_bind()


class SiteFinderHandler(BaseHTTPRequestHandler):
    """Serve the preview application and its small JSON API."""

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlparse(self.path).path
        if path == "/api/examples":
            self._send_json(
                {
                    "parcels": _load_json(EXAMPLES_DIR / "sample_parcels.json"),
                    "townhouse": _load_json(EXAMPLES_DIR / "envelope_townhouse.json"),
                    "apartment": _load_json(EXAMPLES_DIR / "envelope_apartment.json"),
                    "mixed_use": _load_json(EXAMPLES_DIR / "envelope_mixed_use.json"),
                }
            )
            return
        if path == "/api/dataset":
            self._send_json(dataset_info())
            return

        relative_path = "index.html" if path == "/" else path.lstrip("/")
        requested = (STATIC_DIR / relative_path).resolve()
        if STATIC_DIR.resolve() not in requested.parents and requested != STATIC_DIR.resolve():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not requested.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
        body = requested.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if urlparse(self.path).path != "/api/candidates":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            envelope = BuildingEnvelope.model_validate(payload["envelope"])
            if payload.get("use_local_dataset", True):
                parcels, total_matches = load_candidate_parcels(
                    envelope, limit=int(payload.get("limit", 100))
                )
            else:
                parcels = [Parcel.model_validate(item) for item in payload["parcels"]]
                total_matches = len(parcels)
            results = find_candidate_sites(parcels, envelope)
            self._send_json(
                {
                    "results": [asdict(result) for result in results],
                    "total_matches": total_matches,
                    "returned": len(results),
                }
            )
        except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[site-finder] {format % args}")


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Adelaide Site Finder web preview.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    try:
        server = ExclusiveThreadingHTTPServer((args.host, args.port), SiteFinderHandler)
    except OSError as exc:
        raise SystemExit(
            f"Cannot start Adelaide Site Finder on http://{args.host}:{args.port}: "
            "the address is already in use. Stop the older preview or choose another --port."
        ) from exc
    print(f"Adelaide Site Finder preview: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
