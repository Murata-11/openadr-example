from openleadr.service import service, handler
from openleadr import objects
import asyncio
from dataclasses import asdict
import logging

from openleadr_impl.service.vtn_service import MyVTNService

logger = logging.getLogger("openleadr")


@service("OadrPoll")
class PollService(MyVTNService):

    def __init__(
        self, vtn_id, polling_method="internal", event_service=None, report_service=None
    ):
        super().__init__(vtn_id)
        self.polling_method = polling_method
        self.events_updated = {}
        self.report_requests = {}
        self.event_service = event_service
        self.report_service = report_service

    @handler("oadrPoll")
    async def poll(self, payload):
        """
        Handle the request to the oadrPoll service. This either calls a previously registered
        `on_poll` handler, or it retrieves the next message from the internal queue.
        """
        if self.polling_method == "external":
            result = self.on_poll(ven_id=payload["ven_id"])
        elif self.events_updated.get(payload["ven_id"]):
            # Send a oadrDistributeEvent whenever the events were updated
            result = await self.event_service.request_event(
                {"ven_id": payload["ven_id"]}
            )
            self.events_updated[payload["ven_id"]] = False
        else:
            return "oadrResponse", {}

        if asyncio.iscoroutine(result):
            result = await result
        if result is None:
            return "oadrResponse", {}
        if isinstance(result, tuple):
            return result
        if isinstance(result, list):
            return "oadrDistributeEvent", result
        if isinstance(result, dict) and "event_descriptor" in result:
            return "oadrDistributeEvent", {"events": [result]}
        if isinstance(result, objects.Event):
            return "oadrDistributeEvent", {"events": [asdict(result)]}
        logger.warning(
            f"Could not determine type of message in response to oadrPoll: {result}"
        )
        return "oadrResponse", result

    def on_poll(self, ven_id):
        """
        Placeholder for the on_poll handler.
        """
        logger.warning(
            "You should implement and register your own on_poll handler that "
            "returns the next message for the VEN. This handler receives the "
            "ven_id as its argument, and should return None (if no messages "
            "are available), an Event or list of Events, a RequestReregistration "
            " or RequestReport."
        )
        return None
