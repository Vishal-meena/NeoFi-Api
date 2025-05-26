
---

# 🚀 NeoFi Event Management API

This is a secure, collaborative event management REST API built using FastAPI, SQLAlchemy, and JWT-based authentication. It supports full CRUD operations on events, user authentication, sharing with permissions, versioning, rollback, and change tracking.

---

## 📦 Requirements

Ensure Python 3.8+ is installed. Then install the dependencies using:

```bash
pip install -r requirements.txt
```

---

## 🗃️ Setup Instructions

1. **Clone the Repository** (if applicable):

   ```bash
   git clone https://github.com/Vishal-meena/NeoFi-Api.git
   cd NeoFi-Api
   ```

2. **Place the Prebuilt SQLite Database**
   Make sure `neofi_events.db` is present in the root directory. This database contains your users and events schema.

3. **Environment Variables**
   You can optionally move your secret keys to a `.env` file or environment variables. Currently, the secret is hardcoded in `auth.py`.

---

## 🚀 Running the API Server

Use **Uvicorn** to start the FastAPI application:

```bash
uvicorn main:app --reload
```

The server will run at:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔐 Authentication Endpoints

* **POST** `/api/auth/register` – Register a new user
* **POST** `/api/auth/login` – Login and get JWT token
* **POST** `/api/auth/refresh` – Refresh access token
* **POST** `/api/auth/logout` – Dummy logout endpoint

> Use the access token returned from `/api/auth/login` as a Bearer token in the `Authorization` header for protected routes.

---

## 📅 Event Management Endpoints

* **POST** `/api/events` – Create a new event
* **GET** `/api/events` – List events (with optional filters)
* **GET** `/api/events/{id}` – Get event by ID
* **PUT** `/api/events/{id}` – Update event
* **DELETE** `/api/events/{id}` – Delete event
* **POST** `/api/events/batch` – Create multiple events
* **POST** `/api/events/{id}/share` – Share event with permissions

---

## 📜 Versioning Endpoints

* **GET** `/api/events/{event_id}/history/{version_id}` – Get specific version of an event
* **POST** `/api/events/{event_id}/rollback/{version_id}` – Rollback to a specific version
* **GET** `/api/events/{event_id}/changelog` – Get changelog
* **GET** `/api/events/{event_id}/diff/{version_id1}/{version_id2}` – Compare two versions

---

## 🧪 Testing the API

You can test endpoints using:

* **Swagger UI** (automatically enabled):
  [http://localhost:8000/docs](http://localhost:8000/docs)
* **Postman** or **curl** with appropriate headers and body.

---

## ✅ Example Usage

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123"
      }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=alice&password=password123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Use the returned `access_token` in the `Authorization` header as `Bearer <token>`.

---
