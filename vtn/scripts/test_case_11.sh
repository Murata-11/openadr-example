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
DYNAMODB_TABLE_NAME1="test-aws-cli"
DYANAMODB_JSON_PATH1="./cases/case11/dynamodb/meta.json"
DYANAMODB_JSON_PATH2="./cases/case11/dynamodb/dr_event1.json"
DYANAMODB_JSON_PATH3="./cases/case11/dynamodb/dr_event2.json"

# === XMLファイル ===
XML_STEP1="./cases/case11/payloads/oadr_poll_1.xml"
XML_STEP2="./cases/case11/payloads/oadr_created_event_1.xml"
XML_STEP3="./cases/case11/payloads/oadr_poll_2.xml"
XML_STEP4="./cases/case11/payloads/oadr_created_event_2.xml"

# === レスポンス保存先 ===
RESP_DIR="./cases/case11/responses"
RESP_FILE1="${RESP_DIR}/1_oadr_poll.xml"
RESP_FILE2="${RESP_DIR}/2_oadr_created_event.xml"
RESP_FILE3="${RESP_DIR}/3_oadr_poll.xml"
RESP_FILE4="${RESP_DIR}/4_oadr_created_event.xml"

step1() {
  echo "[1] oadrPoll"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_POLL}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP1" \
    > "$RESP_FILE1"

  echo "save response in ${RESP_FILE1}"
  echo -e "\n--- done 1 ---\n"
}

step2() {
  echo "[2] oadrCreatedEvent"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_REGISTER}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP2" \
    > "$RESP_FILE2"

  echo "save response in ${RESP_FILE2}"
  echo -e "\n--- done 2 ---\n"
}

step3() {
  echo "[3] oadrPoll"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_REGISTER}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP3" \
    > "$RESP_FILE3"

  echo "save response in ${RESP_FILE3}"
  echo -e "\n--- done 3 ---\n"
}

step4() {
  echo "[4] oadrCreatedEvent"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_REGISTER}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP4" \
    > "$RESP_FILE4"

  echo "save response in ${RESP_FILE4}"
  echo -e "\n--- done 4 ---\n"
}

main() {
  confirm_endpoint
  put_item_to_dynamodb "$DYNAMODB_TABLE_NAME1" "$DYANAMODB_JSON_PATH1"
  put_item_to_dynamodb "$DYNAMODB_TABLE_NAME2" "$DYANAMODB_JSON_PATH2"
  step1
  step2
  step3
  step4

  echo -e "\n--- done all step ---\n"
}

main "$@"

