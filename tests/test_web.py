import json
import pytest
import threading
import urllib.request

from site_finder.web import ExclusiveThreadingHTTPServer, SiteFinderHandler


def test_preview_serves_home_and_screens_examples():
    server = ExclusiveThreadingHTTPServer(("127.0.0.1", 0), SiteFinderHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(base_url) as response:
            home = response.read()
            assert b"Find the right site" in home
            assert b"Connected parcel dataset" in home
            assert b"Two sample parcels" in home

        with urllib.request.urlopen(f"{base_url}/api/examples") as response:
            examples = json.load(response)
        assert examples["mixed_use"]["building_height_m"] == 11
        assert "not Planning Atlas controls" in examples["mixed_use"]["assumptions"]["screening_note"]
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
        assert payload["results"][0]["status"] == "pass"
    finally:
        server.shutdown()
        thread.join()


def test_preview_refuses_to_share_an_active_port():
    first = ExclusiveThreadingHTTPServer(("127.0.0.1", 0), SiteFinderHandler)
    try:
        with pytest.raises(OSError):
            ExclusiveThreadingHTTPServer(
                ("127.0.0.1", first.server_port), SiteFinderHandler
            )
    finally:
        first.server_close()
