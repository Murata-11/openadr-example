# SPDX-License-Identifier: Apache-2.0

# Copyright 2020 Contributors to OpenLEADR

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from aiohttp import web
from openleadr.messaging import create_message
from openleadr import utils, OpenADRServer
from functools import partial
from datetime import timedelta
import logging
import ssl

from openleadr_impl.service.event_service import EventService
from openleadr_impl.service.poll_service import PollService
from openleadr_impl.service.registration_service import RegistrationService
from openleadr_impl.service.report_service import ReportService
from openleadr_impl.service.vtn_service import MyVTNService

logger = logging.getLogger("openleadr")


class MyOpenADRServer(OpenADRServer):
    _MAP = {
        "on_created_event": "event_service",
        "on_request_event": "event_service",
        "on_register_report": "report_service",
        "on_create_report": "report_service",
        "on_created_report": "report_service",
        "on_request_report": "report_service",
        "on_update_report": "report_service",
        "on_poll": "poll_service",
        "on_query_registration": "registration_service",
        "on_create_party_registration": "registration_service",
        "on_cancel_party_registration": "registration_service",
    }

    def __init__(
        self,
        vtn_id,
        cert=None,
        key=None,
        passphrase=None,
        fingerprint_lookup=None,
        show_fingerprint=True,
        http_port=8080,
        http_host="127.0.0.1",
        http_cert=None,
        http_key=None,
        http_key_passphrase=None,
        http_path_prefix="/OpenADR2/Simple/2.0b",
        requested_poll_freq=timedelta(seconds=10),
        http_ca_file=None,
        ven_lookup=None,
        verify_message_signatures=True,
        show_server_cert_domain=True,
    ):
        """
        Create a new OpenADR VTN (Server).

        :param str vtn_id: An identifier string for this VTN. This is how you identify yourself
                              to the VENs that talk to you.
        :param str cert: Path to the PEM-formatted certificate file that is used to sign outgoing
                            messages
        :param str key: Path to the PEM-formatted private key file that is used to sign outgoing
                           messages
        :param str passphrase: The passphrase used to decrypt the private key file
        :param callable fingerprint_lookup: A callable that receives a ven_id and should return the
                                            registered fingerprint for that VEN. You should receive
                                            these fingerprints outside of OpenADR and configure them
                                            manually.
        :param bool show_fingerprint: Whether to print the fingerprint to your stdout on startup.
                                         Defaults to True.
        :param int http_port: The port that the web server is exposed on (default: 8080)
        :param str http_host: The host or IP address to bind the server to (default: 127.0.0.1).
        :param str http_cert: The path to the PEM certificate for securing HTTP traffic.
        :param str http_key: The path to the PEM private key for securing HTTP traffic.
        :param str http_ca_file: The path to the CA-file that client certificates are checked against.
        :param str http_key_passphrase: The passphrase for the HTTP private key.
        :param ven_lookup: A callback that takes a ven_id and returns a dict containing the
                           ven_id, ven_name, fingerprint and registration_id.
        :param verify_message_signatures: Whether to verify message signatures.
        """
        # Set up the message queues

        self.app = web.Application()
        self.services = {}

        # Globally enable or disable the verification of message
        # signatures. Only used in combination with TLS.
        MyVTNService.verify_message_signatures = verify_message_signatures

        # Create the separate OpenADR services
        self.services["event_service"] = EventService(vtn_id)
        self.services["report_service"] = ReportService(vtn_id)
        self.services["poll_service"] = PollService(vtn_id)
        self.services["registration_service"] = RegistrationService(
            vtn_id, poll_freq=requested_poll_freq
        )

        # Register the other services with the poll service
        self.services["poll_service"].event_service = self.services["event_service"]
        self.services["poll_service"].report_service = self.services["report_service"]

        # Set up the HTTP handlers for the services
        http_path_prefix = http_path_prefix.rstrip("/")
        self.app.add_routes(
            [
                web.post(f"{http_path_prefix}/{s.__service_name__}", s.handler)
                for s in self.services.values()
            ]
        )

        # Add a reference to the openadr VTN to the aiohttp 'app'
        self.app["server"] = self

        # Configure the web server
        self.http_port = http_port
        self.http_host = http_host
        self.http_path_prefix = http_path_prefix

        # Create SSL context for running the server
        if http_cert and http_key and http_ca_file:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ssl_context.load_verify_locations(http_ca_file)
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            self.ssl_context.load_cert_chain(http_cert, http_key, http_key_passphrase)
        else:
            self.ssl_context = None

        # Configure message signing
        if cert and key:
            with open(cert, "rb") as file:
                cert = file.read()
            with open(key, "rb") as file:
                key = file.read()
            if show_fingerprint:
                print("")
                print("*" * 80)
                print(
                    "Your VTN Certificate Fingerprint is "
                    f"{utils.certificate_fingerprint(cert)}".center(80)
                )
                print(
                    "Please deliver this fingerprint to the VENs that connect to you.".center(
                        80
                    )
                )
                print("You do not need to keep this a secret.".center(80))
                if show_server_cert_domain:
                    print("")
                    print(
                        "The VTN Certificate is valid for the following domain(s):".center(
                            80
                        )
                    )
                    print(utils.certificate_domain(cert).center(80))
                print("*" * 80)
                print("")
        MyVTNService._create_message = partial(
            create_message, cert=cert, key=key, passphrase=passphrase
        )
        if fingerprint_lookup is not None:
            logger.warning(
                "DeprecationWarning: the argument 'fingerprint_lookup' is deprecated and "
                "is replaced by 'ven_lookup'. 'fingerprint_lookup' will be removed in a "
                "future version of OpenLEADR. Please see "
                "https://openleadr.org/docs/server.html#things-you-should-implement."
            )
            MyVTNService.fingerprint_lookup = staticmethod(fingerprint_lookup)
        if ven_lookup is None:
            logger.warning(
                "If you provide a 'ven_lookup' to your OpenADRServer() init, OpenLEADR can "
                "automatically issue ReregistrationRequests for VENs that don't exist in "
                "your system. Please see https://openleadr.org/docs/server.html#things-you-should-implement."
            )
        else:
            MyVTNService.ven_lookup = staticmethod(ven_lookup)
        self.__setattr__ = self.add_handler
