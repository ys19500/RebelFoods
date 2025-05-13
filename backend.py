from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import os
import json  # Import the json library

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rebel-foods-demo-price-extraction-bot.streamlit.app"],  # Replace with your frontend domain
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class URLInput(BaseModel):
    url: str

def scrape_url(url: str):
    """
    Calls the scraper.py script as a subprocess.  This keeps the scraping
    logic separate and allows for more flexibility.  Handles errors robustly.
    """
    try:
        # Construct the command.  Use the Python executable in the current environment.
        cmd = [sys.executable, "scraper.py", url]  
        print(f"Running scraper command: {cmd}")  # Good practice to log commands

        # Run the subprocess and capture output
        process = subprocess.run(cmd, capture_output=True, timeout=60)  # Set a timeout

        # Check for errors
        if process.returncode != 0:
            print(f"Scraper process failed.  Return code: {process.returncode}")
            print(f"Scraper stderr:\n{process.stderr.decode()}")
            raise HTTPException(status_code=500, detail="Scraping failed")

        # Process the output from scraper.py
        output = process.stdout.decode().strip()
        print(f"Scraper output:\n{output}") # print the output

        # Split the output. Assuming your scraper prints data, restaurant, city, platform
        # separated by a delimiter (e.g., "|"). You'll need to adjust this based on
        # how your main.py script outputs the results.
        parts = output.split("|")
        if len(parts) == 4:
            try:
                data_str = parts[0].strip()
                restaurant = parts[1].strip()
                city = parts[2].strip()
                platform = parts[3].strip()
                data = json.loads(data_str) # Parse the JSON string into a Python object
                return data, restaurant, city, platform
            except json.JSONDecodeError:
                print(f"Error decoding JSON data: {data_str}")
                raise HTTPException(status_code=500, detail="Scraper returned invalid data format (JSON decode error)")
            except Exception as e:
                print(f"Error processing scraper output: {e}")
                raise HTTPException(status_code=500, detail="Error processing scraper output")
        else:
            print(f"Unexpected output format from scraper: {output}")
            raise HTTPException(status_code=500, detail="Scraper returned invalid data format")

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="scraper.py not found") # Changed "scraper.py" to "main.py"
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Scraping process timed out")
    except Exception as e:
        # Log the error
        print(f"Error in scrape_url: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during scraping: {e}")


@app.post("/scrape")
def scrape_endpoint(input: URLInput):
    """
    Endpoint to trigger the scraping and return the data.
    """
    try:
        data, restaurant, city, platform = scrape_url(input.url) # call the function
        return {
            "data": data,
            "restaurant": restaurant,
            "city": city,
            "platform": platform
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unhandled error in /scrape endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")