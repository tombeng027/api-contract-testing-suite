"""Explicit-only assertion failure used by the lifecycle regression."""

import httpx


def test_owned_server_cleanup_after_failure(client: httpx.Client) -> None:
    assert client.get("/health").status_code == 200
    assert False, "M1_FIXTURE_FAILURE_PROBE"
