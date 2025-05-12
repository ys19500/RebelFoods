import os
import re
import csv
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# Detect website type
def identify_website(url):
    if "swiggy" in url:
        return "swiggy"
    elif "zomato" in url:
        return "zomato"
    elif "mystore" in url:
        return "mystore"
    return None

def scrape_swiggy(url):
    driver = webdriver.Safari()
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'QMaYM')]"))
    )
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

    driver.quit()
    return items, restaurant, city

def scrape_zomato(url):
    driver = webdriver.Safari()
    driver.get(url)
    time.sleep(5)

    city = "UnknownCity"
    restaurant = "UnknownRestaurant"

    try:
        breadcrumb_links = driver.find_elements(By.XPATH, "//a[contains(@class, 'sc-ukj373-3')]")
        if breadcrumb_links and len(breadcrumb_links) >= 2:
            city = breadcrumb_links[2].get_attribute("title").strip()
            restaurant = breadcrumb_links[4].get_attribute("title").strip()
    except Exception:
        pass

    items = []
    elements = driver.find_elements(By.XPATH, "//div[@class= 'sc-nUItV gZWJDT']")
    for el in elements:
        price_element = el.find_element(By.XPATH, ".//span[@class= 'sc-17hyc2s-1 cCiQWA']")
        price = price_element.text.strip()

        name_element = el.find_element(By.XPATH, ".//h4[@class = 'sc-cGCqpu chKhYc']")
        name = name_element.text.strip()

        items.append({"name": name, "price": price})
    driver.quit()
    return items, restaurant, city

def scrape_mystore(url):
    driver = webdriver.Safari()
    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

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
    return items

def scrape_url(url):
    platform = identify_website(url)
    if platform == "swiggy":
        data, restaurant, city = scrape_swiggy(url)
    elif platform == "zomato":
        data, restaurant, city = scrape_zomato(url)
    elif platform == "mystore":
        data = scrape_mystore(url)
        restaurant, city = extract_restaurant_and_city(url)
    else:
        return None, None, None, None
    return data, restaurant, city, platform


def extract_restaurant_and_city(url):
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
        city = "mystore"
        restaurant = parts[2].split('.')[0]
    return restaurant.strip('_'), city.strip('_')

def write_csv(data, platform, restaurant, city):
    city = city.replace(" ", "_").strip()
    restaurant = restaurant.replace(" ", "_").strip()
    platform = platform.lower().strip()

    folder_path = os.path.join(city, restaurant)
    os.makedirs(folder_path, exist_ok=True)

    filename = f"{restaurant}_{city}_{platform}.csv"
    full_path = os.path.join(folder_path, filename)

    keys = data[0].keys()
    with open(full_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    return full_path
