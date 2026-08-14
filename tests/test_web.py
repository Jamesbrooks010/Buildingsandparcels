import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from site_finder.web import SiteFinderHandler


def test_preview_serves_home_and_screens_examples():
    server = ThreadingHTTPServer(("127.0.0.1", 0), SiteFinderHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(base_url) as response:
            assert b"Find the right site" in response.read()

        with urllib.request.urlopen(f"{base_url}/api/examples") as response:
            examples = json.load(response)
        request = urllib.request.Request(
            f"{base_url}/api/candidates",
            data=json.dumps(
                {
                    "envelope": examples["townhouse"],
                    "parcels": examples["parcels"],
                    "use_local_dataset": False,
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            payload = json.load(response)
        assert len(payload["results"]) == 2
        assert payload["results"][0]["parcel"]["parcel_id"] == "sample-001"
    finally:
        server.shutdown()
        thread.join()
