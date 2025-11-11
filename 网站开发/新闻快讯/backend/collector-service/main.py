from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/collect")
def collect_data(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return {
            "success": True,
            "content": response.text,
            "url": url,
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }

if __name__ == "__main__":
    import uvicorn
    # 统一端口：collector 使用 8005，避免与 cleaner (8004) 冲突
    uvicorn.run(app, host="0.0.0.0", port=8005)