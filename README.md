# Campus Lost and Found API

A 15-day Python backend development project using FastAPI.

## Setup Instructions

1. Activate virtual environment:
   `.\venv\Scripts\activate`

2. Run local server:
   `uvicorn main:app --reload`

3. Test Health Endpoint:
   Navigate to `http://127.0.0.1:8000/health`

---

## API Design Plan

### Data Entities
- **Item**: ID, Title, Description, Category, Location, Status (lost/found), Is Claimed, Created At.

### Endpoints
| HTTP Method | Endpoint | Description | Success Code | Error Code |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/health` | Application health check | 200 OK | N/A |
| **POST** | `/items` | Create lost/found item | 201 Created | 422 Unprocessable |
| **GET** | `/items` | List all items | 200 OK | N/A |
| **GET** | `/items/{id}` | Get item details | 200 OK | 404 Not Found |