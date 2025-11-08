from http import HTTPStatus
from unittest.mock import AsyncMock, Mock
import pytest
from lxml.etree import XMLSyntaxError

from openleadr import errors

from openleadr_impl.service import vtn_service
from openleadr_impl.service.vtn_service import MyVTNService


class DummyRequest:
    def __init__(self, headers, body=b""):
        self.headers = headers
        self._body = body

    async def read(self):
        return self._body


class TestMyVTNServiceHandler:
    @pytest.mark.asyncio
    async def test_handler_rejects_non_xml_content_type(self):
        service = MyVTNService(vtn_id="test-vtn")

        # server.pyで注入されるペイロード作成関数をモック化
        service._create_message = lambda *_args, **_kwargs: "<xml/>"
        request = DummyRequest(headers={"content-type": "text/plain"})

        response = await service.handler(request)

        assert response.status == HTTPStatus.BAD_REQUEST
        assert "application/xml" in response.text

    @pytest.mark.asyncio
    async def test_handler_xml_failed_validation(self, monkeypatch):
        service = MyVTNService(vtn_id="test-vtn")
        request = DummyRequest(
            headers={"content-type": "application/xml"}, body=b"<bad/>"
        )

        def raise_xml_error(_content):
            raise XMLSyntaxError("Invalid XML", 0, 0, 0)

        parse_mock = Mock()

        monkeypatch.setattr(vtn_service, "validate_xml_schema", raise_xml_error)
        monkeypatch.setattr(vtn_service, "parse_message", parse_mock)

        response = await service.handler(request)

        assert response.status == HTTPStatus.BAD_REQUEST
        assert "XML failed validation" in response.text
        parse_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_handler_fingerprintMismatch(self, monkeypatch):
        service = MyVTNService(vtn_id="test-vtn")
        service._create_message = lambda *_args, **_kwargs: "<xml/>"
        service.handle_message = AsyncMock()
        service.ven_lookup = AsyncMock(return_value={"registration_id": "reg-1"})

        request = DummyRequest(
            headers={"content-type": "application/xml"}, body=b"<oadr/>"
        )

        monkeypatch.setattr(
            vtn_service, "validate_xml_schema", lambda _content: "mocked-tree"
        )
        monkeypatch.setattr(
            vtn_service, "parse_message", lambda _content: ("oadrPoll", {"ven_id": "ven-123"})
        )

        def raise_fingerprint(_request, _tree, _payload, **_kwargs):
            raise errors.FingerprintMismatch("fingerprint mismatch")

        monkeypatch.setattr(vtn_service, "authenticate_message", raise_fingerprint)

        response = await service.handler(request)

        assert response.status == HTTPStatus.FORBIDDEN
        assert "fingerprint mismatch" in response.text.lower()
        service.handle_message.assert_not_called()
        service.ven_lookup.assert_awaited_once_with(ven_id="ven-123")

    @pytest.mark.asyncio
    async def test_handler_message_type_oadrResponse(self, monkeypatch):
        service = MyVTNService(vtn_id="test-vtn")
        service._create_message = lambda *_args, **_kwargs: "<xml/>"
        service.handle_message = AsyncMock()

        auth_mock = AsyncMock()

        request = DummyRequest(
            headers={"content-type": "application/xml"}, body=b"<oadr/>"
        )

        def mock_parse(_content):
            return "oadrResponse", {"ven_id": "ven-123"}

        monkeypatch.setattr(
            vtn_service, "validate_xml_schema", lambda _content: "mocked-tree"
        )
        monkeypatch.setattr(vtn_service, "parse_message", mock_parse)
        monkeypatch.setattr(vtn_service, "authenticate_message", auth_mock)

        response = await service.handler(request)

        assert response.status == HTTPStatus.OK
        assert response.text == ""
        service.handle_message.assert_not_called()
        auth_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_handler_mismatch_vtn_id(self, monkeypatch):
        service = MyVTNService(vtn_id="expected-vtn")
        service._create_message = lambda *_args, **_kwargs: "<xml/>"
        service.handle_message = AsyncMock()
        service.error_response = Mock(
            return_value=("oadrError", {"response": {"response_code": 459}})
        )

        auth_mock = AsyncMock()
        monkeypatch.setattr(
            vtn_service, "validate_xml_schema", lambda _content: "mocked-tree"
        )

        def mock_parse(_content):
            return "oadrPoll", {
                "ven_id": "ven-123",
                "vtn_id": "wrong-vtn",
            }

        monkeypatch.setattr(vtn_service, "parse_message", mock_parse)
        monkeypatch.setattr(vtn_service, "authenticate_message", auth_mock)

        request = DummyRequest(headers={"content-type": "application/xml"}, body=b"")

        response = await service.handler(request)

        assert response.status == HTTPStatus.OK
        assert response.text == "<xml/>"
        service.handle_message.assert_not_called()
        auth_mock.assert_not_called()
        service.error_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_ven_lookup_result_is_none(self, monkeypatch):
        service = MyVTNService(vtn_id="test-vtn")
        service._create_message = lambda *_args, **_kwargs: "<xml/>"
        service.handle_message = AsyncMock()
        service.error_response = Mock(
            return_value=("oadrError", {"response": {"response_code": 452}})
        )
        service.ven_lookup = AsyncMock(return_value=None)

        auth_mock = AsyncMock()

        monkeypatch.setattr(
            vtn_service, "validate_xml_schema", lambda _content: "mocked-tree"
        )

        def mock_parse(_content):
            return "oadrPoll", {"ven_id": "ven-123"}

        monkeypatch.setattr(vtn_service, "parse_message", mock_parse)
        monkeypatch.setattr(vtn_service, "authenticate_message", auth_mock)

        request = DummyRequest(headers={"content-type": "application/xml"}, body=b"")

        response = await service.handler(request)

        assert response.status == HTTPStatus.OK
        service.ven_lookup.assert_awaited_once_with(ven_id="ven-123")
        service.handle_message.assert_not_called()
        auth_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_handler_ven_lookup_registration_id_is_none(
        self, monkeypatch
    ):
        service = MyVTNService(vtn_id="test-vtn")
        service._create_message = lambda *_args, **_kwargs: "<xml/>"
        service.handle_message = AsyncMock()
        service.error_response = Mock(
            return_value=("oadrError", {"response": {"response_code": 452}})
        )
        service.ven_lookup = AsyncMock(return_value={"registration_id": None})

        auth_mock = AsyncMock()

        monkeypatch.setattr(
            vtn_service, "validate_xml_schema", lambda _content: "mocked-tree"
        )

        def mock_parse(_content):
            return "oadrPoll", {"ven_id": "ven-123"}

        monkeypatch.setattr(vtn_service, "parse_message", mock_parse)
        monkeypatch.setattr(vtn_service, "authenticate_message", auth_mock)

        request = DummyRequest(headers={"content-type": "application/xml"}, body=b"")

        response = await service.handler(request)

        assert response.status == HTTPStatus.OK
        service.ven_lookup.assert_awaited_once_with(ven_id="ven-123")
        service.handle_message.assert_not_called()
        auth_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_handler_success_oadrQueryRegistration(self, monkeypatch):
        fingerprint = "AA:BB"
        service = MyVTNService(vtn_id="test-vtn")
        service._create_message = lambda *_args, **_kwargs: "<xml/>"

        handle_mock = AsyncMock(
            return_value=("oadrCreatedPartyRegistration", {"registration_id": "reg-1"})
        )
        service.handle_message = handle_mock

        monkeypatch.setattr(
            vtn_service, "validate_xml_schema", lambda _content: "mocked-tree"
        )

        def mock_parse(_content):
            return "oadrQueryRegistration", {
                "ven_id": "ven-123",
                "request_id": "1",
            }

        monkeypatch.setattr(vtn_service, "parse_message", mock_parse)
        monkeypatch.setattr(
            vtn_service.myUtils,
            "get_certificate_fingerprint_from_alb_header",
            lambda _request: fingerprint,
        )

        auth_mock = AsyncMock()
        monkeypatch.setattr(vtn_service, "authenticate_message", auth_mock)

        request = DummyRequest(
            headers={
                "content-type": "application/xml",
                "X-Amzn-Mtls-Clientcert-Leaf": "dummy",
            },
            body=b"<oadr/>",
        )

        response = await service.handler(request)

        assert response.status == HTTPStatus.OK
        called_payload = handle_mock.await_args.args[1]
        assert called_payload["fingerprint"] == fingerprint
        auth_mock.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_handler_success_oadrCreatePartyRegistration(self, monkeypatch):
        fingerprint = "AA:BB"
        service = MyVTNService(vtn_id="test-vtn")
        service._create_message = lambda *_args, **_kwargs: "<xml/>"

        handle_mock = AsyncMock(
            return_value=("oadrCreatedPartyRegistration", {"registration_id": "reg-1"})
        )
        service.handle_message = handle_mock

        monkeypatch.setattr(
            vtn_service, "validate_xml_schema", lambda _content: "mocked-tree"
        )

        def mock_parse(_content):
            return "oadrCreatePartyRegistration", {
                "ven_id": "ven-123",
                "request_id": "1",
            }

        monkeypatch.setattr(vtn_service, "parse_message", mock_parse)
        monkeypatch.setattr(
            vtn_service.myUtils,
            "get_certificate_fingerprint_from_alb_header",
            lambda _request: fingerprint,
        )

        auth_mock = AsyncMock()
        monkeypatch.setattr(vtn_service, "authenticate_message", auth_mock)

        request = DummyRequest(
            headers={
                "content-type": "application/xml",
                "X-Amzn-Mtls-Clientcert-Leaf": "dummy",
            },
            body=b"<oadr/>",
        )

        response = await service.handler(request)

        assert response.status == HTTPStatus.OK
        called_payload = handle_mock.await_args.args[1]
        assert called_payload["fingerprint"] == fingerprint
        auth_mock.assert_not_called()


    @pytest.mark.asyncio
    async def test_handler_success_need_authenticates_ven(self, monkeypatch):
        service = MyVTNService(vtn_id="test-vtn")
        service._create_message = lambda *_args, **_kwargs: "<xml/>"

        handle_mock = AsyncMock(return_value=("oadrResponse", {"result": "ok"}))
        service.handle_message = handle_mock

        ven_lookup = AsyncMock(return_value={"registration_id": "reg-1"})
        service.ven_lookup = ven_lookup

        monkeypatch.setattr(
            vtn_service, "validate_xml_schema", lambda _content: "mocked-tree"
        )

        def fake_parse(_content):
            return "oadrPoll", {
                "ven_id": "ven-123",
            }

        monkeypatch.setattr(vtn_service, "parse_message", fake_parse)

        auth_mock = AsyncMock()
        monkeypatch.setattr(vtn_service, "authenticate_message", auth_mock)

        request = DummyRequest(
            headers={"content-type": "application/xml"},
            body=b"<oadr/>",
        )

        response = await service.handler(request)

        assert response.status == HTTPStatus.OK
        auth_mock.assert_awaited_once()
        assert auth_mock.await_args.kwargs["ven_lookup"] is ven_lookup
        ven_lookup.assert_awaited_once()
