from openleadr_impl.model.user import User
from openleadr_impl.repository.dynamodb import BaseDynamoRepository

class Testaa:
    def test_1(self):
        put_requests = []
        for i in range(1, 30):
            user = User(
                name="1", 
                email="1",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
                user_id=str(i)
            )
            put_requests.append(user.to_dynamodb_put_request())

        delete_requests = []
        for i in range(1, 10):
            delete = {
                "TableName": "test-table",
                "Key": {"user_id": {"S": str(i)}}
            }
            delete_requests.append(delete)

        repo = BaseDynamoRepository()
        repo.transact_put_and_delete(put_requests=put_requests, delete_requests=delete_requests) 
        

