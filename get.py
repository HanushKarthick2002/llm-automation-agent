from fastapi import FastAPI, HTTPException, Query
from pathlib import Path

app = FastAPI()

data_dir = Path("./data")  # Allowed data directory

@app.get("/read")
def read_file(path: str = Query(..., description="Path of the file inside /data directory")):
    file_path = data_dir / path

    # Manual Security check B1: Ensure path is inside /data
    try:
        file_path.relative_to(data_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access to paths outside /data is forbidden.")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        content = file_path.read_text()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

# Run the app with: uvicorn file_read_api:app --reload
