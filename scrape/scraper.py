import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# -------- CONFIG --------
SEARCH_QUERY = "marketing agencies in Karachi"
MAX_RESULTS = 20

# -------- SETUP DRIVER --------
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

service = Service("chromedriver.exe")  # path yahan set karo
driver = webdriver.Chrome(service=service, options=chrome_options)

# -------- OPEN GOOGLE MAPS --------
driver.get("https://www.google.com/maps")
time.sleep(5)

# search
search_box = driver.find_element(By.ID, "searchboxinput")
search_box.send_keys(SEARCH_QUERY)
driver.find_element(By.ID, "searchbox-searchbutton").click()
time.sleep(5)

# -------- SCROLL RESULTS --------
results = []

scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')

for _ in range(5):
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
    time.sleep(2)

# -------- GET LISTINGS --------
listings = driver.find_elements(By.XPATH, '//a[contains(@href, "/maps/place")]')

links = []
for l in listings[:MAX_RESULTS]:
    links.append(l.get_attribute("href"))

print(f"Found {len(links)} listings")

# -------- EXTRACT DATA --------
def extract_email(text):
    emails = re.findall(r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+", text)
    return emails[0] if emails else None

data = []

for link in links:
    driver.get(link)
    time.sleep(4)

    try:
        name = driver.find_element(By.XPATH, '//h1').text
    except:
        name = None

    try:
        website = driver.find_element(By.XPATH, '//a[contains(@data-item-id,"authority")]').get_attribute("href")
    except:
        website = None

    email = None

    # -------- VISIT WEBSITE --------
    if website:
        try:
            driver.get(website)
            time.sleep(4)
            body_text = driver.page_source
            email = extract_email(body_text)
        except:
            pass

    data.append({
        "name": name,
        "website": website,
        "email": email
    })

    print(name, website, email)

# -------- SAVE --------
df = pd.DataFrame(data)
df.to_csv("leads.csv", index=False)

driver.quit()
