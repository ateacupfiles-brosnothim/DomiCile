# AI-Powered Tasks Management API

## Base URL

``` text
https://api.taskai.com/v1
```

## Authentication

Protected endpoints require:

``` http
Authorization: Bearer <JWT_TOKEN>
```

# Authentication Endpoints

## POST /auth/register

### Authentication

Not required

### Request

``` json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "StrongPassword123!"
}
```

### Response

``` json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "id": "usr_001",
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

### Error Codes

-   400 Bad Request
-   401 Unauthorized
-   404 Not Found
-   500 Internal Server Error

------------------------------------------------------------------------

## POST /auth/login

### Authentication

Not required

### Request

``` json
{
  "email": "john@example.com",
  "password": "StrongPassword123!"
}
```

### Response

``` json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expiresIn": 86400
}
```

------------------------------------------------------------------------

## POST /auth/logout

### Authentication

JWT Required

### Response

``` json
{
  "success": true,
  "message": "Logged out successfully"
}
```

------------------------------------------------------------------------

# Task Endpoints

## GET /tasks

### Authentication

JWT Required

### Query Parameters

``` text
?page=1&limit=20&priority=urgent
```

### Response

``` json
{
  "success": true,
  "page": 1,
  "limit": 20,
  "total": 87,
  "tasks": []
}
```

------------------------------------------------------------------------

## POST /tasks

### Request

``` json
{
  "title": "Prepare meeting slides",
  "priority": "normal",
  "deadline": "2026-06-23"
}
```

### Response

``` json
{
  "success": true,
  "task": {
    "id": "task_102"
  }
}
```

------------------------------------------------------------------------

## POST /tasks/upload

Uploads a photo and AI extracts text, assigns priority, and suggests a
deadline.

### Response

``` json
{
  "success": true,
  "ocrText": "Pay electricity bill before Friday",
  "aiAnalysis": {
    "priority": "urgent",
    "suggestedDeadline": "2026-06-26"
  }
}
```

------------------------------------------------------------------------

## GET /tasks/{id}

Returns task details.

## PUT /tasks/{id}

Updates task.

## DELETE /tasks/{id}

Deletes task.

## POST /tasks/{id}/share

Shares task with team members.

------------------------------------------------------------------------

# Team Endpoints

## GET /team

Returns all teams.

## POST /team

Creates a team.

## POST /team/{id}/invite

Invites a member.

## GET /team/{id}/tasks

Returns shared tasks.

------------------------------------------------------------------------

# WebSocket

``` text
wss://api.taskai.com/v1/ws
```

## Events

-   task.created
-   task.updated
-   task.deleted
-   team.memberJoined

------------------------------------------------------------------------

# Priority Values

  Value    Meaning
  -------- -------------------
  urgent   High priority
  normal   Standard priority
  low      Low priority

# HTTP Status Codes

  Code   Meaning
  ------ -----------------------
  200    Success
  201    Created
  400    Bad Request
  401    Unauthorized
  404    Not Found
  500    Internal Server Error
