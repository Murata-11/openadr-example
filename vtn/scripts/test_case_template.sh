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
DYNAMODB_TABLE_NAME="test-aws-cli"
DYANAMODB_JSON_PATH="./cases/template/dynamodb/item.json"

# === XMLファイル ===
XML_STEP1="./cases/template/payloads/oadr_query_registration.xml"
XML_STEP2="./cases/template/payloads/oadr_create_party_registration.xml"

# === レスポンス保存先 ===
RESP_DIR="./cases/template/responses"
RESP_FILE1="${RESP_DIR}/1_oadr_query_registration.xml"
RESP_FILE2="${RESP_DIR}/2_oadr_create_party_registration.xml"

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

main() {
  confirm_endpoint
  # DynamoDBにデータを追加する場合は put_item_to_dynamodb（config.sh）を呼び出す。
  put_item_to_dynamodb "$DYNAMODB_TABLE_NAME" "$DYANAMODB_JSON_PATH"
  step1
  step2
  echo -e "\n--- done all step ---\n"
}

main "$@"

