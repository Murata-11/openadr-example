# config.sh

# === 実行環境 ===
APP_ENV="local"

# === 証明書パス ===
CLIENT_CERT="../certs/dummy_ven.crt"
CLIENT_KEY="../certs/dummy_ven.key"
CA_CERT="../certs/dummy_ca.crt"

# === URL ===
DYNAMODB_LOCAL_ENDPOINT="http://dynamodb:8000"
VTN_ENDPOINT="https://openadr-web:443/OpenADR2/Simple/2.0b/"
EI_REGISTER="EiRegisterParty"
EI_REPORT="EiReport"
EI_EVENT="EiEvent"
EI_POLL="OadrPoll"

# ===接続先エンドポイントの確認
confirm_endpoint() {
  echo "このスクリプトは次のエンドポイントにリクエストを送信します:"
  echo "  ${VTN_ENDPOINT}  "
  echo
  read -r -p "本当にこのエンドポイントに接続してもよいですか？ [y/N]: " answer

  case "$answer" in
    [yY]|[yY][eE][sS])
      echo "続行します。"
      ;;
    *)
      echo "中断しました。"
      exit 1
      ;;
  esac
}

# --------------------------------------------------
# ユーティリティ: DynamoDB に put-item する関数
#   引数1: テーブル名
#   引数2: item.json のパス
# --------------------------------------------------
put_item_to_dynamodb() {
  local table_name="$1"
  local json_path="$2"

  echo "[util] put-item to DynamoDB"
  echo "  Mode:     ${APP_ENV}"
  echo "  Table:    ${table_name}"
  echo "  JSON:     ${json_path}"

  # Check aws CLI
  if ! command -v aws >/dev/null 2>&1; then
    echo "Error: aws CLI not found. Please install awscli inside your container or environment." >&2
    exit 1
  fi

  # Check JSON file
  if [ ! -f "${json_path}" ]; then
    echo "Error: The specified JSON file does not exist: ${json_path}" >&2
    exit 1
  fi

  if [ "${APP_ENV}" = "local" ]; then
    echo "  Endpoint: ${DYNAMODB_LOCAL_ENDPOINT}"
    aws dynamodb put-item \
      --table-name "${table_name}" \
      --endpoint-url "${DYNAMODB_LOCAL_ENDPOINT}" \
      --item "file://${json_path}"
  else
    aws dynamodb put-item \
      --table-name "${table_name}" \
      --item "file://${json_path}"
  fi

  echo "[util] put-item completed successfully"
  echo
}