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
DYANAMODB_JSON_PATH1="./cases/case13/dynamodb/meta.json"
DYANAMODB_JSON_PATH2="./cases/case13/dynamodb/offer_report.json"

# === XMLファイル ===
XML_STEP1="./cases/case13/payloads/oadr_update_report.xml"
XML_STEP2="./cases/case13/payloads/oadr_updated_report.xml"

# === レスポンス保存先 ===
RESP_DIR="./cases/case13/responses"
RESP_FILE1="${RESP_DIR}/1_oadr_update_report.xml"
RESP_FILE2="${RESP_DIR}/2_oadr_updated_report.xml"

step1() {
  echo "[1] oadrUpdateReport"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_POLL}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP1" \
    > "$RESP_FILE1"

  echo "save response in ${RESP_FILE1}"
  echo -e "\n--- done 1 ---\n"
}

step2() {
  echo "[2] oadrUpdatedReport"
  curl "${COMMON_OPTS[@]}" -X POST "${VTN_ENDPOINT}${EI_REGISTER}" \
    -H "Content-Type: application/xml; charset=utf-8" \
    --data-binary @"$XML_STEP2" \
    > "$RESP_FILE2"

  echo "save response in ${RESP_FILE2}"
  echo -e "\n--- done 2 ---\n"
}

main() {
  confirm_endpoint
  put_item_to_dynamodb "$DYNAMODB_TABLE_NAME1" "$DYANAMODB_JSON_PATH1"
  put_item_to_dynamodb "$DYNAMODB_TABLE_NAME2" "$DYANAMODB_JSON_PATH2"
  step1
  step2

  echo -e "\n--- done all step ---\n"
}

main "$@"

