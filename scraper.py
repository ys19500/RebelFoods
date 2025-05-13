import os
import re
import csv
import time
import shutil
import sys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
import socket
import json  # Import for JSON output

def is_docker():
    """
    Check if the code is running inside a Docker container.
    """
    return os.path.exists('/.dockerenv')

def get_driver() -> WebDriver:
    """
    Retrieves a configured Chrome WebDriver instance, either locally or in Docker.
    """
    if is_docker():
        print("Running inside Docker container...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--window-size=1920,1080')
        try:
            # Use a remote driver, assuming the Selenium Grid is running at the standard port
            driver = webdriver.Remote(command_executor='http://selenium:4444/wd/hub', options=chrome_options)
            print("Successfully connected to Selenium Grid.")
            return driver
        except Exception as e:
            print(f"Error connecting to Selenium Grid: {e}")
            print("Make sure the Selenium Grid is running and accessible.")
            raise  # Re-raise the exception to stop execution
    else:
        print("Running locally (macOS)...")
        chrome_path = "/Applications"
        chromedriver_path = shutil.which("chromedriver")

        print(f"Detected Chrome path: {chrome_path}")
        print(f"Detected ChromeDriver path: {chromedriver_path}")

        if not chromedriver_path:
            print("ChromeDriver not found in the system PATH.  Attempting to download...")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                chromedriver_path = ChromeDriverManager().install()
                print(f"ChromeDriver downloaded to: {chromedriver_path}")
            except ImportError:
                error_message = "ChromeDriver not found and webdriver_manager is not installed.\n" \
                                   "Please ensure ChromeDriver is in your PATH or install webdriver_manager:\n" \
                                   "`pip install webdriver-manager`"
                print(error_message)
                raise RuntimeError(error_message)
            except Exception as e:
                error_message = f"Error downloading ChromeDriver: {e}"
                print(error_message)
                raise RuntimeError(error_message)

        if not chrome_path:
            error_message = "Google Chrome not found in the system PATH."
            print(error_message)
            raise RuntimeError(error_message)

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--start-maximized')
        options.add_argument('--window-size=1920,1080')

        service = Service(executable_path=chromedriver_path)
        try:
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except WebDriverException as e:
            error_message = f"WebDriverException: {e}\n" \
                            "Please check your Chrome and ChromeDriver versions.  They may be incompatible.\n" \
                            f"Chrome path: {chrome_path}\n" \
                            f"ChromeDriver path: {chromedriver_path}"
            print(error_message)
            raise WebDriverException(error_message)

def identify_website(url):
    """Identifies the website from the URL."""
    if "swiggy" in url:
        return "swiggy"
    elif "zomato" in url:
        return "zomato"
    elif "mystore" in url:
        return "mystore"
    return None

def scrape_swiggy(url, driver: WebDriver):
    """Scrapes data from Swiggy."""
    print(f"Scraping Swiggy: {url}")  # Added logging
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'QMaYM')]"))
        )
    except Exception as e:
        error_message = f"Error waiting for Swiggy load: {e}"
        print(error_message)
        return [], "UnknownRestaurant", "UnknownCity"

    try:
        city_elem = driver.find_element(By.XPATH, "//a[contains(@href, '/city/')]/span[@itemprop='name']")
        city = city_elem.text.strip()
    except NoSuchElementException:
        city = "UnknownCity"

    try:
        restaurant_elem = driver.find_element(By.XPATH, "//span[@class='_2vs3E']")
        restaurant = restaurant_elem.text.strip()
    except NoSuchElementException:
        restaurant = "UnknownRestaurant"

    items = []

    products = driver.find_elements(By.XPATH, "//div[contains(@class, 'QMaYM')]")
    for product in products:
        try:
            name_element = product.find_element(By.XPATH, ".//div[@aria-hidden='true' and contains(@class, 'dwSeRx')]")
            name = name_element.text.strip()
        except NoSuchElementException:
            name = "N/A"

        mrp = "N/A"
        discounted_price = "N/A"

        try:
            mrp_element = product.find_element(By.XPATH, ".//div[contains(@class, 'hTspMV')]")
            mrp = mrp_element.text.strip()
        except NoSuchElementException:
            try:
                price_element = product.find_element(By.XPATH, ".//div[contains(@class, 'chixpw')]")
                mrp = price_element.text.strip()
            except NoSuchElementException:
                pass

        try:
            discounted_element = product.find_element(By.XPATH, ".//div[contains(@class, 'chixpw')]")
            if mrp != discounted_element.text.strip():
                discounted_price = discounted_element.text.strip()
        except NoSuchElementException:
            pass

        items.append({
            "name": name,
            "MRP": mrp,
            "Discounted Price": discounted_price,
            "Offer": "",
            "code": ""
        })

    try:
        offer_containers = driver.find_elements(By.XPATH, "//div[@class='sc-cVzyXs kjqKTW']")
        for container in offer_containers:
            try:
                offer_desc_elem = container.find_element(By.XPATH, ".//div[contains(@class, 'hsuIwO')]")
                offer_description = offer_desc_elem.text.strip()
            except NoSuchElementException:
                offer_description = "N/A"

            try:
                offer_code_elem = container.find_element(By.XPATH, ".//div[contains(@class, 'foYDCM')]")
                offer_code = offer_code_elem.text.strip()
            except NoSuchElementException:
                offer_code = "N/A"

            items.append({
                "name": "",
                "MRP": "",
                "Discounted Price": "",
                "Offer": offer_description,
                "code": offer_code
            })
    except NoSuchElementException:
        pass
    print(f"Swiggy Data: {items}, Restaurant: {restaurant}, City: {city}")
    return items, restaurant, city

