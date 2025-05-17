import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import concurrent.futures
import re
from io import BytesIO
from PIL import Image
import base64
import json
import random
import threading
import queue

# Clear cache and session state to avoid rendering issues
if 'processed_data' in st.session_state:
    # Don't delete the data, we'll use it if it exists
    pass
st.cache_data.clear()

# Set page configuration
st.set_page_config(
    page_title="Amazon Product Viewer",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables if not already present
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'failed_asins' not in st.session_state:
    st.session_state.failed_asins = []
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

if 'current_processing_id' not in st.session_state:
    st.session_state.current_processing_id = 0
if 'total_processing_count' not in st.session_state:
    st.session_state.total_processing_count = 0

# Custom CSS for professional design with reduced white space and enhanced table
def add_custom_css():
    st.markdown("""
    <style>
    
    /* Add this to your custom CSS function */

    /* Full screen gallery specific styling */
    .fullscreen-gallery-container {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #1e1e1e;
        z-index: 9999;
        overflow: hidden;
    }

    .fullscreen-gallery-grid {
        display: grid;
        grid-template-columns: repeat(9, 1fr);
        gap: 8px;
        padding: 10px;
        overflow-y: auto;
        height: 100vh;
        box-sizing: border-box;
    }

    .fullscreen-gallery-item {
        aspect-ratio: 1;
        background-color: white;
        border-radius: 4px;
        overflow: hidden;
        position: relative;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        transition: transform 0.2s ease;
    }

    .fullscreen-gallery-item:hover {
        transform: scale(1.05);
        z-index: 100;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }

    .fullscreen-gallery-item img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        background-color: white;
    }

    .fullscreen-controls {
        position: fixed;
        top: 15px;
        right: 15px;
        display: flex;
        gap: 10px;
        z-index: 10000;
    }

    .fullscreen-exit-button {
        background-color: rgba(0,0,0,0.7);
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        font-size: 18px;
        transition: all 0.2s ease;
    }

    .fullscreen-exit-button:hover {
        background-color: rgba(255,0,0,0.8);
        transform: scale(1.1);
    }

    .image-tooltip {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(0,0,0,0.7);
        color: white;
        padding: 4px 8px;
        font-size: 12px;
        opacity: 0;
        transition: opacity 0.3s;
        text-align: center;
        border-radius: 0 0 4px 4px;
    }

    .fullscreen-gallery-item:hover .image-tooltip {
        opacity: 1;
    }

    /* Initial 4-row viewport guide */
    .four-row-guide {
        position: absolute;
        right: 15px;
        top: 50%;
        width: 3px;
        height: calc(100vh / 4 * 4); /* Exact 4-row height */
        background-color: rgba(255, 153, 0, 0.3);
        z-index: 9999;
        pointer-events: none;
        border-radius: 3px;
    }

    .four-row-guide::after {
        content: "4 rows";
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background-color: rgba(255, 153, 0, 0.8);
        color: white;
        padding: 3px 6px;
        border-radius: 3px;
        font-size: 12px;
        white-space: nowrap;
    }

    /* Animation for items loading */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fullscreen-gallery-item {
        animation: fadeIn 0.3s ease forwards;
        animation-delay: calc(var(--item-index) * 0.02s);
        opacity: 0;
    }
    
    
    :root {
        --primary-color: #232F3E;
        --accent-color: #FF9900;
        --text-color: #232F3E;
        --light-bg: #f5f5f5;
        --card-bg: white;
        --header-font: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        --body-font: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background-color: var(--primary-color);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-family: var(--header-font);
        font-weight: 700;
        margin: 0;
        font-size: 2.5rem;
        color: white;
    }
    
    .accent-text {
        color: var(--accent-color);
    }
    
    .subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 5px;
    }
    
    /* Table styling with fixed layout */
    .styled-table {
        width: 100%;
        table-layout: fixed; /* Critical for fixed column widths */
        border-collapse: separate;
        border-spacing: 0;
        margin: 15px 0;
        font-family: var(--body-font);
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
        border-radius: 10px;
        overflow: hidden;
    }
    
        
    /* Fixed row styling - explicitly set background colors */
    .styled-table tbody tr {
        background-color: white;
    }

    .styled-table tbody tr:nth-of-type(even) {
        background-color: #f9f9f9;
    }

    /* Override any other styles that might cause black background */
    .styled-table tbody tr:hover {
        background-color: #f1f1f1 !important;
    }

    /* Make sure text is always visible regardless of background */
    .styled-table td {
        color: #333333 !important; /* Force text to be dark */
        background-color: inherit !important; /* Use the row's background */
        border: 1px solid #dddddd; /* Add visible borders to help debug */
    }
    
    .styled-table thead tr {
        background-color: #28a745;
        color: white;
        font-weight: bold;
        text-align: left;
    }
    
    .styled-table th,
    .styled-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #ddd;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    /* Column width specifications */
    .styled-table th:nth-child(1),
    .styled-table td:nth-child(1) {
        width: 15%;
        text-align: center;
    }
    
    .styled-table th:nth-child(2),
    .styled-table td:nth-child(2) {
        width: 45%;
        text-align: left;
        white-space: normal; /* Allow wrapping for product titles */
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        line-height: 1.3em;
        max-height: 2.6em;
    }
    
    .styled-table th:nth-child(3),
    .styled-table td:nth-child(3) {
        width: 10%;
        text-align: center;
    }
    
    .styled-table th:nth-child(4),
    .styled-table td:nth-child(4) {
        width: 10%;
        text-align: center;
    }
    
    .styled-table th:nth-child(5),
    .styled-table td:nth-child(5) {
        width: 20%;
        text-align: center;
    }
    
    .styled-table tbody tr:nth-of-type(even) {
        background-color: #f9f9f9;
    }
    
    .styled-table tbody tr:last-of-type {
        border-bottom: 2px solid var(--accent-color);
    }
    
    .styled-table tbody tr:hover {
        background-color: #f1f1f1;
    }
    
    .table-image {
        width: 80px;
        height: 80px;
        object-fit: contain;
        border-radius: 5px;
        border: 1px solid #eee;
        display: block;
        margin: 0 auto;
    }
    
    /* Card styling */
    .product-card {
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        margin-bottom: 15px;
    }
    
    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    
    .product-img-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 10px;
        overflow: hidden;
        border-radius: 8px;
        background-color: #f9f9f9;
        min-height: 200px;
    }
    
    .product-img {
        max-width: 100%;
        max-height: 200px;
        object-fit: contain;
    }
    
    .product-title {
        font-family: var(--header-font);
        font-weight: 600;
        font-size: 1.1rem;
        color: var(--text-color);
        margin-bottom: 10px;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 2.8rem;
    }
    
    .product-price {
        font-weight: 700;
        font-size: 1.3rem;
        color: var(--primary-color);
        margin: 5px 0;
    }
    
    .product-description {
        font-size: 0.9rem;
        color: #555;
        margin-top: 10px;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        flex-grow: 1;
    }
    
    .product-meta {
        font-size: 0.8rem;
        color: #777;
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px solid #eee;
    }
    
    .upload-container {
        background-color: var(--light-bg);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 2px dashed #ccc;
        margin-bottom: 15px;
    }
    
    .upload-icon {
        font-size: 2.5rem;
        color: var(--accent-color);
        margin-bottom: 10px;
    }
    
    .filters-panel {
        background-color: var(--light-bg);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    .filters-panel h3 {
        color: var(--text-color);
        margin: 0 0 10px 0;
    }
    
    .custom-button {
        background-color: var(--accent-color);
        color: white;
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .custom-button:hover {
        background-color: #e68a00;
        transform: translateY(-2px);
    }
    
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 30px 0;
    }
    
    .loading-spinner {
        border: 5px solid #f3f3f3;
        border-top: 5px solid var(--accent-color);
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin-bottom: 15px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .stats-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 15px;
    }
    
    .stat-card {
        background-color: white;
        border-radius: 10px;
        padding: 12px;
        flex: 1;
        margin: 0 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    .stat-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 4px;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #777;
    }
    
    .footer {
        text-align: center;
        padding: 15px;
        margin-top: 20px;
        border-top: 1px solid #eee;
        color: #777;
        font-size: 0.85rem;
    }
    
    /* Product details section styling */
    .product-details-section {
        margin-top: 20px;
    }
    
    .product-details-section h3 {
        color: var(--text-color);
        margin-bottom: 15px;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
    }
    
    /* Fix for Streamlit expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: var(--text-color);
    }
    
    /* Make sure code/data displays correctly */
    code {
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }
    
    pre {
        white-space: pre-wrap !important;
        overflow-x: auto !important;
        max-width: 100% !important;
    }
    
    /* Fix for raw data display */
    .raw-data-container {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
        overflow-x: auto;
        font-family: monospace;
        font-size: 0.9em;
        white-space: pre-wrap;
        word-break: break-word;
    }

    /* New product row styling */
    .product-row {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
    }
    
    .product-row-image {
        flex: 0 0 100px;
        margin-right: 20px;
    }
    
    .product-row-content {
        flex: 1;
    }
    
    .product-row-title {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 5px;
        color: var(--text-color);
    }
    
    .product-row-details {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-top: 8px;
    }
    
    .product-detail-item {
        font-size: 0.9rem;
        color: #555;
    }

    /* Log container styling */
    .log-container {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-family: 'Courier New', monospace;
        padding: 12px;
        border-radius: 5px;
        margin: 10px 0;
        max-height: 300px;
        overflow-y: auto;
    }
    
    .log-entry {
        margin: 4px 0;
        white-space: pre-wrap;
        line-height: 1.4;
    }
    
    .log-info {
        color: #6a9955;
    }
    
    .log-warning {
        color: #dcdcaa;
    }
    
    .log-error {
        color: #f14c4c;
    }
    
    .log-success {
        color: #4ec9b0;
    }
    
    /* IMPROVED Failed ASIN list styling */
    .failed-asin-list {
        background-color: #ff5555;  /* Bright red background */
        border-left: 5px solid #ff0000;
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .failed-asin-title {
        color: white;  /* White text */
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 10px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    .failed-asin-item {
        margin: 5px 0;
        padding: 5px 10px;
        background-color: white;  /* White background for the ASIN code */
        border-radius: 3px;
        color: #d9534f;  /* Red text */
        font-family: monospace;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
        margin-right: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* CAPTCHA counter styling */
    .captcha-counter {
        background-color: #f9f9f9;
        border-left: 3px solid #17a2b8;
        padding: 10px 15px;
        margin: 10px 0;
        border-radius: 0 5px 5px 0;
        font-size: 0.9rem;
    }
    
    .captcha-counter-value {
        font-weight: bold;
        color: #17a2b8;
        font-size: 1.1rem;
    }
    
    /* Processing status indicator */
    .processing-indicator {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        z-index: 1000;
        font-size: 0.9rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .processing-id {
        font-weight: bold;
        color: #4ec9b0;
    }
    
    .processing-total {
        font-weight: bold;
        color: #dcdcaa;
    }
    
    /* Grid Images View Styling */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        grid-auto-rows: 1fr;
        gap: 4px; /* Very small gap (about 0.5 inch) */
        width: 100%;
    }
    
    .grid-item {
        aspect-ratio: 1;
        overflow: hidden;
        background-color: white;
        border-radius: 3px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .grid-item img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }
    
    .scrollable-container {
        height: 800px;
        overflow-y: auto;
        padding: 5px;
        background-color: #f0f0f0;
        border-radius: 5px;
    }

    @media (max-width: 768px) {
        .product-card {
            margin-bottom: 15px;
        }
        .styled-table th,
        .styled-table td {
            padding: 8px 10px;
            font-size: 0.9rem;
        }
        .table-image {
            width: 60px;
            height: 60px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Function to add a log message to the session state
def add_log(message, level="info"):
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    log_entry = (level, f"[{timestamp}] {message}")  # Explicit tuple format with timestamp
    st.session_state.logs.append(log_entry)

def display_logs(log_container):
    log_display = '<div class="log-container">\n'
    
    for entry in st.session_state.logs:
        try:
            # Safely unpack the tuple with proper error handling
            if isinstance(entry, tuple) and len(entry) == 2:
                level, message = entry
                log_display += f'<div class="log-{level}">{message}</div>\n'
            else:
                # Handle unexpected entry format
                log_display += f'<div class="log-error">Invalid log entry: {str(entry)}</div>\n'
        except Exception as e:
            # Catch any errors in the display process
            log_display += f'<div class="log-error">Error displaying log entry: {str(e)}</div>\n'
    
    log_display += '</div>'
    log_container.markdown(log_display, unsafe_allow_html=True)

# Function to create a session with proper headers
def create_session():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/"
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # Add cookies that might help bypass bot detection
    cookies = {
        "session-id": f"{random.randint(100000000, 999999999)}",
        "session-id-time": f"{int(time.time())}",
        "i18n-prefs": "USD",
        "sp-cdn": f"L5Z9:{random.randint(100000, 999999)}"
    }
    
    # Set cookies
    for key, value in cookies.items():
        session.cookies.set(key, value)
        
    return session

# Function to get Amazon product details
def get_amazon_product_details(asin, log_queue, processing_id, total_count):
    # Update processing status
    st.session_state.current_processing_id = processing_id
    st.session_state.total_processing_count = total_count
    
    # Log to the queue
    log_queue.put(('info', f'Starting to process ASIN: {asin} ({processing_id}/{total_count})'))
    
    product_details = {
        'asin': asin,
        'title': 'Product information not available',
        'price': 'N/A',
        'image_url': '',
        'description': 'No description available',
        'rating': 'N/A',
        'success': False,
        'retry_count': 0,
        'error': None
    }

    # Always try exactly 5 times, no early returns
    for attempt in range(5):
        # Create a fresh session every time
        session = create_session()
        url = f"https://www.amazon.com/dp/{asin}"
        
        log_queue.put(('info', f'ASIN {asin}: Attempt {attempt+1}/5 started'))
        
        # Add delay between retries (except first attempt)
        if attempt > 0:
            sleep_time = 2 + random.uniform(2, 7)
            log_queue.put(('info', f'ASIN {asin}: Waiting {sleep_time:.2f} seconds before retry'))
            time.sleep(sleep_time)
        
        try:
            # Make the request with a timeout
            response = session.get(url, timeout=20)  # Longer timeout
            
            if response.status_code == 200:
                log_queue.put(('success', f'ASIN {asin}: Retrieved page on attempt {attempt+1}'))
                
                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract product title
                title_element = soup.select_one('#productTitle')
                if title_element:
                    product_details['title'] = title_element.get_text().strip()
                    log_queue.put(('info', f'ASIN {asin}: Found title: {product_details["title"][:30]}...'))
                else:
                    log_queue.put(('warning', f'ASIN {asin}: No title found on attempt {attempt+1}'))
                
                # Extract product price
                price_selectors = [
                    '.a-price .a-offscreen',
                    '#priceblock_ourprice',
                    '#priceblock_dealprice',
                    '.a-color-price',
                    '#price_inside_buybox',
                    '.priceToPay span.a-offscreen'
                ]
                
                for selector in price_selectors:
                    price_element = soup.select_one(selector)
                    if price_element and price_element.get_text().strip():
                        product_details['price'] = price_element.get_text().strip()
                        log_queue.put(('info', f'ASIN {asin}: Found price: {product_details["price"]}'))
                        break
                
                # Extract product image - CRITICAL PART
                image_found = False
                
                # Try all possible selectors
                image_selectors = [
                    '#landingImage',
                    '#imgBlkFront',
                    '#ebooksImgBlkFront',
                    '#img-wrapper img',
                    '.a-dynamic-image',
                    '#main-image',
                    'img[data-old-hires]',
                    'img[data-a-dynamic-image]',
                    '.imageThumb img',
                    '#imageBlock img',
                    '#imgTagWrapperId img',
                    '.image-wrapper img',
                    'img.a-dynamic-image'
                ]
                
                for selector in image_selectors:
                    image_elements = soup.select(selector)  # Get all matches, not just first
                    
                    for image_element in image_elements:
                        # Try different attribute sources for the image URL
                        for attr in ['src', 'data-old-hires', 'data-a-dynamic-image']:
                            if image_element.get(attr):
                                image_url = image_element.get(attr)
                                
                                # For data-a-dynamic-image (JSON string with URLs)
                                if image_url and image_url.startswith('{'):
                                    try:
                                        image_data = json.loads(image_url)
                                        if image_data:
                                            image_url = max(image_data.keys(), key=lambda x: image_data[x][0] * image_data[x][1])
                                    except:
                                        # If JSON parsing fails, use the src attribute as fallback
                                        image_url = image_element.get('src', '')
                                
                                if image_url:
                                    # If we have a valid URL, process it
                                    try:
                                        # Get the base image URL and append high-resolution suffix
                                        if '._' in image_url:
                                            base_image_url = image_url.split('._')[0]
                                            image_url = base_image_url + "._AC_SL1500_.jpg"
                                        
                                        # Store the image URL
                                        product_details['image_url'] = image_url
                                        log_queue.put(('success', f'ASIN {asin}: Found image on attempt {attempt+1}'))
                                        image_found = True
                                        break
                                        
                                    except Exception as img_error:
                                        log_queue.put(('warning', f'ASIN {asin}: Error processing image URL: {str(img_error)}'))
                                        product_details['image_url'] = image_url  # Use original URL as fallback
                                        image_found = True
                                        break
                            
                        if image_found:
                            break
                    
                    if image_found:
                        break
                
                # Check if we found an image
                if not image_found:
                    log_queue.put(('warning', f'ASIN {asin}: No image found on attempt {attempt+1}. Will retry.'))
                    continue  # Try again if no image found
                
                # Extract product description
                description_element = soup.select_one('#productDescription p')
                if description_element:
                    product_details['description'] = description_element.get_text().strip()
                    log_queue.put(('info', f'ASIN {asin}: Found product description'))
                else:
                    # Try to get feature bullets if description is not available
                    feature_bullets = soup.select('#feature-bullets li')
                    if feature_bullets:
                        product_details['description'] = ' '.join([bullet.get_text().strip() for bullet in feature_bullets[:3]])
                        log_queue.put(('info', f'ASIN {asin}: Found feature bullets instead of description'))
                
                # Extract product rating
                rating_selectors = [
                    '.a-icon-star .a-icon-alt',
                    '#acrPopover .a-icon-alt',
                    'span[data-hook="rating-out-of-text"]',
                    'i.a-icon-star'
                ]
                
                for selector in rating_selectors:
                    rating_element = soup.select_one(selector)
                    if rating_element:
                        # Try to get text from the element
                        rating_text = rating_element.get_text().strip() if hasattr(rating_element, 'get_text') else ''
                        
                        # If that doesn't work, try to get the title attribute
                        if not rating_text and hasattr(rating_element, 'get') and 'title' in rating_element.attrs:
                            rating_text = rating_element['title']
                        
                        if rating_text:
                            product_details['rating'] = rating_text
                            log_queue.put(('info', f'ASIN {asin}: Found rating: {product_details["rating"]}'))
                            break
                
                # Mark as successful if we have at least title and image
                if product_details['title'] != 'Product information not available' and image_found:
                    product_details['success'] = True
                    log_queue.put(('success', f'ASIN {asin}: Successfully found title and image!'))
                    return product_details  # Return immediately on success
            
            else:
                log_queue.put(('error', f'ASIN {asin}: Bad status code {response.status_code} on attempt {attempt+1}'))
        
        except Exception as e:
            log_queue.put(('error', f'ASIN {asin}: Error on attempt {attempt+1}: {str(e)}'))
    
    # After all retries, update error and return
    if not product_details['success']:
        log_queue.put(('error', f'ASIN {asin}: Failed after 5 attempts'))
        product_details['error'] = 'Failed to retrieve product data after 5 attempts'
    
    return product_details
    
    
# Function to process CSV data with proper threading
def process_csv_data(df, max_rows=None):
    if 'Asin' not in df.columns:
        st.error("The CSV file must contain an 'Asin' column.")
        return None
    
    # Check if we need to limit the number of rows
    if max_rows is not None and max_rows > 0 and max_rows < len(df):
        df = df.head(max_rows)
    
    # Reset session state logs, failed ASINs, and counters
    st.session_state.logs = []
    st.session_state.failed_asins = []
    st.session_state.processing_complete = False
    st.session_state.captcha_counter = 0
    st.session_state.current_processing_id = 0
    st.session_state.total_processing_count = 0
    
    # Create UI elements
    progress_bar = st.progress(0)
    status_text = st.empty()
    processing_status = st.empty()
    log_expander = st.expander("Processing Log (Live)", expanded=True)
    log_container = log_expander.empty()
    
    # Initialize log display
    log_container.markdown('<div class="log-container">', unsafe_allow_html=True)
    
    unique_asins = df['Asin'].unique()
    total_asins = len(unique_asins)
    
    status_text.text(f"Processing {total_asins} unique products...")
    add_log(f"Starting processing of {total_asins} unique ASINs")
    
    # Create a log queue to handle logging from threads
    log_queue = queue.Queue()
    
    # Function to process log queue in the main thread
    def process_log_queue(log_queue):
        while not log_queue.empty():
            try:
                # Get the next item - should be a tuple of (level, message)
                item = log_queue.get()
                
                # Make sure it's a tuple with 2 elements
                if isinstance(item, tuple) and len(item) == 2:
                    level, message = item
                    st.session_state.logs.append((level, message))
                else:
                    # Handle unexpected format - convert to string and use as message
                    st.session_state.logs.append(("error", f"Malformed log entry: {str(item)}"))
            except Exception as e:
                # Add error handling for any other issues
                st.session_state.logs.append(("error", f"Error processing log entry: {str(e)}"))
    
    # Create a function to process a batch of ASINs - always batch size 1
    def process_batch(asins, start_index):
        product_details_dict = {}
        # Create a local log queue for this batch
        batch_log_queue = queue.Queue()
        
        # Process one ASIN at a time (force batch size to 1)
        for i, asin in enumerate(asins):
            processing_id = start_index + i + 1  # +1 for 1-based indexing
            product_details = get_amazon_product_details(asin, batch_log_queue, processing_id, total_asins)
            product_details_dict[asin] = product_details
            
            # Add failed ASINs to the list
            if not product_details['success'] or not product_details['image_url']:
                st.session_state.failed_asins.append(asin)
        
        # Transfer batch logs to main log queue
        while not batch_log_queue.empty():
            log_queue.put(batch_log_queue.get())
        
        # Safely process logs from this batch
        process_log_queue(batch_log_queue)
        
        return product_details_dict
    
    # Process ASINS in batches - always batch size 1
    batch_size = 1  # Always process 1 ASIN at a time
    all_product_details = {}
    
    for i in range(0, len(unique_asins), batch_size):
        batch_asins = unique_asins[i:i+batch_size]
        
        # Update status before processing
        progress = i / len(unique_asins)
        progress_bar.progress(progress)
        status_text.text(f"Processing batch {i//batch_size + 1} of {(len(unique_asins) + batch_size - 1) // batch_size}")
        
        # Show current processing status
        processing_status.markdown(f"""
        <div class="processing-indicator">
            Processing ID: <span class="processing-id">{i+1}</span> / <span class="processing-total">{len(unique_asins)}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Process this batch
        batch_results = process_batch(batch_asins, i)
        all_product_details.update(batch_results)
        
        # Process any logs that have accumulated
        while not log_queue.empty():
            level, message = log_queue.get()
            st.session_state.logs.append((level, message))
        
        # Update log display
        log_display = '<div class="log-container">\n'
        for level, message in st.session_state.logs:
            log_display += f'<div class="log-{level}">{message}</div>\n'
        log_display += '</div>'
        log_container.markdown(log_display, unsafe_allow_html=True)
        
        # Update progress
        progress = (i + len(batch_asins)) / len(unique_asins)
        progress_bar.progress(progress)
        status_text.text(f"Processed {i + len(batch_asins)} of {len(unique_asins)} products ({int(progress*100)}%)")
        
        # Small delay to allow the UI to update
        time.sleep(0.1)
    
    # Create the enriched dataframe
    enriched_data = []
    
    for _, row in df.iterrows():
        asin = row['Asin']
        product_info = all_product_details.get(asin, {
            'asin': asin,
            'title': 'Product information not available',
            'price': 'N/A',
            'image_url': '',
            'description': 'No description available',
            'rating': 'N/A',
            'success': False,
            'error': 'Processing skipped'
        })
        
        new_row = row.to_dict()
        new_row.update({
            'Product_Title': product_info['title'],
            'Product_Price': product_info['price'],
            'Product_Image_URL': product_info['image_url'],
            'Product_Description': product_info['description'],
            'Product_Rating': product_info['rating'],
            'Fetch_Success': product_info['success'],
            'Product_Link': f"https://www.amazon.com/dp/{asin}",
            'Error': product_info.get('error', None)
        })
        
        enriched_data.append(new_row)
    
    enriched_df = pd.DataFrame(enriched_data)
    
    # Set processing as complete
    st.session_state.processing_complete = True
    
    # Final progress and status updates
    progress_bar.progress(1.0)
    status_text.empty()
    processing_status.empty()
    
    # Display failed ASINs if any
    if st.session_state.failed_asins:
        failed_count = len(st.session_state.failed_asins)
        st.markdown(f"""
        <div class="failed-asin-list">
            <div class="failed-asin-title">⚠️ Failed to retrieve images for {failed_count} ASINs:</div>
            <div>
        """, unsafe_allow_html=True)
        
        for failed_asin in st.session_state.failed_asins:
            st.markdown(f'<span class="failed-asin-item">{failed_asin}</span>', unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)
            
        log_display += '</div>'
        log_container.markdown(log_display, unsafe_allow_html=True)
    
    return enriched_df



# Add this function to your code
def display_fullscreen_grid(df, search_term=None, min_price=None, max_price=None, sort_by=None):
    if df is None or df.empty:
        st.warning("No data available to display.")
        return
        
    filtered_df = df.copy()
    
    if search_term:
        search_term_lower = search_term.lower()
        filtered_df = filtered_df[
            filtered_df['Product_Title'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Product_Description'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Asin'].str.lower().str.contains(search_term_lower, na=False)
        ]
    
    if min_price is not None:
        filtered_df = filtered_df[filtered_df['Product_Price'].apply(
            lambda x: any(char.isdigit() for char in str(x)) and float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) >= min_price if re.findall(r'\d+\.\d+|\d+', str(x)) else False
        )]
    
    if max_price is not None:
        filtered_df = filtered_df[filtered_df['Product_Price'].apply(
            lambda x: any(char.isdigit() for char in str(x)) and float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) <= max_price if re.findall(r'\d+\.\d+|\d+', str(x)) else False
        )]
    
    if sort_by:
        if sort_by == 'Price (Low to High)':
            filtered_df['Numeric_Price'] = filtered_df['Product_Price'].apply(
                lambda x: float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) if re.findall(r'\d+\.\d+|\d+', str(x)) else float('inf')
            )
            filtered_df = filtered_df.sort_values('Numeric_Price')
            filtered_df = filtered_df.drop('Numeric_Price', axis=1)
        elif sort_by == 'Price (High to Low)':
            filtered_df['Numeric_Price'] = filtered_df['Product_Price'].apply(
                lambda x: float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) if re.findall(r'\d+\.\d+|\d+', str(x)) else 0
            )
            filtered_df = filtered_df.sort_values('Numeric_Price', ascending=False)
            filtered_df = filtered_df.drop('Numeric_Price', axis=1)
        elif sort_by == 'Title (A-Z)':
            filtered_df = filtered_df.sort_values('Product_Title')
        elif sort_by == 'Title (Z-A)':
            filtered_df = filtered_df.sort_values('Product_Title', ascending=False)
    
    if filtered_df.empty:
        st.warning("No products match your search criteria.")
        return
    
    # Create a custom HTML grid for 7 columns instead of the current 9
    import streamlit.components.v1 as components
    
    # Create direct HTML with fixed grid layout - now 7 columns
    html_content = """
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        
        /* Full screen container */
        .fullscreen-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: #1e1e1e;
            z-index: 9999;
            overflow: auto;
            padding: 10px;
            box-sizing: border-box;
        }
        
        /* Close button */
        .fullscreen-exit-button {
            position: fixed;
            top: 15px;
            right: 15px;
            background-color: rgba(0,0,0,0.7);
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 10000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            transition: background-color 0.2s, transform 0.2s;
        }
        
        .fullscreen-exit-button:hover {
            background-color: rgba(255,0,0,0.8);
            transform: scale(1.1);
        }
        
        /* 7-column grid - changed from 9 columns */
        .fullscreen-gallery-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 8px;
            width: 100%;
            padding-top: 10px;
        }
        
        .gallery-item {
            aspect-ratio: 1;
            background-color: white;
            border-radius: 4px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
            position: relative;
        }
        
        .gallery-item:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 1;
        }
        
        .gallery-item img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            background-color: white;
        }
        
        /* ASIN tooltip on hover */
        .gallery-item .asin-tooltip {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: rgba(0,0,0,0.7);
            color: white;
            padding: 4px;
            font-size: 10px;
            opacity: 0;
            transition: opacity 0.2s;
            text-align: center;
        }
        
        .gallery-item:hover .asin-tooltip {
            opacity: 1;
        }
        
        /* Add loading animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .gallery-item {
            animation: fadeIn 0.3s ease forwards;
            animation-delay: calc(var(--item-index) * 0.02s);
            opacity: 0;
        }
    </style>
    
    <div class="fullscreen-container">
        <div class="fullscreen-exit-button" onclick="window.history.back()">×</div>
        <div class="fullscreen-gallery-grid">
    """
    
    # Add all product images to the grid with animation delay
    for i, product in filtered_df.iterrows():
        image_url = product['Product_Image_URL']
        asin = product['Asin']
        title = product['Product_Title'] if 'Product_Title' in product else ''
        
        # Use placeholder if no image
        if not image_url:
            image_url = "https://placehold.co/200x200?text=No+Image"
            
        # Add image with ASIN tooltip and animation delay
        html_content += f"""
        <div class="gallery-item" style="--item-index: {i}">
            <img src="{image_url}" alt="Product {asin}">
            <div class="asin-tooltip">{asin}</div>
        </div>
        """
    
    # Add keyboard controls and close the HTML
    html_content += """
        </div>
    </div>
    
    <script>
        // Add keyboard event to close on ESC key
        document.addEventListener('keydown', function(event) {
            if (event.key === "Escape") {
                window.history.back();
            }
        });
        
        // Hide Streamlit elements to make it truly fullscreen
        document.addEventListener('DOMContentLoaded', function() {
            // Hide all Streamlit elements
            const streamlitElements = document.querySelectorAll('.stApp > div:not(.element-container), header, footer, .stToolbar');
            streamlitElements.forEach(el => {
                el.style.display = 'none';
            });
            
            // Make container fill the screen
            const container = document.querySelector('.fullscreen-container');
            if (container) {
                container.style.position = 'fixed';
                container.style.top = '0';
                container.style.left = '0';
                container.style.width = '100vw';
                container.style.height = '100vh';
                container.style.zIndex = '999999';
            }
        });
    </script>
    """
    
    # Render the fullscreen grid using components.html with height set to cover the screen
    components.html(html_content, height=1000, scrolling=True)

