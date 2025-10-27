import asyncio
from http import HTTPStatus
from aiohttp.test_utils import make_mocked_request
from aiohttp import web
import pytest

from openleadr_impl.service.vtn_service import MyVTNService

pytest_plugins = ("aiohttp.pytest_plugin",)


@pytest.fixture
def imports_monkeypatch(monkeypatch):
    """
    MyVTNService モジュール内の外部依存を差し替える
    """
    import openleadr_impl.service.vtn_service as m

    class _Hooks:
        @staticmethod
        def call(*args, **kwargs):
            return None

    monkeypatch.setattr(m, "hooks", _Hooks(), raising=False)

    monkeypatch.setattr(
        m, "validate_xml_schema", lambda content: "<ok/>", raising=False
    )

    async def _auth(*args, **kwargs):
        return None

    monkeypatch.setattr(m, "authenticate_message", _auth, raising=False)

    def _parse_message(content):
        return "oadrQueryRegistration", {
            "request_id": "req-1",
            "ven_id": "ven-1",
            "vtn_id": "VTN-X",
        }

    monkeypatch.setattr(m, "parse_message", _parse_message, raising=False)

    class _Utils:
        @staticmethod
        async def await_if_required(x):
            if asyncio.iscoroutine(x):
                return await x
            return x

    monkeypatch.setattr(m, "utils", _Utils, raising=False)

    class _MyUtils:
        @staticmethod
        def get_certificate_fingerprint_from_alb_header(request):
            return "fp:ALB"

    monkeypatch.setattr(m, "myUtils", _MyUtils, raising=False)

    return m


@pytest.fixture
def app_factory(imports_monkeypatch, monkeypatch):
    # テスト用にサーバーを起動
    async def _make_app(vtn_id="vtn_001"):
        svc = MyVTNService(vtn_id=vtn_id)

        svc.ven_lookup = ven_lookup

        app = web.Application()
        app.router.add_post("/", svc.handler)
        return app

    return _make_app


# テスト用のモック関数
def ven_lookup(ven_id):
    return ven_id


@pytest.mark.asyncio
async def test_異常系_ContentTypeの不正(app_factory, aiohttp_client):
    app = await app_factory()
    client = await aiohttp_client(app)

    resp = await client.post(
        "/", data=b"<xml/>", headers={"Content-Type": "text/plain"}
    )
    assert resp.status == HTTPStatus.BAD_REQUEST
    txt = await resp.text()
    assert "The Content-Type header must be application/xml;" in txt


@pytest.mark.asyncio
async def test_異常系_oadrResponseを受信(
    imports_monkeypatch, app_factory, aiohttp_client, monkeypatch
):
    # parse_message を oadrResponse に差し替え
    monkeypatch.setattr(
        imports_monkeypatch,
        "parse_message",
        lambda c: ("oadrResponse", {}),
        raising=False,
    )

    app = await app_factory()
    client = await aiohttp_client(app)
    resp = await client.post(
        "/", data=b"<xml/>", headers={"Content-Type": "application/xml"}
    )
    assert resp.status == HTTPStatus.OK
    assert (await resp.text()) == ""


@pytest.mark.asyncio
async def test_異常系_vtnIDが異なる(
    imports_monkeypatch, app_factory, aiohttp_client, monkeypatch
):
    monkeypatch.setattr(
        imports_monkeypatch,
        "parse_message",
        lambda c: ("anyType", {"ven_id": "ven-1", "vtn_id": "OTHER"}),
        raising=False,
    )

    app = await app_factory()
    client = await aiohttp_client(app)
    resp = await client.post(
        "/", data=b"<xml/>", headers={"Content-Type": "application/xml"}
    )
    txt = await resp.text()
    # 200 OK（OpenADR メッセージで返す仕様）
    assert resp.status == HTTPStatus.OK
