# ven.py
import os
import asyncio
from datetime import timedelta
from openleadr import OpenADRClient, enable_default_logging

enable_default_logging()

VTN_URL  = os.getenv("VTN_URL", "https://openadr-web:443/OpenADR2/Simple/2.0b")

CERT_FILE = os.getenv("CERT_FILE", "/certs/ven-client.crt")
KEY_FILE  = os.getenv("KEY_FILE",  "/certs/ven-client.key")
CA_FILE   = os.getenv("CA_FILE",   "/certs/ca.pem")


async def collect_value():
    return 1.23   # ダミーの計測値


async def handle_event(event):
    print("[EVENT] received:", event["event_signals"][0]["intervals"])
    return "optIn"

client = OpenADRClient(
    ven_id="ven_001",
    ven_name="ven123",
    vtn_url=VTN_URL,
    cert=CERT_FILE,
    key=KEY_FILE,
    ca_file=CA_FILE
)

client.add_report(
    callback=collect_value,
    resource_id="device001",
    measurement="voltage",
    sampling_rate=timedelta(seconds=10)
)

client.add_handler("on_event", handle_event)

loop = asyncio.get_event_loop()
loop.create_task(client.run())
loop.run_forever()
