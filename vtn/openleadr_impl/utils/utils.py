from http import HTTPStatus
import hashlib

from urllib.parse import unquote
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from openleadr import errors


def get_certificate_fingerprint_from_alb_header(request):
    """
    ALBのmTLSヘッダー（X-Amzn-Mtls-Clientcert-Leaf）からクライアント証明書のフィンガープリントを取得して返す。
    フィンガープリント:  SHA-256 'AA:BB:...' 形式（大文字HEX・コロン区切り）
    """
    leaf_enc = request.headers.get("X-Amzn-Mtls-Clientcert-Leaf")
    if not leaf_enc:
        raise errors.HTTPError(
            status=HTTPStatus.UNAUTHORIZED,
            description="Client certificate is missing. Mutual TLS authentication is required",
        )

    try:
        # 1) URLデコード → PEMテキスト
        leaf_pem = unquote(leaf_enc).encode("utf-8")

        # 2) PEMを読み込んでDERに
        cert = x509.load_pem_x509_certificate(leaf_pem)
        der = cert.public_bytes(Encoding.DER)

        # 3) 指紋を計算
        h = hashlib.sha256(der).digest()
    except Exception:
        raise errors.HTTPError(
            status=HTTPStatus.BAD_REQUEST,
            description="Invalid client certificate header",
        )

    return ":".join(f"{b:02X}" for b in h)
