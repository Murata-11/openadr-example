from openleadr.service import service, handler
import logging

from openleadr_impl.service.vtn_service import MyVTNService

logger = logging.getLogger("openleadr")


@service("EiOpt")
class OptService(MyVTNService):

    def __init__(self, vtn_id):
        super().__init__(vtn_id)
        self.created_opt_schedules = {}

    @handler("oadrCreateOpt")
    async def create_opt(self, payload):
        """
        Handle an opt schedule created by the VEN
        """

        pass  # TODO: call handler and return the result (oadrCreatedOpt)

    def on_create_opt(self, payload):
        """
        Implementation of the on_create_opt handler, may be overwritten by the user.
        """
        ven_id = payload["ven_id"]

        if payload["ven_id"] not in self.created_opt_schedules:
            self.created_opt_schedules[ven_id] = []

        # TODO: internally create an opt schedule and save it, if this is an optional handler then make sure to handle None returns

        return "oadrCreatedOpt", {"opt_id": payload["opt_id"]}

    @handler("oadrCancelOpt")
    async def cancel_opt(self, payload):
        """
        Cancel an opt schedule previously created by the VEN
        """
        ven_id = payload["ven_id"]
        opt_id = payload["opt_id"]

        pass  # TODO: call handler and return result (oadrCanceledOpt)

    def on_cancel_opt(self, ven_id, opt_id):
        """
        Placeholder for the on_cancel_opt handler.
        """

        # TODO: implement cancellation of previously acknowledged opt schedule, if this is an optional handler make sure to hande None returns

        return "oadrCanceledOpt", {"opt_id": opt_id}
