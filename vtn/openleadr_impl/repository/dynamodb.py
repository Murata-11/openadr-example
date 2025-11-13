from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
from openleadr_impl.infra.dynamodb import get_dynamodb_client


def _chunked(seq: List[Dict[str, Any]], size: int) -> List[List[Dict[str, Any]]]:
    return [seq[i:i + size] for i in range(0, len(seq), size)]

class BaseDynamoRepository:
    def __init__(self):
        self._client = get_dynamodb_client()

    def transact_put_and_delete(
        self,
        put_requests: Optional[List[Dict[str, Any]]] = None,
        delete_requests: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        put_requests = put_requests or []
        delete_requests = delete_requests or []

        transact_items: List[Dict[str, Any]] = []

        for p in put_requests:
            transact_items.append({"Put": p})

        for d in delete_requests:
            transact_items.append({"Delete": d})

        if not transact_items:
            return

        # 25件ごとに分割
        batches = _chunked(transact_items, 25)

        try:
            for batch in batches:
                self._client.transact_write_items(TransactItems=batch)
        except ClientError:
            # 呼び出し側で補正処理する前提でそのまま投げる
            raise