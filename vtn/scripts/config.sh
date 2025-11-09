# config.sh

# === 証明書パス ===
CLIENT_CERT="/home/murata/playground/openadr-vtn/docker/dev/web/dummy_ven.crt"
CLIENT_KEY="/home/murata/playground/openadr-vtn/docker/dev/web/dummy_ven.key"
CA_CERT="/home/murata/playground/openadr-vtn/docker/dev/web/dummy_ca.crt"

# === URL ===
VTN_ENDPOINT="https://localhost:443/OpenADR2/Simple/2.0b/"
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
