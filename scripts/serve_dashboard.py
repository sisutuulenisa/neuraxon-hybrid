#!/usr/bin/env python3
"""Serve the Neuraxon dashboard over HTTP for LAN/Tailscale access."""

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Neuraxon dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8787, help="Bind port (default: 8787)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)

    server = ThreadingHTTPServer((args.host, args.port), SimpleHTTPRequestHandler)
    print(f"Serving {project_root} on http://{args.host}:{args.port}")
    print("Open dashboard at /dashboard/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")


if __name__ == "__main__":
    main()
