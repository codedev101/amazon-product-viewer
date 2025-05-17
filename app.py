import streamlit as st
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import time
from requests.exceptions import RequestException
import os

# Set page config
st.set_page_config(page_title="Amazon ASIN Scraper", page_icon="🛒", layout="centered")

# Streamlit UI
st.title("Amazon ASIN Scraper")
st.write("Enter an Amazon ASIN to fetch product details.")

# Input form
with st.form("asin_form"):
    asin = st.text_input("ASIN (e.g., B08J5V2Q3F)", "")
    submitted = st.form_submit_button("Scrape Product")
    if submitted and not asin:
        st.error("Please enter a valid ASIN.")

# Function to fetch page with retry logic
def fetch_with_retry(url, headers, proxies=None, retries=3, backoff=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            if response.status_code == 200:
                return response
            elif response.status_code in [429, 503]:
                st.warning(f"Rate limited (status {response.status_code}), retrying in {backoff * (2 ** attempt)} seconds...")
                time.sleep(backoff * (2 ** attempt))
            else:
                st.error(f"Failed with status: {response.status_code}")
                return None
        except RequestException as e:
            st.error(f"Request error: {e}")
            time.sleep(backoff * (2 ** attempt))
    st.error("Max retries exceeded.")
    return None

# Function to parse product details
def parse_product_details(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Extract title
        title_elem = soup.select_one("#productTitle")
        title = title_elem.get_text(strip=True) if title_elem else "Not found"
        # Extract price
        price_elem = soup.select_one(".a-price .a-offscreen")
        price = price_elem.get_text(strip=True) if price_elem else "Not found"
        return {"title": title, "price": price}
    except Exception as e:
        st.error(f"Parsing error: {e}")
        return None

# Scrape when form is submitted
if submitted and asin:
    with st.spinner("Fetching product details..."):
        # Generate random User-Agent
        ua = UserAgent()
        headers = {
            "User-Agent": ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }

        # Load proxy settings from environment variables
        proxy_user = os.getenv("PROXY_USER")
        proxy_pass = os.getenv("PROXY_PASS")
        proxy_host = os.getenv("PROXY_HOST")
        proxy_port = os.getenv("PROXY_PORT")

        proxies = None
        if all([proxy_user, proxy_pass, proxy_host, proxy_port]):
            proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
        else:
            st.warning("Proxy settings not found. Scraping may fail on cloud due to IP restrictions.")

        # Construct Amazon URL
        url = f"https://www.amazon.com/dp/{asin.strip()}"

        # Fetch page
        response = fetch_with_retry(url, headers, proxies)
        if response:
            # Parse details
            details = parse_product_details(response.text)
            if details:
                # Display results
                st.success("Product details fetched successfully!")
                st.subheader("Product Details")
                st.write(f"**Title**: {details['title']}")
                st.write(f"**Price**: {details['price']}")
            else:
                st.error("Failed to parse product details.")
        else:
            st.error("Failed to fetch product page.")
