# Bristol Marketplace API

A Django REST API for a local food marketplace in Bristol. Supports role-based access control for Customers, Producers, and Admins.

## Tech Stack

- Python / Django 5.2
- Django REST Framework + SimpleJWT
- PostgreSQL
- Docker & Docker Compose

## Setup & Running

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) must be installed and running.

### 1. Clone the repository

```bash
git clone https://github.com/Rhys11Evans/bristol-marketplace.git
cd bristol-marketplace
```

### 2. Start the containers

```bash
docker compose up -d --build
```

### 3. Apply database migrations

```bash
docker compose exec web python manage.py migrate
```

### 4. (Optional) Create a superuser for Django admin

```bash
docker compose exec web python manage.py createsuperuser
```

### 5. Access the API

The API is available at: **http://localhost:8000**

---

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | No | Register (CUSTOMER / PRODUCER / ADMIN) |
| POST | `/api/auth/login/` | No | Session login |
| POST | `/api/auth/logout/` | Yes | Session logout |
| GET | `/api/auth/me/` | JWT | Current user info + role |
| POST | `/api/auth/token/` | No | JWT login → access + refresh tokens |
| POST | `/api/auth/token/refresh/` | No | Refresh access token |

### Products (`/api/products/`)

| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| GET | `/api/products/` | JWT | Any | List all products |
| POST | `/api/products/create/` | JWT | PRODUCER | Create a product |

### Cart (`/api/cart/`)

| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| GET | `/api/cart/` | JWT | CUSTOMER | View cart |
| POST | `/api/cart/add/` | JWT | CUSTOMER | Add item to cart |
| DELETE | `/api/cart/remove/<id>/` | JWT | CUSTOMER | Remove item from cart |

### Admin (`/api/auth/admin/`)

| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| GET | `/api/auth/admin/users/` | JWT | ADMIN | List all users |
| GET | `/api/auth/admin/users/<id>/` | JWT | ADMIN | Get user details |
| PATCH | `/api/auth/admin/users/<id>/` | JWT | ADMIN | Update user role / status |
| DELETE | `/api/auth/admin/users/<id>/` | JWT | ADMIN | Delete user |

---

## Quick Test (PowerShell)

```powershell
# Register a Producer
$r = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register/" -Method POST `
     -ContentType "application/json" `
     -Body '{"username":"producer1","email":"p@test.com","password":"TestPass123!","password_confirm":"TestPass123!","role":"PRODUCER"}'
$producerToken = $r.tokens.access

# Register a Customer
$r2 = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register/" -Method POST `
      -ContentType "application/json" `
      -Body '{"username":"customer1","email":"c@test.com","password":"TestPass123!","password_confirm":"TestPass123!","role":"CUSTOMER"}'
$customerToken = $r2.tokens.access

# Register an Admin
$r3 = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register/" -Method POST `
      -ContentType "application/json" `
      -Body '{"username":"admin1","email":"a@test.com","password":"TestPass123!","password_confirm":"TestPass123!","role":"ADMIN"}'
$adminToken = $r3.tokens.access

# Producer creates a product
Invoke-RestMethod -Uri "http://localhost:8000/api/products/create/" -Method POST `
  -ContentType "application/json" `
  -Headers @{"Authorization"="Bearer $producerToken"} `
  -Body '{"name":"Organic Honey","description":"Local Bristol honey","price":"12.99"}'

# Customer views cart
Invoke-RestMethod -Uri "http://localhost:8000/api/cart/" -Method GET `
  -Headers @{"Authorization"="Bearer $customerToken"}

# Admin lists all users
Invoke-RestMethod -Uri "http://localhost:8000/api/auth/admin/users/" -Method GET `
  -Headers @{"Authorization"="Bearer $adminToken"}
```

---

## Useful Docker Commands

```powershell
docker compose up -d                  # Start containers
docker compose up -d --build          # Rebuild and start
docker compose exec web python manage.py migrate       # Apply migrations
docker compose exec web python manage.py makemigrations # Create migrations
docker compose restart web            # Restart web server
docker compose logs web --tail 30     # View logs
docker compose down                   # Stop containers
```

## User Roles

| Role | Permissions |
|------|-------------|
| `CUSTOMER` | View products, manage own cart |
| `PRODUCER` | View products, create and manage own products |
| `ADMIN` | View and manage all users |