# Modify the render_gallery_tab function to include the fullscreen button
def render_gallery_tab():
    if st.session_state.processed_data is None:
        st.warning("No data has been processed yet. Please upload and process a CSV file in the Upload tab.")
        return
    
    st.markdown("""
    <div class="filters-panel">
        <h3>Search & Filter Products</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Use a 4-column layout instead of 3
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input("Search by product name, description, or ASIN", key="gallery_search")
    
    with col2:
        min_price = st.number_input("Min Price ($)", min_value=0, value=0, key="gallery_min_price")
    
    with col3:
        max_price = st.number_input("Max Price ($)", min_value=0, value=10000, key="gallery_max_price")
    
    with col4:
        # Add the fullscreen button
        fullscreen_button = st.button("🖼️ Full Screen View", key="gallery_fullscreen_btn", help="View images in a fullscreen 9-column grid")
    
    sort_options = ["None", "Price (Low to High)", "Price (High to Low)", "Title (A-Z)", "Title (Z-A)"]
    sort_by = st.selectbox("Sort by", sort_options, key="gallery_sort")
    
    # Show failed ASINs if any
    if st.session_state.failed_asins:
        failed_count = len(st.session_state.failed_asins)
        st.markdown(f"""
        <div class="failed-asin-list">
            <div class="failed-asin-title">❌ Failed to retrieve images for {failed_count} ASINs:</div>
        """, unsafe_allow_html=True)
        
        for failed_asin in st.session_state.failed_asins:
            st.markdown(f'<div class="failed-asin-item">{failed_asin}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Check if fullscreen button was clicked
    if fullscreen_button:
        display_fullscreen_grid(
            st.session_state.processed_data,
            search_term=search_term if search_term else None,
            min_price=min_price if min_price > 0 else None,
            max_price=max_price if max_price < 10000 else None,
            sort_by=sort_by if sort_by != "None" else None
        )
    else:
        # Display the normal gallery
        display_product_gallery(
            st.session_state.processed_data,
            search_term=search_term,
            min_price=min_price if min_price > 0 else None,
            max_price=max_price if max_price < 10000 else None,
            sort_by=sort_by if sort_by != "None" else None
        )
    
    # Keep only this export button and remove any duplicate inside the display_product_gallery function
    try:
        if st.download_button(
            label="Export Enriched Data to CSV",
            data=st.session_state.processed_data.to_csv(index=False),
            file_name="enriched_amazon_products.csv",
            mime="text/csv",
            key="gallery_export_unique"
        ):
            st.success("Data exported successfully!")
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")

# Add the render_grid_tab function to also include a fullscreen option
def render_grid_tab():
    if st.session_state.processed_data is None:
        st.warning("No data has been processed yet. Please upload and process a CSV file in the Upload tab.")
        return
    
    st.markdown("""
    <div class="filters-panel">
        <h3>Grid Images</h3>
        <p>Just product images in a grid</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Use a 4-column layout instead of 3
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input("Search by product name, description, or ASIN", key="grid_search")
    
    with col2:
        min_price = st.number_input("Min Price ($)", min_value=0, value=0, key="grid_min_price")
    
    with col3:
        max_price = st.number_input("Max Price ($)", min_value=0, value=10000, key="grid_max_price")
    
    with col4:
        # Add the fullscreen button
        fullscreen_button = st.button("🖼️ Full Screen View", key="grid_fullscreen_btn", help="View images in a fullscreen 9-column grid")
    
    sort_options = ["None", "Price (Low to High)", "Price (High to Low)", "Title (A-Z)", "Title (Z-A)"]
    sort_by = st.selectbox("Sort by", sort_options, key="grid_sort")
    
    # Show number of products being displayed
    total_products = len(st.session_state.processed_data)
    st.write(f"Displaying images for {total_products} products in 5-column grid")
    
    # Check if fullscreen button was clicked
    if fullscreen_button:
        display_fullscreen_grid(
            st.session_state.processed_data,
            search_term=search_term if search_term else None,
            min_price=min_price if min_price > 0 else None,
            max_price=max_price if max_price < 10000 else None,
            sort_by=sort_by if sort_by != "None" else None
        )
    else:
        # Display the normal grid
        display_product_grid(
            st.session_state.processed_data,
            search_term=search_term,
            min_price=min_price if min_price > 0 else None,
            max_price=max_price if max_price < 10000 else None,
            sort_by=sort_by if sort_by != "None" else None
        )
        
# Function to display data in table format with images and product details
def display_product_table(df, search_term=None, min_price=None, max_price=None, sort_by=None):
    if df is None or df.empty:
        st.warning("No data available to display.")
        return
        
    filtered_df = df.copy()
    
    if search_term:
        search_term_lower = search_term.lower()
        filtered_df = filtered_df[
            filtered_df['Product_Title'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Product_Description'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Asin'].str.lower().str.contains(search_term_lower, na=False)
        ]
    
    if min_price is not None:
        filtered_df = filtered_df[filtered_df['Product_Price'].apply(
            lambda x: any(char.isdigit() for char in str(x)) and float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) >= min_price if re.findall(r'\d+\.\d+|\d+', str(x)) else False
        )]
    
    if max_price is not None:
        filtered_df = filtered_df[filtered_df['Product_Price'].apply(
            lambda x: any(char.isdigit() for char in str(x)) and float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) <= max_price if re.findall(r'\d+\.\d+|\d+', str(x)) else False
        )]
    
    if sort_by:
        if sort_by == 'Price (Low to High)':
            filtered_df['Numeric_Price'] = filtered_df['Product_Price'].apply(
                lambda x: float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) if re.findall(r'\d+\.\d+|\d+', str(x)) else float('inf')
            )
            filtered_df = filtered_df.sort_values('Numeric_Price')
            filtered_df = filtered_df.drop('Numeric_Price', axis=1)
        elif sort_by == 'Price (High to Low)':
            filtered_df['Numeric_Price'] = filtered_df['Product_Price'].apply(
                lambda x: float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) if re.findall(r'\d+\.\d+|\d+', str(x)) else 0
            )
            filtered_df = filtered_df.sort_values('Numeric_Price', ascending=False)
            filtered_df = filtered_df.drop('Numeric_Price', axis=1)
        elif sort_by == 'Title (A-Z)':
            filtered_df = filtered_df.sort_values('Product_Title')
        elif sort_by == 'Title (Z-A)':
            filtered_df = filtered_df.sort_values('Product_Title', ascending=False)
    
    # Display stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(filtered_df)}</div>
            <div class="stat-label">Products Displayed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        success_count = filtered_df['Fetch_Success'].sum() if 'Fetch_Success' in filtered_df.columns else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{success_count}</div>
            <div class="stat-label">Successfully Fetched</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_price = filtered_df['Retail'].mean() if 'Retail' in filtered_df.columns else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">${avg_price:.2f}</div>
            <div class="stat-label">Average Retail Price</div>
        </div>
        """, unsafe_allow_html=True)
    
    if filtered_df.empty:
        st.warning("No products match your search criteria.")
        return
    
    # Create complete HTML with fixed CSS to prevent black backgrounds
    html_content = """
    <style>
    /* Basic table styling */
    .styled-table {
        width: 100%;
        table-layout: fixed;
        border-collapse: separate;
        border-spacing: 0;
        margin: 15px 0;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
        border-radius: 10px;
        overflow: hidden;
    }

    /* Fix table row background issues */
    .styled-table tbody tr {
        background-color: white !important;  /* Force white background */
    }

    .styled-table tbody tr:nth-of-type(even) {
        background-color: #f9f9f9 !important;  /* Force light gray for even rows */
    }

    .styled-table tbody tr:hover {
        background-color: #f1f1f1 !important;  /* Force light hover state */
    }

    /* Force text to be visible */
    .styled-table td {
        color: black !important;
        background-color: transparent !important;
    }

    /* Header styling */
    .styled-table thead tr {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: bold;
        text-align: left;
    }
    
    .styled-table th {
        color: white !important;
    }
    
    /* Cell styling */
    .styled-table th,
    .styled-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #ddd;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Column width specifications */
    .styled-table th:nth-child(1),
    .styled-table td:nth-child(1) {
        width: 15%;
        text-align: center;
    }
    
    .styled-table th:nth-child(2),
    .styled-table td:nth-child(2) {
        width: 45%;
        text-align: left;
    }
    
    .styled-table th:nth-child(3),
    .styled-table td:nth-child(3) {
        width: 10%;
        text-align: center;
    }
    
    .styled-table th:nth-child(4),
    .styled-table td:nth-child(4) {
        width: 10%;
        text-align: center;
    }
    
    .styled-table th:nth-child(5),
    .styled-table td:nth-child(5) {
        width: 20%;
        text-align: center;
    }
    
    .styled-table tbody tr:last-of-type {
        border-bottom: 2px solid #FF9900;
    }
    
    .table-image {
        width: 80px;
        height: 80px;
        object-fit: contain;
        border-radius: 5px;
        border: 1px solid #eee;
        display: block;
        margin: 0 auto;
    }
    </style>
    
    <table class="styled-table">
        <thead>
            <tr>
                <th>ASIN</th>
                <th>Product Title</th>
                <th>Price</th>
                <th>Rating</th>
                <th>Image</th>
            </tr>
        </thead>
        <tbody>
    """
    
    # Build table rows
    for _, product in filtered_df.iterrows():
        # Clean data
        asin = str(product['Asin']).strip()
        title = str(product['Product_Title']).strip()
        price = str(product['Product_Price']).strip()
        rating = str(product['Product_Rating']).strip()
        image_url = str(product['Product_Image_URL']).strip()
        
        # Truncate title if needed
        title_display = title[:80] + '...' if len(title) > 80 else title
        
        # Use a placeholder image if the image URL is empty
        if not image_url:
            image_url = "https://placehold.co/200x200?text=No+Image"
            
        # Create image HTML - make sure the image tag is properly closed
        image_html = f'<img src="{image_url}" class="table-image" alt="{title}">'
        
        # Add each row to the table with proper HTML escaping
        html_content += f"""
        <tr>
            <td>{asin}</td>
            <td>{title_display}</td>
            <td>{price}</td>
            <td>{rating}</td>
            <td>{image_html}</td>
        </tr>
        """
    
    # Close the table
    html_content += """
        </tbody>
    </table>
    """
    
    # Directly render the complete HTML table using st.components.v1.html()
    import streamlit.components.v1 as components
    components.html(html_content, height=500, scrolling=True)
    
    # Product Details section with improved formatting
    st.markdown('<div class="product-details-section">', unsafe_allow_html=True)
    st.markdown('<h3>Product Details</h3>', unsafe_allow_html=True)
    
    for i, product in filtered_df.iterrows():
        # Ensure clean data
        title = str(product['Product_Title']).strip()
        title_display = title[:80] + '...' if len(title) > 80 else title
        
        with st.expander(title_display):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if product['Product_Image_URL']:
                    st.image(product['Product_Image_URL'], width=150)
                else:
                    st.write("No image available")
                    
            with col2:
                st.subheader(title)
                
                # Format and display key product information
                st.write(f"**Price:** {product['Product_Price']}")
                st.write(f"**ASIN:** {product['Asin']}")
                st.write(f"**Rating:** {product['Product_Rating']}")
                
                # Display description with proper formatting
                st.write("**Description:**")
                description = str(product['Product_Description']).strip()
                if description and description.lower() != 'no description available':
                    st.write(description)
                else:
                    st.write("No detailed description available.")
                
                # Product link with proper formatting
                product_link = f"https://www.amazon.com/dp/{product['Asin']}"
                st.write(f"**Product Link:** [{product_link}]({product_link})")
                
                # Display additional information if available
                if 'UPC' in product and str(product['UPC']).strip():
                    st.write(f"**UPC:** {product['UPC']}")
                if 'Units' in product and str(product['Units']).strip():
                    st.write(f"**Units:** {product['Units']}")
                if 'Retail' in product and not pd.isna(product['Retail']):
                    st.write(f"**Retail Price:** ${product['Retail']}")
                
                # Display error message if product retrieval failed
                if 'Error' in product and product['Error']:
                    st.error(f"Error during retrieval: {product['Error']}")
                
                # Add raw data display WITHOUT using an expander
                st.markdown("**Raw Data:**")
                product_dict = product.to_dict()
                st.markdown(f"""
                <div class="raw-data-container">
                {json.dumps(product_dict, indent=2, default=str)}
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_product_gallery(df, search_term=None, min_price=None, max_price=None, sort_by=None):
    if df is None or df.empty:
        st.warning("No data available to display.")
        return
        
    filtered_df = df.copy()
    
    if search_term:
        search_term_lower = search_term.lower()
        filtered_df = filtered_df[
            filtered_df['Product_Title'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Product_Description'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Asin'].str.lower().str.contains(search_term_lower, na=False)
        ]
    
    if min_price is not None:
        filtered_df = filtered_df[filtered_df['Product_Price'].apply(
            lambda x: any(char.isdigit() for char in str(x)) and float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) >= min_price if re.findall(r'\d+\.\d+|\d+', str(x)) else False
        )]
    
    if max_price is not None:
        filtered_df = filtered_df[filtered_df['Product_Price'].apply(
            lambda x: any(char.isdigit() for char in str(x)) and float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) <= max_price if re.findall(r'\d+\.\d+|\d+', str(x)) else False
        )]
    
    if sort_by:
        if sort_by == 'Price (Low to High)':
            filtered_df['Numeric_Price'] = filtered_df['Product_Price'].apply(
                lambda x: float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) if re.findall(r'\d+\.\d+|\d+', str(x)) else float('inf')
            )
            filtered_df = filtered_df.sort_values('Numeric_Price')
            filtered_df = filtered_df.drop('Numeric_Price', axis=1)
        elif sort_by == 'Price (High to Low)':
            filtered_df['Numeric_Price'] = filtered_df['Product_Price'].apply(
                lambda x: float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) if re.findall(r'\d+\.\d+|\d+', str(x)) else 0
            )
            filtered_df = filtered_df.sort_values('Numeric_Price', ascending=False)
            filtered_df = filtered_df.drop('Numeric_Price', axis=1)
        elif sort_by == 'Title (A-Z)':
            filtered_df = filtered_df.sort_values('Product_Title')
        elif sort_by == 'Title (Z-A)':
            filtered_df = filtered_df.sort_values('Product_Title', ascending=False)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(filtered_df)}</div>
            <div class="stat-label">Products Displayed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        success_count = filtered_df['Fetch_Success'].sum() if 'Fetch_Success' in filtered_df.columns else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{success_count}</div>
            <div class="stat-label">Successfully Fetched</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_price = filtered_df['Retail'].mean() if 'Retail' in filtered_df.columns else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">${avg_price:.2f}</div>
            <div class="stat-label">Average Retail Price</div>
        </div>
        """, unsafe_allow_html=True)
    
    if filtered_df.empty:
        st.warning("No products match your search criteria.")
        return
    
    # If we have CAPTCHA data, show it
    if st.session_state.captcha_counter > 0:
        st.markdown(f"""
        <div class="captcha-counter">
            Successfully solved <span class="captcha-counter-value">{st.session_state.captcha_counter}</span> CAPTCHAs during processing.
        </div>
        """, unsafe_allow_html=True)
    
    # Instead of using st.columns and st.markdown for each product card,
    # create a complete HTML string with all product cards and render it at once
    import streamlit.components.v1 as components
    
    # Create the HTML content with all product cards
    html_content = """
    <style>
    .product-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        margin-bottom: 15px;
    }
    
    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    
    .product-img-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 10px;
        overflow: hidden;
        border-radius: 8px;
        background-color: #f9f9f9;
        min-height: 200px;
    }
    
    .product-img {
        max-width: 100%;
        max-height: 200px;
        object-fit: contain;
    }
    
    .product-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        color: #232F3E;
        margin-bottom: 10px;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 2.8rem;
    }
    
    .product-price {
        font-weight: 700;
        font-size: 1.3rem;
        color: #232F3E;
        margin: 5px 0;
    }
    
    .product-description {
        font-size: 0.9rem;
        color: #555;
        margin-top: 10px;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        flex-grow: 1;
    }
    
    .product-meta {
        font-size: 0.8rem;
        color: #777;
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px solid #eee;
    }
    
    .warning-indicator {
        color: #d9534f;
        font-size: 0.8rem;
        margin-top: 5px;
    }
    
    .product-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
    }
    
    @media (max-width: 768px) {
        .product-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (max-width: 576px) {
        .product-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    
    <div class="product-grid">
    """
    
    # Add each product card to the HTML
    for _, product in filtered_df.iterrows():
        # Sanitize strings for HTML
        title = str(product['Product_Title']).replace('"', '&quot;').replace("'", "&#39;")
        price = str(product['Product_Price']).replace('"', '&quot;').replace("'", "&#39;")
        description = str(product['Product_Description']).replace('"', '&quot;').replace("'", "&#39;")
        asin = str(product['Asin']).replace('"', '&quot;').replace("'", "&#39;")
        rating = str(product['Product_Rating']).replace('"', '&quot;').replace("'", "&#39;")
        
        # Check for failed image
        image_indicator = ""
        failed_image = False
        if not product['Product_Image_URL'] or (product['Asin'] in st.session_state.failed_asins):
            image_indicator = '<div class="warning-indicator">⚠️ Image Retrieval Failed</div>'
            failed_image = True
        
        # Image URL (use placeholder if needed)
        image_url = product['Product_Image_URL'] if not failed_image and product['Product_Image_URL'] else 'https://placehold.co/200x200?text=No+Image'
        
        # Append this product card to the HTML
        html_content += f"""
        <div class="product-card">
            <div class="product-img-container">
                <img src="{image_url}" class="product-img" alt="{title}">
                {image_indicator}
            </div>
            <div class="product-title">{title}</div>
            <div class="product-price">{price}</div>
            <div class="product-description">{description}</div>
            <div class="product-meta">
                ASIN: {asin} | Rating: {rating}
            </div>
        </div>
        """
    
    # Close the HTML container
    html_content += "</div>"
    
    # Render all product cards at once using components.html
    components.html(html_content, height=800, scrolling=True)
    
    # Export button with error handling
    try:
        if st.download_button(
            label="Export Enriched Data to CSV",
            data=filtered_df.to_csv(index=False),
            file_name="enriched_amazon_products.csv",
            mime="text/csv",
            key="gallery_export"
        ):
            st.success("Data exported successfully!")
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")

# Function to render the Upload tab
def render_upload_tab():
    st.markdown("""
    <div class="upload-container">
        <div class="upload-icon">📂</div>
        <h3>Upload your CSV file with ASINs</h3>
        <p>The file should contain an 'Asin' column with valid Amazon ASINs.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Use a more unique key name
    uploaded_file = st.file_uploader("", type=["csv", "xlsx", "xls"], key="main_csv_uploader")
    
    # Add option to limit number of rows to process (removed batch size)
    process_limit = st.number_input(
        "Limit number of rows to process (leave at 0 to process all):",
        min_value=0,
        value=0,
        step=1,
        help="Set a limit on how many rows to process. This can be useful for testing or to reduce processing time.",
        key="process_limit_input"  # Add a unique key here too
    )
    
    # Hidden batch size - always set to 1
    batch_size = 1
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Show a preview of the raw data in a clean format
            with st.expander("Preview Raw Data"):
                # Clean and format DataFrame for display
                preview_df = df.copy()
                for col in preview_df.columns:
                    if preview_df[col].dtype == 'object':
                        preview_df[col] = preview_df[col].astype(str).str.strip()
                
                st.dataframe(preview_df)
                
                # Show raw data in JSON format for debugging WITHOUT using another expander
                st.markdown("### Raw JSON Data (First 5 Records)")
                st.markdown("""
                <div class="raw-data-container">
                <pre>
                {}
                </pre>
                </div>
                """.format(df.head(5).to_json(orient='records', indent=2)), unsafe_allow_html=True)
            
            # Display info about the data
            total_rows = len(df)
            unique_asins = df['Asin'].nunique() if 'Asin' in df.columns else 0
            
            st.info(f"File contains {total_rows} rows with {unique_asins} unique ASINs.")
            
            # Warning about processing time
            if process_limit > 0 and process_limit < total_rows:
                st.warning(f"You've chosen to process only {process_limit} rows out of {total_rows} total rows.")
            
            if st.button("Process and Fetch Product Details", key="process_button_unique", help="Click to start fetching product details from Amazon"):
                # Validate the input
                if 'Asin' not in df.columns:
                    st.error("The uploaded file does not contain an 'Asin' column. Please check your file.")
                else:
                    with st.spinner("Processing data and fetching product details..."):
                        # Pass the processing limit to the function
                        max_rows = process_limit if process_limit > 0 else None
                        st.session_state.processed_data = process_csv_data(df, max_rows)
                        
                        if st.session_state.processed_data is not None:
                            st.success("Data processed successfully! Switch to Gallery, Table, or Grid Images tab to view results.")
                        else:
                            st.error("Failed to process data. Please check your CSV file and ensure it has an 'Asin' column.")
        
        except Exception as e:
            st.error(f"Error reading the file: {str(e)}")
            st.markdown("""
            <div class="raw-data-container">
            <p>Troubleshooting tips:</p>
            <ul>
                <li>Ensure your file is properly formatted (CSV or Excel)</li>
                <li>Check that your file contains an 'Asin' column</li>
                <li>Verify there are no special characters or encoding issues</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

def display_product_grid(df, search_term=None, min_price=None, max_price=None, sort_by=None):
    if df is None or df.empty:
        st.warning("No data available to display.")
        return
        
    filtered_df = df.copy()
    
    if search_term:
        search_term_lower = search_term.lower()
        filtered_df = filtered_df[
            filtered_df['Product_Title'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Product_Description'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Asin'].str.lower().str.contains(search_term_lower, na=False)
        ]
    
    if min_price is not None:
        filtered_df = filtered_df[filtered_df['Product_Price'].apply(
            lambda x: any(char.isdigit() for char in str(x)) and float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) >= min_price if re.findall(r'\d+\.\d+|\d+', str(x)) else False
        )]
    
    if max_price is not None:
        filtered_df = filtered_df[filtered_df['Product_Price'].apply(
            lambda x: any(char.isdigit() for char in str(x)) and float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) <= max_price if re.findall(r'\d+\.\d+|\d+', str(x)) else False
        )]
    
    if sort_by:
        if sort_by == 'Price (Low to High)':
            filtered_df['Numeric_Price'] = filtered_df['Product_Price'].apply(
                lambda x: float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) if re.findall(r'\d+\.\d+|\d+', str(x)) else float('inf')
            )
            filtered_df = filtered_df.sort_values('Numeric_Price')
            filtered_df = filtered_df.drop('Numeric_Price', axis=1)
        elif sort_by == 'Price (High to Low)':
            filtered_df['Numeric_Price'] = filtered_df['Product_Price'].apply(
                lambda x: float(re.findall(r'\d+\.\d+|\d+', str(x))[0]) if re.findall(r'\d+\.\d+|\d+', str(x)) else 0
            )
            filtered_df = filtered_df.sort_values('Numeric_Price', ascending=False)
            filtered_df = filtered_df.drop('Numeric_Price', axis=1)
        elif sort_by == 'Title (A-Z)':
            filtered_df = filtered_df.sort_values('Product_Title')
        elif sort_by == 'Title (Z-A)':
            filtered_df = filtered_df.sort_values('Product_Title', ascending=False)
    
    if filtered_df.empty:
        st.warning("No products match your search criteria.")
        return
    
    # Create a custom HTML grid for 5 columns and 4 rows
    import streamlit.components.v1 as components
    
    # Create direct HTML with fixed grid layout
    html_content = """
    <style>
        .image-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            grid-auto-rows: 1fr;
            gap: 4px; /* Very small gap (about 0.5 inch) */
            width: 100%;
        }
        
        .grid-item {
            aspect-ratio: 1;
            overflow: hidden;
        }
        
        .grid-item img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            background-color: white;
        }
        
        .scrollable-container {
            height: 100%;
            overflow-y: auto;
        }
    </style>
    
    <div class="scrollable-container">
        <div class="image-grid">
    """
    
    # Add all product images to the grid
    for i, product in filtered_df.iterrows():
        image_url = product['Product_Image_URL']
        
        # Use placeholder if no image
        if not image_url:
            image_url = "https://placehold.co/200x200?text=No+Image"
            
        # Add just the image to grid - no ASIN or text
        html_content += f"""
        <div class="grid-item">
            <img src="{image_url}" alt="Product">
        </div>
        """
    
    # Close the HTML
    html_content += """
        </div>
    </div>
    """
    
    # Render the grid
    components.html(html_content, height=800, scrolling=True)



# Function to render the Table tab
def render_table_tab():
    if st.session_state.processed_data is None:
        st.warning("No data has been processed yet. Please upload and process a CSV file in the Upload tab.")
        return
    
    st.markdown("""
    <div class="filters-panel">
        <h3>Search & Filter Products</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("Search by product name, description, or ASIN", key="table_search")
    
    with col2:
        min_price = st.number_input("Min Price ($)", min_value=0, value=0, key="table_min_price")
    
    with col3:
        max_price = st.number_input("Max Price ($)", min_value=0, value=10000, key="table_max_price")
    
    sort_options = ["None", "Price (Low to High)", "Price (High to Low)", "Title (A-Z)", "Title (Z-A)"]
    sort_by = st.selectbox("Sort by", sort_options, key="table_sort")
    
    # Show failed ASINs if any
    if st.session_state.failed_asins:
        failed_count = len(st.session_state.failed_asins)
        st.markdown(f"""
        <div class="failed-asin-list">
            <div class="failed-asin-title">❌ Failed to retrieve images for {failed_count} ASINs:</div>
        """, unsafe_allow_html=True)
        
        for failed_asin in st.session_state.failed_asins:
            st.markdown(f'<div class="failed-asin-item">{failed_asin}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    display_product_table(
        st.session_state.processed_data,
        search_term=search_term,
        min_price=min_price if min_price > 0 else None,
        max_price=max_price if max_price < 10000 else None,
        sort_by=sort_by if sort_by != "None" else None
    )
    
    # Export button with error handling
    try:
        if st.download_button(
            label="Export Enriched Data to CSV",
            data=st.session_state.processed_data.to_csv(index=False),
            file_name="enriched_amazon_products_table.csv",
            mime="text/csv",
            key="table_export_unique"
        ):
            st.success("Data exported successfully!")
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")

# Main app function
# Main app function - updated version
def main():
    add_custom_css()
    
    st.markdown("""
    <div class="main-header">
        <h1>Amazon <span class="accent-text">Product Viewer</span></h1>
        <div class="subtitle">Upload your CSV file with ASINs to view product details</div>
    </div>
    """, unsafe_allow_html=True)
    
    # FIXED: Use st.query_params instead of st.experimental_get_query_params
    query_params = st.query_params
    if 'fullscreen' in query_params and query_params.get('fullscreen') == 'true':
        if st.session_state.processed_data is not None:
            # Get filter parameters if they exist
            search_term = query_params.get('search', '')
            min_price = float(query_params.get('min_price', 0))
            max_price = float(query_params.get('max_price', 10000))
            sort_by = query_params.get('sort_by', 'None')
            
            # Display fullscreen grid
            display_fullscreen_grid(
                st.session_state.processed_data,
                search_term=search_term if search_term else None,
                min_price=min_price if min_price > 0 else None,
                max_price=max_price if max_price < 10000 else None,
                sort_by=sort_by if sort_by != "None" else None
            )
            return  # Skip the rest of the UI
    
    # Normal UI with tabs - ensure each tab has a unique key
    tab_names = ["📤 Upload CSV", "🖼️ Gallery View", "📋 Table View", "📷 Grid Images"]
    tabs = st.tabs(tab_names)
    
    # Only render each tab content when that tab is selected
    # This prevents duplicate widget creation
    with tabs[0]:
        render_upload_tab()
    
    with tabs[1]:
        render_gallery_tab()
    
    with tabs[2]:
        render_table_tab()
    
    with tabs[3]:
        render_grid_tab()
    
    st.markdown("""
    <div class="footer">
        <p>Amazon Product Viewer App | Created with Streamlit and CAPTCHA Solving</p>
        <p>Enhanced with automatic CAPTCHA detection and solving for reliable product data retrieval</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

