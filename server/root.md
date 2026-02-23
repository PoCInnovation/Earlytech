# API Routes (Rust server)

Base URL: http://localhost:3000

## GET /
Returns a simple root message.

```bash
curl -s http://localhost:3000/
```

## GET /articles/count
Returns the number of rows in the `articles` table.

```bash
curl -s http://localhost:3000/articles/count
```

Response example:

```json
{"count": 123}
```

## POST /auth/register
Creates a new user.

Request body:

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "password123"
}
```

```bash
curl -s -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"password123"}'
```

Response example:

```json
{"status":"success","user":{"id":"00000000-0000-0000-0000-000000000000"}}
```

## POST /auth/login
Authenticates a user and returns a JWT.

Request body:

```json
{
  "email": "alice@example.com",
  "password": "password123"
}
```

```bash
curl -s -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"password123"}'
```

Response example:

```json
{"status":"success","token":"<jwt>"}
```

## GET /users/:id/keywords
Returns all keywords for a user.

```bash
curl -s http://localhost:3000/users/<user_id>/keywords
```

Response example:

```json
[
  {
    "id": "00000000-0000-0000-0000-000000000000",
    "user_id": "11111111-1111-1111-1111-111111111111",
    "keyword": "machine learning",
    "created_at": "2026-02-23T12:00:00Z"
  }
]
```

## POST /users/:id/keywords
Adds a keyword for a user.

Request body:

```json
{
  "keyword": "machine learning"
}
```

```bash
curl -s -X POST http://localhost:3000/users/<user_id>/keywords \
  -H "Content-Type: application/json" \
  -d '{"keyword":"machine learning"}'
```

Response example:

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "user_id": "11111111-1111-1111-1111-111111111111",
  "keyword": "machine learning",
  "created_at": "2026-02-23T12:00:00Z"
}
```