def scrape_zomato(url, driver: WebDriver):
    """Scrapes data from Zomato."""
    print(f"Scraping Zomato: {url}")  # Added logging
    driver.get(url)
    time.sleep(5)

    city = "UnknownCity"
    restaurant = "UnknownRestaurant"

    try:
        breadcrumb_links = driver.find_elements(By.XPATH, "//a[contains(@class, 'sc-ukj373-3')]")
        if breadcrumb_links and len(breadcrumb_links) >= 2:
            city = breadcrumb_links[2].get_attribute("title").strip()
            restaurant = breadcrumb_links[4].get_attribute("title").strip()
    except Exception as e:
        error_message = f"Error extracting Zomato breadcrumbs: {e}"
        print(error_message)
        city = "UnknownCity"
        restaurant = "UnknownRestaurant"

    items = []
    try:
        elements = driver.find_elements(By.XPATH, "//div[@class= 'sc-nUItV gZWJDT']") # Changed Class
        for el in elements:
            try:
                price_element = el.find_element(By.XPATH, ".//span[@class= 'sc-17hyc2s-1 cCiQWA']") # Changed Class
                price = price_element.text.strip()
            except NoSuchElementException:
                price = "N/A"

            try:
                name_element = el.find_element(By.XPATH, ".//h4[@class = 'sc-cGCqpu chKhYc']") # Changed Class
                name = name_element.text.strip()
            except NoSuchElementException:
                name = "N/A"
            items.append({"name": name, "price": price})
    except Exception as e:
        error_message = f"Error scraping Zomato: {e}"
        print(error_message)
        items = [] # IMPORTANT:  Return an empty list, not None, to avoid errors later

    print(f"Zomato Data: {items}, Restaurant: {restaurant}, City: {city}")
    return items, restaurant, city

def scrape_mystore(url, driver: WebDriver):
    """Scrapes data from Mystore."""
    print(f"Scraping Mystore: {url}") # Added logging
    driver.get(url)
    time.sleep(5)
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")

        items = []
        cards = soup.select("div.product-caption-top.mt-auto")
        for card in cards:
            name = card.select_one("a.twoline_ellipsis")
            seller = card.select_one("a.product_seller_name")
            container = card.find_previous("div")
            price_new = container.select_one("span.price-new")
            price_old = container.select_one("span.price-old")
            discount = container.select_one("span.discount-off")

            items.append({
                "name": name.text.strip() if name else "N/A",
                "price": price_new.text.strip() if price_new else "N/A",
                "old_price": price_old.text.strip() if price_old else "N/A",
                "discount": discount.text.strip() if discount else "N/A",
                "seller": seller.text.strip() if seller else "N/A"
            })
        print(f"Mystore Data: {items}")
        return items
    except Exception as e:
        error_message = f"Error scraping Mystore: {e}"
        print(error_message)
        return []

def scrape_url(url, driver: WebDriver):
    """
    Scrapes the given URL, identifying the website and calling the appropriate scraper.

    Args:
        url (str): The URL to scrape.
        driver (WebDriver):  The Selenium WebDriver instance to use.

    Returns:
        tuple: (data, restaurant, city, platform) or (None, None, None, None) on error
    """
    platform = identify_website(url)
    if platform == "swiggy":
        data, restaurant, city = scrape_swiggy(url, driver)
    elif platform == "zomato":
        data, restaurant, city = scrape_zomato(url, driver)
    elif platform == "mystore":
        data = scrape_mystore(url, driver)
        restaurant, city = extract_restaurant_and_city(url)
    else:
        print(f"Unsupported website: {url}")
        return None, None, None, None
    return data, restaurant, city, platform

def extract_restaurant_and_city(url):
    """
    Extracts restaurant and city names from the URL.  Handles different URL formats.
    """
    url = url.lower()
    parts = url.split('/')
    restaurant = 'unknown_restaurant'
    city = 'unknown_city'

    if "swiggy" in url or "zomato" in url:
        if len(parts) > 4:
            city = parts[3]
        if len(parts) > 5:
            restaurant = parts[5].split('?')[0].replace('-', '_')
    elif "mystore" in url:
        if len(parts) > 2:
           restaurant = parts[2].split('.')[0]
        city = "mystore"
    return restaurant.strip('_'), city.strip('_')

def write_csv(data, platform, restaurant, city):
    """
    Writes the scraped data to a CSV file.

    Args:
        data (list): The data to write.
        platform (str): The website platform.
        restaurant (str): The restaurant name.
        city (str): The city name.

    Returns:
        str: The full path to the created CSV file, or None on error.
    """
    if not data:
        print("No data to write to CSV.")
        return None

    city = city.replace(" ", "_").strip()
    restaurant = restaurant.replace(" ", "_").strip()
    platform = platform.lower().strip()

    folder_path = os.path.join(city, restaurant)
    os.makedirs(folder_path, exist_ok=True)

    filename = f"{restaurant}_{city}_{platform}.csv"
    full_path = os.path.join(folder_path, filename)

    keys = data[0].keys()
    try:
        with open(full_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        return full_path
    except Exception as e:
        print(f"Error writing to CSV: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <url>")
        sys.exit(1)

    target_url = sys.argv[1]
    driver = get_driver()
    try:
        scraped_data, restaurant, city, platform = scrape_url(target_url, driver)
        if scraped_data is not None:
            import json
            print(f"{json.dumps(scraped_data)}|{restaurant}|{city}|{platform}")
        else:
            print("Error during scraping.")
    finally:
        driver.quit()
