from datetime import datetime, timedelta, timezone

import pytest
from openleadr import messaging

import openleadr_impl.patch.patch_timedelta
from openleadr_impl.patch.patch_timedelta import timedeltaformat_with_zero


class TestTimeDeltaformatWithZero:

    @pytest.mark.parametrize(
        "value,expected",
        [
            (timedelta(seconds=0), "PT0S"),
            (timedelta(days=1), "P1D"),
            (timedelta(hours=1), "PT1H"),
            (timedelta(minutes=1), "PT1M"),
            (timedelta(seconds=1), "PT1S"),
            (timedelta(days=1, hours=1, minutes=2, seconds=3), "P1DT1H2M3S"),
        ],
    )
    def test_元の実装_各条件に1回当てはまる(
        self, value, expected
    ):
        assert timedeltaformat_with_zero(value) == expected

class TestPatchTimedelta:

    def test_generated_xml_contains_PT0S_for_zero_duration(self):
        payload = {
            "response": {
                "response_code": 200,
                "response_description": "OK",
                "request_id": "req-1",
            },
            "registration_id": "reg-1",
            "ven_id": "ven-1",
            "vtn_id": "vtn-1",
            "profiles": [
                {
                    "profile_name": "2.0b",
                    "transports": [{"transport_name": "simpleHttp"}],
                }
            ],
            "requested_oadr_poll_freq": timedelta(seconds=0),
        }

        xml = messaging.create_message("oadrCreatedPartyRegistration", **payload)

        # "PT0S" が XML 内に出現していることを確認
        assert "PT0S" in xml

    def test_generated_xml_contains_PT0S_for_zero_duration_create_report(self):
        payload = {
            "request_id": "req-1",
            "ven_id": "ven-1",
            "report_requests": [
                {
                    "report_request_id": "rr-1",
                    "report_specifier": {
                        "report_specifier_id": "rs-1",
                        "granularity": timedelta(seconds=0),
                        "report_back_duration": timedelta(seconds=0),
                        "report_interval": {
                            "dtstart": datetime.now(timezone.utc),
                            "duration": timedelta(seconds=0),
                        },
                        "specifier_payloads": [
                            {"r_id": "rid-1", "reading_type": "Direct Read"}
                        ],
                    },
                }
            ],
        }

        xml = messaging.create_message("oadrCreateReport", **payload)

        # 生成された XML に "PT0S" が含まれることを確認
        assert "PT0S" in xml
