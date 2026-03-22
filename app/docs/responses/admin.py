# "/admin/keys"
POST_ADMIN_KEYS = {
    200: {
        "description": "Created API key",
        "content": {
            "application/json": {
                "example": {
                    "key": "tQz1s-BVgg2FEqBUcAg4QaDQb33OOXnAn50b24cFVx0",
                    "name": "test-02"
                }
            }
        },
    },
}

# "/admins/keys/list"
GET_ADMIN_KEYS_LIST = {
    200: {
        "description": "List of API keys",
        "content": {
            "application/json": {
                "example": [
                    {
                        "id": 1,
                        "key": "tQz1s-BVgg2FEqBUcAg4QaDQb33OOXnAn50b24cFVx0",
                        "name": "First Key",
                        "active": True
                    },
                    {
                        "id": 2,
                        "key": "tQz1s-BVgg2FEqBUcAg4QaDQb33OOXnAn50b24cFVx1",
                        "name": "User 443",
                        "active": True
                    },
                    {
                        "id": 3,
                        "key": "tQz1s-BVgg2FEqBUcAg4QaDQb33OOXnAn50b24cFVx2",
                        "name": "User 445",
                        "active": True
                    }
                ]
            }
        },
    },
}

# "/admin/keys/{key_name}"
PATCH_ADMIN_KEYS_KEYNAME = {
    200: {
        "description": "Deactivated API key",
        "content": {
            "application/json": {
                "example": {"status": "deactivated"}
            }
        },
    },
    404: {
        "description": "Key not found",
        "content": {
            "application/json": {
                "example": {"detail": "User not found"}
            }
        },
    },
    500: {
        "description": "Internal server error",
        "content": {
            "application/json": {
                "example": {"detail": "Error message"}
            }
        },
    },
}

# "admin/authenticated"
GET_ADMIN_AUTHENTICATED = {
    200: {
        "description": "Authenticated",
        "content": {
            "application/json": {
                "example": {"status": "authenticated"}
            }
        },
    },
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid API Key"}
            }
        }
    }
}

POST_ADMIN_SQL = {
    200: {
        "description": "SQL executed successfully",
        "content": {
            "application/json": {
                "example": {
                    "rows": [
                        {"name": "IIC2233-1", "credits": 10},
                        {"name": "IIC2233-2", "credits": 10}
                    ],
                    "count": 2
                }
            }
        },
    },
    400: {
        "description": "Invalid SQL or non-read query",
        "content": {"application/json": {"example": {"detail": "Only SELECT/PRAGMA statements are allowed"}}},
    },
    403: {
        "description": "Not authorized",
        "content": {"application/json": {"example": {"detail": "Admin privileges required"}}},
    },
}
