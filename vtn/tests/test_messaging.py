import types
import pytest
from types import SimpleNamespace
from openleadr import errors, utils

from openleadr_impl.messaging import authenticate_message
from openleadr_impl.utils import utils as myUtils


@pytest.fixture(autouse=True)
def patch_await_if_required(monkeypatch):
    async def _await_if_required(value):
        if hasattr(value, "__await__") or isinstance(value, types.CoroutineType):
            return await value
        return value

    monkeypatch.setattr(utils, "await_if_required", _await_if_required)


@pytest.mark.asyncio
async def test_異常系_ヘッダーからフィンガープリントが取得できない(monkeypatch):
    monkeypatch.setattr(
        myUtils, "get_certificate_fingerprint_from_alb_header", lambda req: None
    )
    req = make_request(headers={})
    with pytest.raises(errors.NotRegisteredOrAuthorizedError):
        await authenticate_message(
            request=req, message_tree=None, message_payload={"ven_id": "VEN-1"}
        )


@pytest.mark.asyncio
async def test_異常系_登録済みのVEN情報からフィンガープリントが取得できない(
    monkeypatch, patch_await_if_required
):
    monkeypatch.setattr(
        myUtils,
        "get_certificate_fingerprint_from_alb_header",
        lambda req: "12:34:56:78:90",
    )

    req = make_request(headers={})
    with pytest.raises(errors.NotRegisteredOrAuthorizedError):
        await authenticate_message(
            request=req,
            message_tree=None,
            message_payload={"ven_id": "VEN-1"},
            ven_lookup=ven_lookup_異常系_登録済みのVEN情報からフィンガープリントが取得できない,
        )


def ven_lookup_異常系_登録済みのVEN情報からフィンガープリントが取得できない(ven_id):
    return {"ven_id": ven_id, "ven_name": "ven", "registration_id": "123"}


@pytest.mark.asyncio
async def test_異常系_登録済みのVEN情報のフィンガープリントとヘッダーのフィンガープリントが一致しない(
    monkeypatch, patch_await_if_required
):
    monkeypatch.setattr(
        myUtils,
        "get_certificate_fingerprint_from_alb_header",
        lambda req: "12:34:56:78:90",  # ヘッダーから取得したフィンガープリント
    )

    req = make_request(headers={})
    with pytest.raises(errors.NotRegisteredOrAuthorizedError):
        await authenticate_message(
            request=req,
            message_tree=None,
            message_payload={"ven_id": "VEN-1"},
            ven_lookup=ven_lookup_異常系_登録済みのVEN情報のフィンガープリントとヘッダーのフィンガープリントが一致しない,
        )


def ven_lookup_異常系_登録済みのVEN情報のフィンガープリントとヘッダーのフィンガープリントが一致しない(
    ven_id,
):
    return {
        "ven_id": ven_id,
        "ven_name": "ven",
        "fingerprint": "09:87:65:43:21",
        "registration_id": "123",
    }


@pytest.mark.asyncio
async def test_正常系(monkeypatch, patch_await_if_required):
    monkeypatch.setattr(
        myUtils,
        "get_certificate_fingerprint_from_alb_header",
        lambda req: "12:34:56:78:90",
    )

    req = make_request(headers={})
    await authenticate_message(
        request=req,
        message_tree=None,
        message_payload={"ven_id": "VEN-1"},
        ven_lookup=ven_lookup_正常系,
    )


def ven_lookup_正常系(ven_id):
    return {
        "ven_id": ven_id,
        "ven_name": "ven",
        "fingerprint": "12:34:56:78:90",
        "registration_id": "123",
    }


def make_request(headers: dict):
    return SimpleNamespace(headers=headers)
