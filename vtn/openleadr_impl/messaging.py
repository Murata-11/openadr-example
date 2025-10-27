from openleadr import utils, errors

from openleadr_impl.utils import utils as myUtils


async def authenticate_message(
    request,
    message_tree,
    message_payload,
    fingerprint_lookup=None,
    ven_lookup=None,
):
    if "ven_id" in message_payload:
        connection_fingerprint = myUtils.get_certificate_fingerprint_from_alb_header(
            request
        )
        if connection_fingerprint is None:
            msg = (
                "Your request must use a client side SSL certificate, of which the "
                "fingerprint must match the fingerprint that you have given to this VTN."
            )
            raise errors.NotRegisteredOrAuthorizedError(msg)

        try:
            ven_id = message_payload.get("ven_id")
            if fingerprint_lookup:
                expected_fingerprint = await utils.await_if_required(
                    fingerprint_lookup(ven_id)
                )
                if not expected_fingerprint:
                    raise ValueError
            elif ven_lookup:
                ven_info = await utils.await_if_required(ven_lookup(ven_id))
                if not ven_info:
                    raise ValueError
                expected_fingerprint = ven_info.get("fingerprint")
        except ValueError:
            msg = (
                f"Your venID {ven_id} is not known to this VTN. Make sure you use the venID "
                "that you receive from this VTN during the registration step"
            )
            raise errors.NotRegisteredOrAuthorizedError(msg)

        if expected_fingerprint is None:
            msg = (
                "This VTN server does not know what your certificate fingerprint is. Please "
                "deliver your fingerprint to the VTN (outside of OpenADR). You used the "
                "following fingerprint to make this request:"
            )
            raise errors.NotRegisteredOrAuthorizedError(msg)

        if connection_fingerprint != expected_fingerprint:
            msg = (
                f"The fingerprint of your HTTPS certificate '{connection_fingerprint}' "
                f"does not match the expected fingerprint '{expected_fingerprint}'"
            )
            raise errors.NotRegisteredOrAuthorizedError(msg)
