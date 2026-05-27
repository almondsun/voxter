from __future__ import annotations

import pytest

from voxter.capture.portal import (
    PortalScreenCastStream,
    _expected_request_handle,
    _load_gio_glib,
    parse_portal_streams,
)
from voxter.contracts import CaptureRecordError


class FakeVariant:
    def __init__(self, value: object) -> None:
        self.value = value

    def unpack(self) -> object:
        return self.value


def test_parse_portal_streams_accepts_variant_properties() -> None:
    streams = parse_portal_streams(
        [
            (
                42,
                {
                    "size": FakeVariant((1920, 1080)),
                    "source_type": FakeVariant(1),
                },
            )
        ]
    )

    assert streams == (
        PortalScreenCastStream(
            node_id=42,
            properties={"size": (1920, 1080), "source_type": 1},
        ),
    )


@pytest.mark.parametrize("streams", [[], [(0, {})], [(42, [])], ["bad"]])
def test_parse_portal_streams_rejects_invalid_shapes(streams: object) -> None:
    with pytest.raises(CaptureRecordError):
        parse_portal_streams(streams)


def test_expected_request_handle_matches_portal_sender_token_shape() -> None:
    assert (
        _expected_request_handle(":1.100", "create_abc")
        == "/org/freedesktop/portal/desktop/request/1_100/create_abc"
    )


def test_load_gio_glib_reports_missing_pygobject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_import_module(name: str) -> object:
        if name == "gi":
            raise ModuleNotFoundError("No module named 'gi'")
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(
        "voxter.capture.portal.importlib.import_module", fake_import_module
    )

    with pytest.raises(CaptureRecordError, match="PyGObject"):
        _load_gio_glib()
