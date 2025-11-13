from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
import boto3


def transact_put_and_delete(
    client: boto3.client,
    *,
    put_requests: Optional[List[Dict[str, Any]]] = None,
    delete_requests: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Put と Delete をまとめて TransactWriteItems で実行する低レベル汎用関数。

    Parameters
    ----------
    client:
        boto3.client("dynamodb")
    put_requests:
        TransactWriteItems 用 "Put" の dict のリスト
        例:
            {
                "TableName": "users",
                "Item": {...},  # AttributeValue 形式 {"S": "..."} など
                # 任意:
                # "ConditionExpression": "...",
                # "ExpressionAttributeNames": {...},
                # "ExpressionAttributeValues": {...},
            }
    delete_requests:
        TransactWriteItems 用 "Delete" の dict のリスト
        例:
            {
                "TableName": "users",
                "Key": {...},  # AttributeValue 形式
                # 任意で ConditionExpression など
            }
    """
    put_requests = put_requests or []
    delete_requests = delete_requests or []

    transact_items: List[Dict[str, Any]] = []

    for p in put_requests:
        transact_items.append({"Put": p})

    for d in delete_requests:
        transact_items.append({"Delete": d})

    # 何もなければ何もしない
    if not transact_items:
        return

    if len(transact_items) > 25:
        # DynamoDB の制限
        raise ValueError("TransactWriteItems は最大 25 アクションまでです")

    try:
        client.transact_write_items(TransactItems=transact_items)
    except ClientError:
        # 呼び出し側でハンドリングしたいはずなのでそのまま投げる
        raise
