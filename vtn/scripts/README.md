# 結合テスト スクリプト手順書

## 1. 目的

- `*.sh` を用いて OpenADR 2.0b の一連処理を再現する。
- 送信ペイロードとレスポンスをファイルで管理し、デバッグや比較を容易にする。

## 2. ディレクトリと主なファイル

| パス                                   | 役割                                          |                      |
| -------------------------------------- | --------------------------------------------- | -------------------- |
| `scripts/config.sh`                    | 証明書パスや VTN エンドポイントなど共通設定。 |                      |
| `scripts/*.sh`                         | 実行本体。curl でリクエストを連続送信。       |                      |
| `scripts/cases/<name>/dynamodb/*.json` | DynamoDB に追加するデータの定義。             | 必要に応じて作成     |
| `scripts/cases/<name>/payloads/*.xml`  | 送信用ペイロード。事前に準備が必要。          | テストケース毎に作成 |
| `scripts/cases/<name>/responses/*.xml` | 実行後に保存されるレスポンス。                | テストケース毎に作成 |

## 3. 事前準備

1. `/scripts/.devcontainer/devcontainer.json`から開発コンテナに入る（以下はコンテナ上で操作することを想定）。
2. VTN サーバーが起動していること。
3. bash・curl が利用できること（大半の Linux/macOS では標準で可）。
4. VEN 用クライアント証明書 (`.crt`/`.key`) と CA 証明書を取得済みであること。
5. 実行するリクエストに対応する送信用ペイロードが作成済みであること。
6. 必要に応じて、DynamoDB に追加するデータの定義が作成済みであること。

### DynamoDB にデータを追加する場合

1. aws の情報を設定する。（DynamoDB ローカルにデータを追加する場合も設定が必要です。）
   ```bash
   aws configure
   # AWS Access Key ID: xxx（ローカルの場合: dummy）
   # AWS Secret Access Key: xxx（ローカルの場合: dummy）
   # Default region name: ap-northeast-1 など（ローカルの場合: local）
   # Default output format:（必要に応じて）
   ```

## 4. 設定ファイルの更新 (`config.sh`)

| 変数                         | 説明                                                  |
| ---------------------------- | ----------------------------------------------------- |
| `APP_ENV`                    | 実行環境。ローカルの場合`local`、AWS 上の場合`aws`。  |
| `CLIENT_CERT` / `CLIENT_KEY` | VEN 証明書と秘密鍵。                                  |
| `CA_CERT`                    | VTN サーバー検証用 CA。                               |
| `DYNAMODB_LOCAL_ENDPOINT`    | DynamoDB ローカル の エンドポイント。環境ごとに変更。 |
| `VTN_ENDPOINT`               | ベース URL。環境ごとに変更。                          |
| `EI_*`                       | 対象エンドポイント。必要に応じて追加/変更。           |

スクリプト実行時には `confirm_endpoint` 関数が対話的にエンドポイントを再確認するので、意図しない接続を防げる。

## 5. 実行手順

1. `/scripts` に移動する。
   ```bash
   cd /home/murata/playground/openadr-vtn/vtn/scripts
   ```
2. 実行権限が無い場合は付与する（初回のみ）。
   ```bash
   chmod +x test_case_1.sh
   ```
3. スクリプトを実行する。
   ```bash
   bash ./test_case_1.sh
   ```
4. 表示される接続先のエンドポイントを確認して、問題ない場合は y を入力する。中断したい場合は n を入力する
5. 実行中は以下ステップ（例）が順に走る。
   - Step1: `cases/case1/payloads/oadr_query_registration.xml` を `EiRegisterParty` に POST。レスポンスは `responses/1_oadr_query_registration.xml`。
   - Step2: `cases/case1/payloads/oadr_create_party_registration.xml` を同エンドポイントへ POST。レスポンスは `responses/2_oadr_create_party_registration.xml`。

## 6. 実行結果の確認

- レスポンスは XML のまま保存されるため、差分確認には `xmllint --format` などを利用すると読みやすい。
- 正常終了すると `--- done all step ---` が表示される。途中でエラーになった場合は set -e により即停止するので、出力された curl エラーや証明書エラーを確認する。

## 7. よく使う調整項目

- **エンドポイント切り替え**: テスト/本番で URL が異なる場合は `VTN_ENDPOINT` を切り替える。
- **証明書の更新**: 新しい VEN 証明書を発行したら `CLIENT_CERT`／`CLIENT_KEY` を差し替える。
- **追加テストケース**: `cases/caseX` ディレクトリを複製し、ペイロードを変更した上でスクリプト内の XML パスを差し替える。
- **ポーリング等の追加**: `EI_REPORT` `EI_EVENT` `EI_POLL` の変数は今後のエンドポイント追加用に定義済み。必要に応じて関数を追加して利用する。
