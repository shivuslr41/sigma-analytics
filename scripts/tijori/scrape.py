import requests
from bs4 import BeautifulSoup

# URL of the page to scrape
url = "https://www.tijorifinance.com/company/reliance-industries-limited/"

# Headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Send a GET request to the page with headers
response = requests.get(url, headers=headers, timeout=10)
response.raise_for_status()  # Check if the request was successful

# Parse the page content
soup = BeautifulSoup(response.content, "html.parser")

# Example: Scraping company name and key data points
company_name = soup.find("h1").text.strip()
data_points = soup.find_all("div", class_="key-ratio")

# Extract and print the key data points
print(f"Company Name: {company_name}")
for data_point in data_points:
    label = data_point.find("div", class_="key-ratio-name").text.strip()
    value = data_point.find("div", class_="key-ratio-value").text.strip()
    print(f"{label}: {value}")
