# Test Credentials — Temple Management System

## Admin / Superuser (created/reset for testing)
- **Email**: `admin@gmail.com`
- **Password**: `Admin@123`
- **Role**: Admin
- **is_superuser**: True

Login endpoint: `POST /api/user/login`  body `{"email": "...", "password": "..."}`

The response contains a `jwt` field which must be sent on subsequent
requests in the header:

```
Authorization: <jwt>
```

## Database
- **Engine**: MariaDB / MySQL (5.7+ compatible)
- **DB**: `temple`
- **User**: `appadmin`
- **Password**: `appadmin`
- **Host/Port**: `localhost:3306`

## URLs
- Preview frontend: https://fd32960a-5552-41c8-bee2-e9a5572be60a.preview.emergentagent.com
- Preview backend (via ingress `/api`): same host, prefixed with `/api`
- Local backend: http://localhost:8001
- Local frontend: http://localhost:3000

## New penalty endpoints (introduced in this session)
- `GET  /api/penalty/pending/`   – list members with pending penalty
- `POST /api/penalty/recompute/` – idempotent recompute, returns summary
- `GET  /api/penalty/summary/`   – numbers only
