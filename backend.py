from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from scraper import scrape_url


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLInput(BaseModel):
    url: str

@app.post("/scrape")
def scrape_endpoint(input: URLInput):
    data, restaurant, city, platform = scrape_url(input.url)

    if data:
        return {
            "data": data,
            "restaurant": restaurant,
            "city": city,
            "platform": platform
        }
    else:
        raise HTTPException(status_code=400, detail="Unable to scrape the URL")
