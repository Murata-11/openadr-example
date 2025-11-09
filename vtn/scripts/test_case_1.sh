#!/usr/bin/env bash
set -euo pipefail

# このスクリプトと同じディレクトリにある config.sh を読む
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# クライアント証明書付きの共通 curl オプション
COMMON_OPTS=(
  -sS
  --cert "$CLIENT_CERT"
  --key "$CLIENT_KEY"     
  --cacert "$CA_CERT"
)

# === DynamoDB設定 ===
DYNAMODB_TABLE_NAME="test-aws-cli" # TODO: 変更
DYANAMODB_JSON_PATH="./cases/case1/dynamodb/meta.json"

# === XMLファイル ===
XML_STEP1="./cases/case1/payloads/oadr_query_registration.xml"
XML_STEP2="./cases/case1/payloads/oadr_create_party_registration.xml"
XML_STEP3="./cases/case1/payloads/oadr_register_report.xml"
XML_STEP4_TMPL="./cases/case1/payloads/oadr_created_report.xml.tmpl"
XML_STEP4="./cases/case1/payloads/oadr_created_report.xml"
XML_STEP5="./cases/case1/payloads/oadr_request_event.xml"
XML_STEP6="./cases/case1/payloads/oadr_poll.xml"

# === レスポンス保存先 ===
RESP_DIR="./cases/case1/responses"
RESP_FILE1="${RESP_DIR}/1_oadr_query_registration.xml"
RESP_FILE2="${RESP_DIR}/2_oadr_create_party_registration.xml"
RESP_FILE3="${RESP_DIR}/3_oadr_register_report.xml"
RESP_FILE4="${RESP_DIR}/4_oadr_created_report.xml"
RESP_FILE5="${RESP_DIR}/5_oadr_request_event.xml"
RESP_FILE6="${RESP_DIR}/6_oadr_poll.xml"

step1() {
  echo "[1] oadrQueryRegistration"
  mkdir -p "$RESP_DIR"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_REGISTER}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP1" \
    > "$RESP_FILE1"

  echo "save response in ${RESP_FILE1}"
  echo -e "\n--- done 1 ---\n"
}

step2() {
  echo "[2] oadrCreatePartyRegistration"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_REGISTER}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP2" \
    > "$RESP_FILE2"

  echo "save response in ${RESP_FILE2}"
  echo -e "\n--- done 2 ---\n"
}

step3() {
  echo "[3] oadrRegisterReport"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_REPORT}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP3" \
    > "$RESP_FILE3"

  echo "save response in ${RESP_FILE3}"

  # レスポンスからreportRequestIDを抜いて、次ステップ用XMLを組み立てる
  build_report_request_ids "$RESP_FILE3"
  generate_xml_step "$XML_STEP4_TMPL" "$XML_STEP4"

  echo -e "\n--- done 3 ---\n"
}

step4() {
  echo "[4] oadrCreatedReport"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_REPORT}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP4" \
    > "$RESP_FILE4"

  echo "save response in ${RESP_FILE4}"
  echo -e "\n--- done 4 ---\n"
}

step5() {
  echo "[5] oadrRequestEvent"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_EVENT}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP5" \
    > "$RESP_FILE5"

  echo "save response in ${RESP_FILE5}"
  echo -e "\n--- done 5 ---\n"
}

step6() {
  echo "[6] oadrPoll"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_POLL}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP6" \
    > "$RESP_FILE6"

  echo "save response in ${RESP_FILE6}"
  echo -e "\n--- done 6 ---\n"
}

main() {
  confirm_endpoint
  # DynamoDBにデータを追加する場合は put_item_to_dynamodb（config.sh）を呼び出す。
  put_item_to_dynamodb "$DYNAMODB_TABLE_NAME" "$DYANAMODB_JSON_PATH"
  step1
  step2
  step3
  step4
  step5
  step6
  echo -e "\n--- done all step ---\n"
}

main "$@"

