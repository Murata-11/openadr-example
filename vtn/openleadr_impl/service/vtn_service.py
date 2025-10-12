from http import HTTPStatus
import logging
import traceback
import hashlib

from urllib.parse import unquote
from aiohttp import web
from lxml.etree import XMLSyntaxError
from signxml.exceptions import InvalidSignature
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from openleadr import errors, hooks, utils
from openleadr.messaging import validate_xml_schema, parse_message, authenticate_message
from openleadr.service import VTNService

logger = logging.getLogger("openleadr")


class MyVTNService(VTNService):
    verify_message_signatures = False

    async def handler(self, request):
        """
        Handle all incoming POST requests.
        """
        try:
            # Check the Content-Type header
            content_type = request.headers.get("content-type", "")
            if not content_type.lower().startswith("application/xml"):
                raise errors.HTTPError(
                    response_code=HTTPStatus.BAD_REQUEST,
                    response_description="The Content-Type header must be application/xml; "
                    f"you provided {request.headers.get('content-type', '')}",
                )
            content = await request.read()
            hooks.call("before_parse", content)

            # Validate the message to the XML Schema
            message_tree = validate_xml_schema(content)

            # Parse the message to a type and payload dict
            message_type, message_payload = parse_message(content)

            if message_type == "oadrResponse":
                raise errors.SendEmptyHTTPResponse()

            if (
                "vtn_id" in message_payload
                and message_payload["vtn_id"] is not None
                and message_payload["vtn_id"] != self.vtn_id
            ):
                raise errors.InvalidIdError(
                    f"The supplied vtnID is invalid. It should be '{self.vtn_id}', "
                    f"you supplied {message_payload['vtn_id']}."
                )

            # Check if we know this VEN, ask for reregistration otherwise
            if (
                message_type
                not in ("oadrCreatePartyRegistration", "oadrQueryRegistration")
                and "ven_id" in message_payload
                and hasattr(self, "ven_lookup")
            ):
                result = await utils.await_if_required(
                    self.ven_lookup(ven_id=message_payload["ven_id"])
                )
                if result is None or result.get("registration_id", None) is None:
                    raise errors.RequestReregistration(message_payload["ven_id"])

            # Authenticate the message
            if "ven_id" in message_payload:
                if hasattr(self, "fingerprint_lookup"):
                    await authenticate_message(
                        request,
                        message_tree,
                        message_payload,
                        fingerprint_lookup=self.fingerprint_lookup,
                        verify_message_signature=self.verify_message_signatures,
                    )
                elif hasattr(self, "ven_lookup"):
                    await authenticate_message(
                        request,
                        message_tree,
                        message_payload,
                        ven_lookup=self.ven_lookup,
                        verify_message_signature=self.verify_message_signatures,
                    )
                else:
                    logger.error(
                        "Could not authenticate this VEN because "
                        "you did not provide a 'ven_lookup' function. Please see "
                        "https://openleadr.org/docs/server.html#signing-messages for info."
                    )

            # Pass the message off to the handler and get the response type and payload
            try:
                # Add the request fingerprint to the message so that the handler can check for it.
                if message_type == "oadrCreatePartyRegistration":
                    # message_payload['fingerprint'] = utils.get_cert_fingerprint_from_request(request)
                    message_payload['fingerprint'] = self.aa(request)
                    print(message_payload['fingerprint'])
                response_type, response_payload = await self.handle_message(
                    message_type, message_payload
                )
            except Exception as err:
                logger.error(
                    "An exception occurred during the execution of your "
                    f"{self.__class__.__name__} handler: "
                    f"{err.__class__.__name__}: {err}"
                )
                raise err

            if "response" not in response_payload:
                response_payload["response"] = {
                    "response_code": 200,
                    "response_description": "OK",
                    "request_id": message_payload.get("request_id"),
                }
            response_payload["vtn_id"] = self.vtn_id
            if "ven_id" not in response_payload:
                response_payload["ven_id"] = message_payload.get("ven_id")
        except errors.RequestReregistration as err:
            response_type = "oadrRequestReregistration"
            response_payload = {"ven_id": err.ven_id}
            msg = self._create_message(response_type, **response_payload)
            response = web.Response(
                text=msg, status=HTTPStatus.OK, content_type="application/xml"
            )
        except errors.SendEmptyHTTPResponse:
            response = web.Response(
                text="", status=HTTPStatus.OK, content_type="application/xml"
            )
        except errors.ProtocolError as err:
            # In case of an OpenADR error, return a valid OpenADR message
            response_type, response_payload = self.error_response(
                message_type, err.response_code, err.response_description
            )
            msg = self._create_message(response_type, **response_payload)
            response = web.Response(
                text=msg, status=HTTPStatus.OK, content_type="application/xml"
            )
        except errors.HTTPError as err:
            # If we throw a http-related error, deal with it here
            response = web.Response(
                text=err.response_description, status=err.response_code
            )
        except XMLSyntaxError as err:
            logger.warning(f"XML schema validation of incoming message failed: {err}.")
            response = web.Response(
                text=f"XML failed validation: {err}", status=HTTPStatus.BAD_REQUEST
            )
        except errors.FingerprintMismatch as err:
            logger.warning(err)
            response = web.Response(text=str(err), status=HTTPStatus.FORBIDDEN)
        except InvalidSignature:
            logger.warning("Incoming message had invalid signature, ignoring.")
            response = web.Response(
                text="Invalid Signature", status=HTTPStatus.FORBIDDEN
            )
        except Exception as err:
            # In case of some other error, return a HTTP 500
            logger.error(
                f"The VTN server encountered an error: {err.__class__.__name__}: {err}"
            )
            logger.error(traceback.format_exc())
            response = web.Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)
        else:
            # We've successfully handled this message
            msg = self._create_message(response_type, **response_payload)
            response = web.Response(
                text=msg, status=HTTPStatus.OK, content_type="application/xml"
            )
        hooks.call("before_respond", response.text)
        return response

    def aa(self, request):
        leaf_enc = request.headers.get("X-Amzn-Mtls-Clientcert-Leaf")
        if not leaf_enc:
            return web.Response(text="no client cert", status=400)

        # 1) URLデコード → PEMテキスト
        leaf_pem = unquote(leaf_enc).encode("utf-8")

        # 2) PEMを読み込んでDERに
        cert = x509.load_pem_x509_certificate(leaf_pem)
        der = cert.public_bytes(Encoding.DER)

        # 3) 指紋を計算
        return self.certificate_fingerprint_from_der(der)

    def certificate_fingerprint_from_der(self, der_bytes: bytes) -> str:
        """X.509 DER の SHA-256 フィンガープリントを 'AA:BB:...' 形式で返す"""
        h = hashlib.sha256(der_bytes).digest()
        return ":".join(f"{b:02X}" for b in h)