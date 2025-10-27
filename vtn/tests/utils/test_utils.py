import base64
from http import HTTPStatus
import pytest
from types import SimpleNamespace
from openleadr import errors
from pathlib import Path

import urllib

from openleadr_impl.utils import utils


class TestGetCerificateFingerprintFromAlbHeader:

    def test_異常系_mTLSヘッダーが無い(self):
        req = make_request({"not-mtls-header": "example"})
        with pytest.raises(errors.HTTPError) as ei:
            utils.get_certificate_fingerprint_from_alb_header(req)
        assert ei.value.response_code == HTTPStatus.UNAUTHORIZED
        assert "Client certificate is missing. Mutual TLS authentication is required"

    def test_異常系_クライアント証明書が不正(self):
        req = make_request({"X-Amzn-Mtls-Clientcert-Leaf": "aa"})
        with pytest.raises(errors.HTTPError) as ei:
            utils.get_certificate_fingerprint_from_alb_header(req)
        assert ei.value.response_code == HTTPStatus.BAD_REQUEST
        assert "Invalid client certificate header" in ei.value.response_description

    def test_正常系_URLエンコードされた証明書(self):
        cert = load_url_encoding_cert()
        req = make_request({"X-Amzn-Mtls-Clientcert-Leaf": cert})

        result = utils.get_certificate_fingerprint_from_alb_header(req)
        # X.509 証明書（DER, whole cert）の SHA-256 フィンガープリントを'AA:BB:...' 形式（大文字HEX・コロン区切り）であること
        assert (
            result
            == "1F:0B:2A:34:91:A1:E6:9F:40:5E:5F:78:5F:A6:73:BF:BD:D8:A9:EC:C1:74:21:35:77:1D:0A:0E:AE:97:AB:34"
        )

    def test_正常系_URLエンコードされていない証明書(self):
        cert = load_plain_cert()
        req = make_request({"X-Amzn-Mtls-Clientcert-Leaf": cert})

        result = utils.get_certificate_fingerprint_from_alb_header(req)
        # X.509 証明書（DER, whole cert）の SHA-256 フィンガープリントを'AA:BB:...' 形式（大文字HEX・コロン区切り）であること
        assert (
            result
            == "1F:0B:2A:34:91:A1:E6:9F:40:5E:5F:78:5F:A6:73:BF:BD:D8:A9:EC:C1:74:21:35:77:1D:0A:0E:AE:97:AB:34"
        )


# 以下はヘルパー関数
def make_request(headers: dict):
    return SimpleNamespace(headers=headers)


def load_url_encoding_cert():
    p = Path("/workspaces/tests/utils/client_cert_for_test.crt")
    data = p.read_text(encoding="utf-8")
    url_encoded = urllib.parse.quote(data, safe="")
    return url_encoded


def load_plain_cert():
    p = Path("/workspaces/tests/utils/client_cert_for_test.crt")
    data = p.read_text(encoding="utf-8")
    return data
