# vtn.py
from aiohttp import web
import asyncio
from datetime import datetime, timezone, timedelta
from functools import partial
from openleadr import enable_default_logging
from openleadr_impl.server import MyOpenADRServer

enable_default_logging()

# 1) 登録を許可（ven_name が "ven123" の時だけ）


async def on_create_party_registration(info):
    if info["ven_name"] == "ven123":
        return "ven_001", "reg_id_123"  # 最小実装：固定値でOK（まずは動かす）
    return False


# 2) レポート登録に応答（値受け取り用のコールバックを返す）


# async def on_register_report(
#     report
# ):
#     print("on_register_report")
#     print(report)

#     async def on_update_report(data):
#         print("on_update_report")
#         print(data)
#     # 受け取りたいなら callback と サンプリング周期 を返す
#     return (on_update_report, 1)

# ---- 受理時の分岐 ----


def _normalize_report_name(name: str | None) -> str | None:
    if name and name.startswith("METADATA_"):
        return name[len("METADATA_") :]
    return name


# --- フル形式のハンドラ ---


async def on_register_report(report: dict):
    """
    report 例:
      {
        'report_specifier_id': 'AmpereHistory',
        'report_name': 'METADATA_TELEMETRY_USAGE',
        'report_descriptions': [
          {'r_id': '...', 'measurement': {...}, 'sampling_rate': {...}, 'report_subject': {...}, ...},
          ...
        ]
      }
    """
    report_name = _normalize_report_name(
        report.get("report_name")
    )  # 'TELEMETRY_USAGE' 等に正規化
    rs_id = report.get("report_specifier_id")
    results = []

    # offered の各 series（r_id）を精査して、受けたいものだけ返す
    for desc in report.get("report_descriptions", []):
        r_id = desc.get("r_id")
        meas = desc.get("measurement", {})
        # 例: 'Voltage', 'Current', 'energyReal'
        item_name = meas.get("item_name")
        unit = meas.get("item_units")
        sampling = desc.get("sampling_rate", {})
        # VENが提示した最小サンプル周期を採用（必要に応じて調整）
        min_period = sampling.get("min_period")

        # --- report_name で分岐 ---
        if report_name == "TELEMETRY_USAGE":
            cb = partial(
                on_update_report_usage,
                report_name=report_name,
                r_id=r_id,
                report_specifier_id=rs_id,
                item_name=item_name,
                unit=unit,
            )
            results.append((r_id, cb, min_period))
        elif report_name == "TELEMETRY_STATUS":
            cb = partial(
                on_update_report_status,
                report_name=report_name,
                r_id=r_id,
                report_specifier_id=rs_id,
                item_name=item_name,
                unit=unit,
            )
            results.append((r_id, cb, min_period))
        else:
            # 想定外は generic に扱う
            cb = partial(
                on_update_report_generic,
                report_name=report_name,
                r_id=r_id,
                report_specifier_id=rs_id,
                item_name=item_name,
                unit=unit,
            )
            results.append((r_id, cb, min_period))

    # 返り値は [(callback, r_id, sampling_rate), ...] の配列
    return results


def ven_lookup(ven_id):
    return {
        "ven_id": "ven_001",
        "ven_name": "ven123",
        "fingerprint": "53:A4:8E:9C:E0:E1:F5:E4:19:28:2E:20:CB:56:92:D2:FF:CD:18:9A:78:1F:20:11:C9:27:8B:43:3F:4D:4A:CF",
        "registration_id": "reg_id_123",
    }


# ---- 実際の更新受信 ----


# 以降は実際の受信時コールバック（data は [(datetime, value), ...]）
async def on_update_report_usage(
    data, report_name, r_id, report_specifier_id, item_name, unit
):
    for ts, val in data:
        print(
            f"[USAGE] {ts} r_id={r_id} rs_id={report_specifier_id} {item_name}={val} {unit} report_name={report_name}"
        )


async def on_update_report_status(
    data, report_name, r_id, report_specifier_id, item_name, unit
):
    for ts, val in data:
        print(
            f"[STATUS] {ts} r_id={r_id} rs_id={report_specifier_id} {item_name}={val} {unit}"
        )


async def on_update_report_generic(
    data, report_name, r_id, report_specifier_id, item_name, unit
):
    for ts, val in data:
        print(
            f"[{report_name}] {ts} r_id={r_id} rs_id={report_specifier_id} {item_name}={val} {unit}"
        )


# 3) VENの応答（optIn/optOut）を受け取る


async def on_event_response(ven_id, event_id, opt_type):
    print(f"[EVENT-RESP] ven={ven_id} event={event_id} opt={opt_type}")


server = MyOpenADRServer(
    vtn_id="myvtn", http_host="0.0.0.0", http_port="8080", ven_lookup=ven_lookup
)
server.add_handler("on_create_party_registration", on_create_party_registration)
server.add_handler("on_register_report", on_register_report)

# 起動直後に拾われるイベントを1つ用意（開始=今から60秒後）
server.add_event(
    ven_id="ven_001",
    signal_name="simple",
    signal_type="level",
    intervals=[
        {
            "dtstart": datetime.now(timezone.utc) + timedelta(seconds=60),
            "duration": timedelta(minutes=5),
            "signal_payload": 1,
        }
    ],
    callback=on_event_response,
)


async def debug_headers(request):
    for k, v in request.headers.items():
        if k.startswith("X-Amzn-Mtls") or k == "AMZN-MTLS-CLIENT-CERT":
            print(k, "=", v[:80], "...")
    return web.Response(text="ok")


server.app.router.add_get("/debug/headers", debug_headers)

loop = asyncio.get_event_loop()
loop.create_task(server.run())
loop.run_forever()
