from fastapi import FastAPI

app = FastAPI(title="Campus Lost and Found API")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Campus Lost and Found API is running successfully"
    }