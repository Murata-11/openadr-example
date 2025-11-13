from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class User:
    user_id: str
    name: str
    email: str
    created_at: str
    updated_at: str

    def to_dynamodb_put_request(self) -> Dict[str, Any]:
        
        item: Dict[str, Any] = {
            "user_id": {"S": self.user_id},
            "name": {"S": self.name},
            "email": {"S": self.email},
            "created_at": {"S": self.created_at},
            "updated_at": {"S": self.updated_at}
        }

        req: Dict[str, Any] = {
            "TableName": "test-table",
            "Item": item,
        }

        return req
