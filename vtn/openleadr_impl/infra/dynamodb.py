import os
import boto3
from typing import Optional


def get_dynamodb_client():
    """
    DynamoDB の boto3 クライアントを取得するヘルパー関数。

    引数:
        region_name: AWS リージョン（例: "ap-northeast-1"）
                     未指定なら AWS_REGION 環境変数、なければ "ap-northeast-1"
        endpoint_url: DynamoDB のエンドポイント URL
                      未指定なら DYNAMODB_ENDPOINT 環境変数を利用
                      (例: "http://localhost:8000")
        profile_name: ~/.aws/credentials のプロファイル名

    戻り値:
        boto3.client("dynamodb") のインスタンス
    """

    session = boto3.Session()

    region = os.getenv("AWS_REGION", "local")
    endpoint = os.getenv("DYNAMODB_ENDPOINT")

    client = session.client(
        service_name="dynamodb",
        region_name="local",
        endpoint_url="http://dynamodb:8000",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy"
    )

    return client
