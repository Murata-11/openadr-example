import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from openleadr_impl.repository import dynamodb


@pytest.fixture
def dynamodb_client(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "ap-northeast-1")
    with mock_aws():
        yield boto3.client("dynamodb", region_name="ap-northeast-1")


def _ensure_table(client, table_name="users"):
    try:
        client.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    except client.exceptions.ResourceInUseException:
        pass


class TestChunked:
    def test_even_split(self):
        seq = [{"index": i} for i in range(6)]

        chunks = dynamodb._chunked(seq, 2)

        assert len(chunks) == 3
        assert all(len(chunk) == 2 for chunk in chunks)

    def test_handles_remainder(self):
        seq = [{"index": i} for i in range(5)]

        chunks = dynamodb._chunked(seq, 2)

        assert len(chunks) == 3
        assert chunks[-1] == [{"index": 4}]


class TestBaseDynamoRepositoryTransactPutAndDelete:
    def test_no_requests(self, dynamodb_client):
        _ensure_table(dynamodb_client)
        repo = dynamodb.BaseDynamoRepository()

        repo.transact_put_and_delete()

        assert dynamodb_client.scan(TableName="users")["Items"] == []

    def test_combines_requests(self, dynamodb_client):
        _ensure_table(dynamodb_client)
        dynamodb_client.put_item(
            TableName="users",
            Item={"id": {"S": "2"}},
        )
        repo = dynamodb.BaseDynamoRepository()

        put = {"TableName": "users", "Item": {"id": {"S": "1"}}}
        delete = {"TableName": "users", "Key": {"id": {"S": "2"}}}

        repo.transact_put_and_delete(put_requests=[put], delete_requests=[delete])

        inserted = dynamodb_client.get_item(TableName="users", Key={"id": {"S": "1"}})
        deleted = dynamodb_client.get_item(TableName="users", Key={"id": {"S": "2"}})

        assert inserted["Item"]["id"]["S"] == "1"
        assert "Item" not in deleted

    def test_chunks_more_than_25(self, dynamodb_client):
        _ensure_table(dynamodb_client)
        repo = dynamodb.BaseDynamoRepository()

        put_requests = [
            {"TableName": "users", "Item": {"id": {"S": str(i)}}}
            for i in range(30)
        ]

        repo.transact_put_and_delete(put_requests=put_requests)

        items = dynamodb_client.scan(TableName="users")["Items"]
        ids = {item["id"]["S"] for item in items}

        assert len(items) == 30
        assert ids == {str(i) for i in range(30)}

    def test_propagates_client_error(self, dynamodb_client):
        _ = dynamodb_client  # ensure moto context is active
        repo = dynamodb.BaseDynamoRepository()
        put = {"TableName": "missing", "Item": {"id": {"S": "1"}}}

        with pytest.raises(ClientError) as excinfo:
            repo.transact_put_and_delete(put_requests=[put])

        assert excinfo.value.response["Error"]["Code"] == "ResourceNotFoundException"
