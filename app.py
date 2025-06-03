import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
import json
import random
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

if 'fullscreen_mode' not in st.session_state:
    st.session_state.fullscreen_mode = False


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

# Custom CSS for professional design with grid focus
def add_custom_css():
    st.markdown("""
    <style>
    
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
        grid-template-columns: repeat(7, 1fr);
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
    
    .upload-container {
        background-color: var(--light-bg);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 2px dashed #ccc;
        margin-bottom: 15px;
        color: var(--text-color); /* Ensure text is dark for contrast */
    }
    
    .upload-container h3 {
        color: var(--text-color); /* Explicitly set header text color */
        margin-bottom: 10px;
    }
    
    .upload-container p {
        color: var(--text-color); /* Explicitly set paragraph text color */
        margin: 5px 0;
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
        color: var(--text-color); /* Ensure text is dark for contrast */
    }
    
    .filters-panel h3 {
        color: var(--text-color); /* Explicitly set header text color */
        margin: 0 0 10px 0;
    }
    
    .filters-panel p {
        color: var(--text-color); /* Explicitly set paragraph text color */
        margin: 5px 0;
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
    
    /* Failed ASIN list styling */
    .failed-asin-list {
        background-color: #ff5555;
        border-left: 5px solid #ff0000;
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .failed-asin-title {
        color: white;
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 10px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    .failed-asin-item {
        margin: 5px 0;
        padding: 5px 10px;
        background-color: white;
        border-radius: 3px;
        color: #d9534f;
        font-family: monospace;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
        margin-right: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Processing status indicator */
    .processing-indicator {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: rgba(0,0,0,0.8);
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
        gap: 4px;
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
        .image-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Function to add a log message to the session state
def add_log(message, level="info"):
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    log_entry = (level, f"[{timestamp}] {message}")
    st.session_state.logs.append(log_entry)

def display_logs(log_container):
    log_display = '<div class="log-container">\n'
    
    for entry in st.session_state.logs:
        try:
            if isinstance(entry, tuple) and len(entry) == 2:
                level, message = entry
                log_display += f'<div class="log-{level}">{message}</div>\n'
            else:
                log_display += f'<div class="log-error">Invalid log entry: {str(entry)}</div>\n'
        except Exception as e:
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
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
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
    
    cookies = {
        "session-id": f"{random.randint(100000000, 999999999)}",
        "session-id-time": f"{int(time.time())}",
        "i18n-prefs": "USD",
        "sp-cdn": f"L5Z9:{random.randint(100000, 999999)}"
    }
    
    for key, value in cookies.items():
        session.cookies.set(key, value)
        
    return session

# Function to get Amazon product details
def get_amazon_product_details(asin, log_queue, processing_id, total_count):
    st.session_state.current_processing_id = processing_id
    st.session_state.total_processing_count = total_count
    
    log_queue.put(('info', f'Starting to process ASIN: {asin} ({processing_id}/{total_count})'))
    
    product_details = {
        'asin': asin,
        'title': 'Product information not available',
        'price': 'N/A',
        'image_url': '',
        'success': False,
        'retry_count': 0,
        'error': None
    }

    for attempt in range(3):  # Keep 3 attempts
        session = create_session()
        url = f"https://www.amazon.com/dp/{asin}"
        
        log_queue.put(('info', f'ASIN {asin}: Attempt {attempt+1}/3 started'))
        
        if attempt > 0:
            sleep_time = 2 + random.uniform(1, 3)
            log_queue.put(('info', f'ASIN {asin}: Waiting {sleep_time:.2f} seconds before retry'))
            time.sleep(sleep_time)
        
        try:
            response = session.get(url, timeout=15)
            
            if response.status_code == 200:
                log_queue.put(('success', f'ASIN {asin}: Retrieved page on attempt {attempt+1}'))
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract product title
                title_element = soup.select_one('#productTitle')
                if title_element:
                    product_details['title'] = title_element.get_text().strip()
                    log_queue.put(('info', f'ASIN {asin}: Found title: {product_details["title"][:30]}...'))
                
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
                
                # Extract product image
                image_found = False
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
                    image_elements = soup.select(selector)
                    
                    for image_element in image_elements:
                        for attr in ['src', 'data-old-hires', 'data-a-dynamic-image']:
                            if image_element.get(attr):
                                image_url = image_element.get(attr)
                                
                                if image_url and image_url.startswith('{'):
                                    try:
                                        image_data = json.loads(image_url)
                                        if image_data:
                                            image_url = max(image_data.keys(), key=lambda x: image_data[x][0] * image_data[x][1])
                                    except:
                                        image_url = image_element.get('src', '')
                                
                                if image_url:
                                    try:
                                        if '._' in image_url:
                                            base_image_url = image_url.split('._')[0]
                                            image_url = base_image_url + "._AC_SL1500_.jpg"
                                        
                                        product_details['image_url'] = image_url
                                        log_queue.put(('success', f'ASIN {asin}: Found image on attempt {attempt+1}'))
                                        image_found = True
                                        break
                                        
                                    except Exception as img_error:
                                        log_queue.put(('warning', f'ASIN {asin}: Error processing image URL: {str(img_error)}'))
                                        product_details['image_url'] = image_url
                                        image_found = True
                                        break
                            
                        if image_found:
                            break
                    
                    if image_found:
                        break
                
                if not image_found:
                    log_queue.put(('warning', f'ASIN {asin}: No image found on attempt {attempt+1}. Will retry.'))
                    continue
                
                # Check if we have the essential data (title, price, image)
                if product_details['title'] != 'Product information not available' and image_found:
                    product_details['success'] = True
                    log_queue.put(('success', f'ASIN {asin}: Successfully found title, price and image!'))
                    return product_details
            
            else:
                log_queue.put(('error', f'ASIN {asin}: Bad status code {response.status_code} on attempt {attempt+1}'))
        
        except Exception as e:
            log_queue.put(('error', f'ASIN {asin}: Error on attempt {attempt+1}: {str(e)}'))
    
    if not product_details['success']:
        log_queue.put(('error', f'ASIN {asin}: Failed after 3 attempts'))
        product_details['error'] = 'Failed to retrieve product data after 3 attempts'
    
    return product_details
    
# Function to detect CSV type and process accordingly
def detect_csv_type(df):
    """Detect if CSV contains Amazon ASINs or direct image URLs"""
    
    # Clean the dataframe first - remove empty rows and handle NaN
    df_clean = df.dropna(how='all').copy()
    
    if df_clean.empty:
        return 'unknown'
    
    # Check for the specific Excel format: "Listing ID" and "url" columns
    columns_lower = [col.lower().strip() for col in df_clean.columns]
    
    if ('listing id' in columns_lower and 'url' in columns_lower) or \
       ('listing_id' in columns_lower and 'url' in columns_lower) or \
       ('listingid' in columns_lower and 'url' in columns_lower):
        return 'excel_format'
    
    # Check for Amazon ASINs
    amazon_columns = ['asin', 'sku', 'product_id']
    for col in df_clean.columns:
        if any(amazon_term in col.lower() for amazon_term in amazon_columns):
            return 'amazon'
    
    # Check for direct image URLs by examining the actual data
    for index, row in df_clean.head(20).iterrows():
        for value in row:
            if pd.notna(value) and value != 'nan':
                value_str = str(value).strip().lower()
                if ('http' in value_str and 
                    ('.jpg' in value_str or '.png' in value_str or '.jpeg' in value_str or 
                     '.gif' in value_str or '.webp' in value_str)):
                    return 'direct_urls'
    
    return 'unknown'

# Function to process direct image URLs
def process_direct_urls_data(df, max_rows=None):
    """Process CSV with direct image URLs (like liquidation.com)"""
    
    if max_rows is not None and max_rows > 0 and max_rows < len(df):
        df = df.head(max_rows)
    
    st.session_state.logs = []
    st.session_state.failed_asins = []
    st.session_state.processing_complete = False
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_expander = st.expander("Processing Log (Live)", expanded=True)
    log_container = log_expander.empty()
    
    total_rows = len(df)
    status_text.text(f"Processing {total_rows} image URLs...")
    add_log(f"Starting processing of {total_rows} direct image URLs")
    
    enriched_data = []
    
    for index, row in df.iterrows():
        progress = (index + 1) / total_rows
        progress_bar.progress(progress)
        status_text.text(f"Processing {index + 1} of {total_rows} images ({int(progress*100)}%)")
        
        # Extract data from row
        row_dict = row.to_dict()
        
        # Find image URL in the row (look for http URLs)
        image_url = None
        listing_id = None
        
        for key, value in row_dict.items():
            if pd.notna(value) and 'http' in str(value) and ('.jpg' in str(value) or '.png' in str(value) or '.jpeg' in str(value)):
                image_url = str(value).strip()
                break
        
        # Find listing ID (usually the first column or a numeric value)
        for key, value in row_dict.items():
            if pd.notna(value) and str(value).isdigit():
                listing_id = str(value).strip()
                break
        
        if not listing_id:
            listing_id = f"Item_{index + 1}"
        
        # Create enriched row
        new_row = row_dict.copy()
        new_row.update({
            'Listing_ID': listing_id,
            'Product_Title': f"Liquidation Item {listing_id}",
            'Product_Price': 'See Auction',
            'Product_Image_URL': image_url if image_url else '',
            'Product_Description': 'Liquidation item - see auction for details',
            'Product_Rating': 'N/A',
            'Fetch_Success': True if image_url else False,
            'Product_Link': f"https://www.liquidation.com/auction/{listing_id}" if listing_id else '',
            'Error': None if image_url else 'No image URL found'
        })
        
        if not image_url:
            st.session_state.failed_asins.append(listing_id)
            add_log(f"No image URL found for Listing ID: {listing_id}", "warning")
        else:
            add_log(f"Found image URL for Listing ID: {listing_id}", "success")
        
        enriched_data.append(new_row)
        
        # Update log display
        log_display = '<div class="log-container">\n'
        for level, message in st.session_state.logs:
            log_display += f'<div class="log-{level}">{message}</div>\n'
        log_display += '</div>'
        log_container.markdown(log_display, unsafe_allow_html=True)
        
        time.sleep(0.05)  # Small delay for UI updates
    
    enriched_df = pd.DataFrame(enriched_data)
    
    st.session_state.processing_complete = True
    progress_bar.progress(1.0)
    status_text.empty()
    
    # Show failed items if any
    if st.session_state.failed_asins:
        failed_count = len(st.session_state.failed_asins)
        st.markdown(f"""
        <div class="failed-asin-list">
            <div class="failed-asin-title">⚠️ No image URLs found for {failed_count} items:</div>
            <div>
        """, unsafe_allow_html=True)
        
        for failed_item in st.session_state.failed_asins:
            st.markdown(f'<span class="failed-asin-item">{failed_item}</span>', unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    add_log(f"Processing complete! Processed {len(enriched_data)} items", "success")
    return enriched_df

# Function to process Excel format with Listing ID and url columns
def process_excel_format_data(df, max_rows=None):
    """Process Excel with 'Listing ID' and 'url' columns"""
    
    if max_rows is not None and max_rows > 0 and max_rows < len(df):
        df = df.head(max_rows)
    
    st.session_state.logs = []
    st.session_state.failed_asins = []
    st.session_state.processing_complete = False
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_expander = st.expander("Processing Log (Live)", expanded=True)
    log_container = log_expander.empty()
    
    # Find the correct column names (case insensitive)
    listing_id_col = None
    url_col = None
    
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'listing' in col_lower and 'id' in col_lower:
            listing_id_col = col
        elif col_lower == 'url':
            url_col = col
    
    if not listing_id_col or not url_col:
        st.error("Could not find 'Listing ID' and 'url' columns in the Excel file.")
        return None
    
    # Clean the dataframe
    df_clean = df.dropna(how='all').copy()
    total_rows = len(df_clean)
    
    status_text.text(f"Processing {total_rows} Excel rows...")
    add_log(f"Starting processing of {total_rows} Excel rows with Listing ID and URL columns")
    add_log(f"Using columns: '{listing_id_col}' and '{url_col}'")
    
    enriched_data = []
    
    for index, row in df_clean.iterrows():
        progress = (index + 1) / total_rows
        progress_bar.progress(progress)
        status_text.text(f"Processing {index + 1} of {total_rows} images ({int(progress*100)}%)")
        
        # Extract data from row
        listing_id = row[listing_id_col] if pd.notna(row[listing_id_col]) else f"Item_{index + 1}"
        image_url = row[url_col] if pd.notna(row[url_col]) else ''
        
        # Convert to string and clean
        listing_id = str(listing_id).strip()
        image_url = str(image_url).strip()
        
        # Validate image URL
        valid_url = False
        if image_url and image_url != 'nan' and 'http' in image_url.lower():
            if any(ext in image_url.lower() for ext in ['.jpg', '.png', '.jpeg', '.gif', '.webp']):
                valid_url = True
        
        # Create enriched row with all original data plus new fields
        new_row = row.to_dict()
        new_row.update({
            'Listing_ID': listing_id,
            'Product_Title': f"Excel Item {listing_id}",
            'Product_Price': 'See Details',
            'Product_Image_URL': image_url if valid_url else '',
            'Product_Description': 'Excel imported item',
            'Product_Rating': 'N/A',
            'Fetch_Success': valid_url,
            'Product_Link': f"https://example.com/item/{listing_id}",  # Generic link
            'Error': None if valid_url else 'Invalid or missing image URL'
        })
        
        if not valid_url:
            st.session_state.failed_asins.append(listing_id)
            add_log(f"Invalid image URL for Listing ID: {listing_id}", "warning")
        else:
            add_log(f"Valid image URL found for Listing ID: {listing_id}", "success")
        
        enriched_data.append(new_row)
        
        # Update log display after every row
        log_display = '<div class="log-container">\n'
        for level, message in st.session_state.logs:
            log_display += f'<div class="log-{level}">{message}</div>\n'
        log_display += '</div>'
        log_container.markdown(log_display, unsafe_allow_html=True)
        
        time.sleep(0.1)  # Slightly longer delay to ensure UI updates
        
    enriched_df = pd.DataFrame(enriched_data)
    
    st.session_state.processing_complete = True
    progress_bar.progress(1.0)
    status_text.empty()
    
    # Show failed items if any
    if st.session_state.failed_asins:
        failed_count = len(st.session_state.failed_asins)
        st.markdown(f"""
        <div class="failed-asin-list">
            <div class="failed-asin-title">⚠️ Invalid image URLs found for {failed_count} items:</div>
            <div>
        """, unsafe_allow_html=True)
        
        for failed_item in st.session_state.failed_asins[:10]:  # Show max 10
            st.markdown(f'<span class="failed-asin-item">{failed_item}</span>', unsafe_allow_html=True)
        
        if failed_count > 10:
            st.markdown(f'<span class="failed-asin-item">... and {failed_count - 10} more</span>', unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    add_log(f"Processing complete! Processed {len(enriched_data)} items", "success")
    # Final log update
    log_display = '<div class="log-container">\n'
    for level, message in st.session_state.logs:
        log_display += f'<div class="log-{level}">{message}</div>\n'
    log_display += '</div>'
    log_container.markdown(log_display, unsafe_allow_html=True)
    
    return enriched_df

# Function to process CSV data (updated to handle new Excel format)
def process_csv_data(df, max_rows=None):
    csv_type = detect_csv_type(df)
    
    if csv_type == 'amazon':
        if not any(col.lower() in ['asin', 'sku'] for col in df.columns):
            st.error("The CSV file must contain an 'Asin' column for Amazon products.")
            return None
        return process_amazon_data(df, max_rows)
    elif csv_type == 'excel_format':
        return process_excel_format_data(df, max_rows)
    elif csv_type == 'direct_urls':
        return process_direct_urls_data(df, max_rows)
    else:
        st.error("Could not detect CSV format. Please ensure your file contains either 'Asin' column for Amazon products, 'Listing ID' and 'url' columns for Excel format, or direct image URLs.")
        return None

# Function to process Amazon data (original function renamed)
def process_amazon_data(df, max_rows=None):
    if max_rows is not None and max_rows > 0 and max_rows < len(df):
        df = df.head(max_rows)
    
    st.session_state.logs = []
    st.session_state.failed_asins = []
    st.session_state.processing_complete = False
    st.session_state.current_processing_id = 0
    st.session_state.total_processing_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    processing_status = st.empty()
    log_expander = st.expander("Processing Log (Live)", expanded=True)
    log_container = log_expander.empty()
    
    log_container.markdown('<div class="log-container">', unsafe_allow_html=True)
    
    unique_asins = df['Asin'].unique()
    total_asins = len(unique_asins)
    
    status_text.text(f"Processing {total_asins} unique Amazon products...")
    add_log(f"Starting processing of {total_asins} unique ASINs")
    
    log_queue = queue.Queue()
    
    def process_log_queue(log_queue):
        while not log_queue.empty():
            try:
                item = log_queue.get()
                
                if isinstance(item, tuple) and len(item) == 2:
                    level, message = item
                    st.session_state.logs.append((level, message))
                else:
                    st.session_state.logs.append(("error", f"Malformed log entry: {str(item)}"))
            except Exception as e:
                st.session_state.logs.append(("error", f"Error processing log entry: {str(e)}"))
    
    def process_batch(asins, start_index):
        product_details_dict = {}
        batch_log_queue = queue.Queue()
        
        for i, asin in enumerate(asins):
            processing_id = start_index + i + 1
            product_details = get_amazon_product_details(asin, batch_log_queue, processing_id, total_asins)
            product_details_dict[asin] = product_details
            
            if not product_details['success'] or not product_details['image_url']:
                st.session_state.failed_asins.append(asin)
        
        while not batch_log_queue.empty():
            log_queue.put(batch_log_queue.get())
        
        process_log_queue(batch_log_queue)
        
        return product_details_dict
    
    batch_size = 1
    all_product_details = {}
    
    for i in range(0, len(unique_asins), batch_size):
        batch_asins = unique_asins[i:i+batch_size]
        
        progress = i / len(unique_asins)
        progress_bar.progress(progress)
        status_text.text(f"Processing batch {i//batch_size + 1} of {(len(unique_asins) + batch_size - 1) // batch_size}")
        
        processing_status.markdown(f"""
        <div class="processing-indicator">
            Processing ID: <span class="processing-id">{i+1}</span> / <span class="processing-total">{len(unique_asins)}</span>
        </div>
        """, unsafe_allow_html=True)
        
        batch_results = process_batch(batch_asins, i)
        all_product_details.update(batch_results)
        
        while not log_queue.empty():
            level, message = log_queue.get()
            st.session_state.logs.append((level, message))
        
        log_display = '<div class="log-container">\n'
        for level, message in st.session_state.logs:
            log_display += f'<div class="log-{level}">{message}</div>\n'
        log_display += '</div>'
        log_container.markdown(log_display, unsafe_allow_html=True)
        
        progress = (i + len(batch_asins)) / len(unique_asins)
        progress_bar.progress(progress)
        status_text.text(f"Processed {i + len(batch_asins)} of {len(unique_asins)} products ({int(progress*100)}%)")
        
        time.sleep(0.1)
    
    enriched_data = []
    
    for _, row in df.iterrows():
        asin = row['Asin']
        product_info = all_product_details.get(asin, {
            'asin': asin,
            'title': 'Product information not available',
            'price': 'N/A',
            'image_url': '',
            'success': False,
            'error': 'Processing skipped'
        })
        
        new_row = row.to_dict()
        new_row.update({
            'Product_Title': product_info['title'],
            'Product_Price': product_info['price'],
            'Product_Image_URL': product_info['image_url'],
            'Product_Description': 'N/A',  # Simplified - no longer fetching
            'Product_Rating': 'N/A',       # Simplified - no longer fetching
            'Fetch_Success': product_info['success'],
            'Product_Link': f"https://www.amazon.com/dp/{asin}",
            'Error': product_info.get('error', None)
        })
        
        enriched_data.append(new_row)
    
    enriched_df = pd.DataFrame(enriched_data)
    
    st.session_state.processing_complete = True
    
    progress_bar.progress(1.0)
    status_text.empty()
    processing_status.empty()
    
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

# Function to display fullscreen grid
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
    
    import streamlit.components.v1 as components
    
    exit_container = st.container()
    with exit_container:
        if st.button("✕", key="exit_fullscreen_amazon", help="Exit fullscreen"):
            st.session_state.fullscreen_mode = False
            st.rerun()
    
    html_content = """
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        
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
        <div class="fullscreen-gallery-grid">
    """
    
    for i, product in filtered_df.iterrows():
        image_url = product['Product_Image_URL']
        asin = product['Asin']
        
        if not image_url:
            image_url = "https://placehold.co/200x200?text=No+Image"
            
        html_content += f"""
        <div class="gallery-item" style="--item-index: {i}">
            <img src="{image_url}" alt="Product {asin}">
            <div class="asin-tooltip">{asin}</div>
        </div>
        """
    
    html_content += """
        </div>
    </div>
    
    <script>
        document.addEventListener('keydown', function(event) {
            if (event.key === "Escape") {
                window.parent.location.reload();
            }
        });
        document.addEventListener('DOMContentLoaded', function() {
            const streamlitElements = document.querySelectorAll('.stApp > div:not(.element-container), header, footer, .stToolbar');
            streamlitElements.forEach(el => {
                el.style.display = 'none';
            });
            
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
    
    components.html(html_content, height=1000, scrolling=True)

# Function to display product grid
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
    
    import streamlit.components.v1 as components
    
    html_content = """
    <style>
        .image-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            grid-auto-rows: 1fr;
            gap: 4px;
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
    
    for i, product in filtered_df.iterrows():
        image_url = product['Product_Image_URL']
        
        if not image_url:
            image_url = "https://placehold.co/200x200?text=No+Image"
            
        html_content += f"""
        <div class="grid-item">
            <img src="{image_url}" alt="Product">
        </div>
        """
    
    html_content += """
        </div>
    </div>
    """
    
    components.html(html_content, height=800, scrolling=True)

# Function to render the Amazon Grid tab
def render_amazon_grid_tab():
    if st.session_state.processed_data is None:
        st.warning("No data has been processed yet. Please upload and process a CSV file in the Upload tab.")
        return
    
    # Check if processed data is Amazon data
    csv_type = detect_csv_type(st.session_state.processed_data)
    if csv_type != 'amazon':
        st.warning("This tab is for Amazon products only. Please use the Excel Grid Images tab for other formats.")
        return
    
    st.markdown("""
    <div class="filters-panel">
        <h3>Amazon Grid Images</h3>
        <p>Amazon product images in a grid layout with full search and filter capabilities</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input("Search by product name, description, or ASIN", key="amazon_grid_search")
    
    with col2:
        min_price = st.number_input("Min Price ($)", min_value=0, value=0, key="amazon_grid_min_price")
    
    with col3:
        max_price = st.number_input("Max Price ($)", min_value=0, value=10000, key="amazon_grid_max_price")
    
    with col4:
        fullscreen_button = st.button("🖼️ Full Screen View", key="amazon_grid_fullscreen_btn", help="View images in a fullscreen 7-column grid")
    
    sort_options = ["None", "Price (Low to High)", "Price (High to Low)", "Title (A-Z)", "Title (Z-A)"]
    sort_by = st.selectbox("Sort by", sort_options, key="amazon_grid_sort")
    
    total_products = len(st.session_state.processed_data)
    st.write(f"Displaying images for {total_products} Amazon products in 5-column grid")
    
    if fullscreen_button:
        st.session_state.fullscreen_mode = True
        st.rerun()

    if st.session_state.fullscreen_mode:
        display_fullscreen_grid(
            st.session_state.processed_data,
            search_term=search_term if search_term else None,
            min_price=min_price if min_price > 0 else None,
            max_price=max_price if max_price < 10000 else None,
            sort_by=sort_by if sort_by != "None" else None
        )
        
    else:
        display_product_grid(
            st.session_state.processed_data,
            search_term=search_term,
            min_price=min_price if min_price > 0 else None,
            max_price=max_price if max_price < 10000 else None,
            sort_by=sort_by if sort_by != "None" else None
        )
    
    # Export button
    try:
        if st.download_button(
            label="Export Amazon Data to CSV",
            data=st.session_state.processed_data.to_csv(index=False),
            file_name="amazon_products_grid.csv",
            mime="text/csv",
            key="amazon_grid_export_unique"
        ):
            st.success("Amazon data exported successfully!")
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")

# Function to render the Excel Grid tab (no sorting/filtering)
# Function to render the Excel Grid tab (no sorting/filtering)
def render_excel_grid_tab():
    if st.session_state.processed_data is None:
        st.warning("No data has been processed yet. Please upload and process a CSV file in the Upload tab.")
        return
    
    # Check if processed data is direct URLs or Excel format
    csv_type = detect_csv_type(st.session_state.processed_data)
    if csv_type not in ['direct_urls', 'excel_format']:
        st.warning("This tab is for Excel files with direct image URLs. Please use the Amazon Grid Images tab for Amazon products.")
        return
    
    st.markdown("""
    <div class="filters-panel">
        <h3>Excel Grid Images</h3>
        <p>Simple grid view of images from Excel file - no sorting or filtering</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        total_products = len(st.session_state.processed_data)
        st.write(f"Displaying {total_products} images from Excel file in 5-column grid")
    
    with col2:
        fullscreen_button = st.button("🖼️ Full Screen View", key="excel_grid_fullscreen_btn", help="View images in a fullscreen 7-column grid")
    
    if fullscreen_button:
        st.session_state.fullscreen_mode = True
        st.rerun()
    
    if st.session_state.fullscreen_mode:
        display_simple_fullscreen_grid(st.session_state.processed_data)
    else:
        display_simple_product_grid(st.session_state.processed_data)
    
    # Export button
    try:
        if st.download_button(
            label="Export Excel Data to CSV",
            data=st.session_state.processed_data.to_csv(index=False),
            file_name="excel_images_grid.csv",
            mime="text/csv",
            key="excel_grid_export_unique"
        ):
            st.success("Excel data exported successfully!")
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")
        
        
        
# Simple grid display functions (no filtering/sorting)
def display_simple_product_grid(df):
    if df is None or df.empty:
        st.warning("No data available to display.")
        return
    
    import streamlit.components.v1 as components
    
    html_content = """
    <style>
        .image-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            grid-auto-rows: 1fr;
            gap: 4px;
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
    
    for i, product in df.iterrows():
        image_url = product['Product_Image_URL']
        
        if not image_url:
            image_url = "https://placehold.co/200x200?text=No+Image"
            
        html_content += f"""
        <div class="grid-item">
            <img src="{image_url}" alt="Product">
        </div>
        """
    
    html_content += """
        </div>
    </div>
    """
    
    components.html(html_content, height=800, scrolling=True)

def display_simple_fullscreen_grid(df):
    if df is None or df.empty:
        st.warning("No data available to display.")
        return
    
    import streamlit.components.v1 as components
    exit_container = st.container()
    with exit_container:
        if st.button("✕", key="exit_fullscreen_excel", help="Exit fullscreen"):
            st.session_state.fullscreen_mode = False
            st.rerun()
    html_content = """
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        
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
        <div class="fullscreen-gallery-grid">
    """
    
    for i, product in df.iterrows():
        image_url = product['Product_Image_URL']
        
        if not image_url:
            image_url = "https://placehold.co/200x200?text=No+Image"
            
        html_content += f"""
        <div class="gallery-item" style="--item-index: {i}">
            <img src="{image_url}" alt="Product">
        </div>
        """
    
    html_content += """
        </div>
    </div>
    
    <script>
        document.addEventListener('keydown', function(event) {
            if (event.key === "Escape") {
                window.parent.location.reload();
            }
        });
        document.addEventListener('DOMContentLoaded', function() {
            const streamlitElements = document.querySelectorAll('.stApp > div:not(.element-container), header, footer, .stToolbar');
            streamlitElements.forEach(el => {
                el.style.display = 'none';
            });
            
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
    
    components.html(html_content, height=1000, scrolling=True)

def render_upload_tab():
    st.markdown("""
    <div class="upload-container">
        <div class="upload-icon">📂</div>
        <h3>Upload your CSV file</h3>
        <p><strong>Supported formats:</strong></p>
        <p>• Amazon ASINs: CSV with 'Asin' column</p>
        <p>• Excel Format: CSV/Excel with 'Listing ID' and 'url' columns</p>
        <p>• Direct Image URLs: CSV with direct links to .jpg/.png images</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=["csv", "xlsx", "xls"], key="main_csv_uploader")
    
    process_limit = st.number_input(
        "Limit number of rows to process (leave at 0 to process all):",
        min_value=0,
        value=0,
        step=1,
        help="Set a limit on how many rows to process. This can be useful for testing or to reduce processing time.",
        key="process_limit_input"
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                # Special handling for Excel files
                # Load the Excel file to get all sheet names
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names
                if not sheet_names:
                    st.error("No sheets found in the Excel file.")
                    return
                
                # Read the last sheet
                last_sheet = sheet_names[-1]
                df = pd.read_excel(uploaded_file, sheet_name=last_sheet)
                
                # Handle unnamed columns by giving them generic names
                df.columns = [f'Column_{i}' if col.startswith('Unnamed:') else col for i, col in enumerate(df.columns)]
                
                # Skip rows that are entirely NaN
                df = df.dropna(how='all')
                
                # Reset index after dropping rows
                df = df.reset_index(drop=True)
            
            with st.expander("Preview Raw Data"):
                preview_df = df.copy()
                for col in preview_df.columns:
                    if preview_df[col].dtype == 'object':
                        preview_df[col] = preview_df[col].astype(str).str.strip()
                
                st.dataframe(preview_df)
                
                st.markdown("### Raw JSON Data (First 5 Records)")
                st.markdown("""
                <div class="raw-data-container">
                <pre>
                {}
                </pre>
                </div>
                """.format(df.head(5).to_json(orient='records', indent=2)), unsafe_allow_html=True)
            
            # Detect CSV type and show info
            csv_type = detect_csv_type(df)
            total_rows = len(df)
            
            if csv_type == 'amazon':
                # Find the ASIN column (case insensitive)
                asin_col = None
                for col in df.columns:
                    if col.lower() in ['asin', 'sku']:
                        asin_col = col
                        break
                
                if asin_col:
                    unique_asins = df[asin_col].nunique()
                    st.info(f"📦 **Amazon CSV detected** - File contains {total_rows} rows with {unique_asins} unique ASINs in column '{asin_col}'.")
                else:
                    st.info(f"📦 **Amazon CSV detected** - File contains {total_rows} rows.")
                    
            elif csv_type == 'excel_format':
                st.info(f"📋 **Excel Format detected** - File contains {total_rows} rows with 'Listing ID' and 'url' columns (from last sheet: '{last_sheet}').")
                # Show sample of the data
                listing_id_col = None
                url_col = None
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if 'listing' in col_lower and 'id' in col_lower:
                        listing_id_col = col
                    elif col_lower == 'url':
                        url_col = col
                
                if listing_id_col and url_col:
                    sample_data = []
                    for _, row in df.head(3).iterrows():
                        if pd.notna(row[listing_id_col]) and pd.notna(row[url_col]):
                            sample_data.append(f"ID: {row[listing_id_col]} → URL: {str(row[url_col])[:50]}...")

                            
            elif csv_type == 'direct_urls':
                # Count how many rows have image URLs
                url_count = 0
                sample_urls = []
                for _, row in df.head(10).iterrows():  # Check first 10 rows
                    for value in row:
                        if pd.notna(value):
                            value_str = str(value).strip()
                            if ('http' in value_str.lower() and 
                                ('.jpg' in value_str.lower() or '.png' in value_str.lower() or '.jpeg' in value_str.lower())):
                                url_count += 1
                                if len(sample_urls) < 3:
                                    sample_urls.append(value_str[:50] + "..." if len(value_str) > 50 else value_str)
                                break
                
                st.info(f"🖼️ **Direct Image URLs detected** - File contains {total_rows} rows with image URLs found (from last sheet: '{last_sheet}').")
                if sample_urls:
                    st.write("**Sample URLs found:**")
                    for url in sample_urls:
                        st.write(f"• {url}")
                        
            else:
                st.warning(f"⚠️ **Unknown format** - Could not detect CSV type.")
                st.write("**Debug Info:**")
                st.write(f"- Columns: {list(df.columns)}")
                st.write(f"- First row sample: {df.iloc[0].to_dict()}")
                
                # Show suggestions based on what we found
                has_numeric_first_col = df.iloc[:, 0].apply(lambda x: str(x).replace('-', '').replace('_', '').isdigit()).any()
                has_urls_anywhere = False
                
                for col in df.columns:
                    if df[col].astype(str).str.contains('http', case=False, na=False).any():
                        has_urls_anywhere = True
                        break
                
                st.write("**Suggestions:**")
                if has_numeric_first_col and has_urls_anywhere:
                    st.write("• This looks like it might be direct image URLs with ID numbers")
                elif not has_numeric_first_col and not has_urls_anywhere:
                    st.write("• For Amazon: Ensure you have an 'ASIN' column")
                    st.write("• For direct URLs: Ensure you have HTTP image links (.jpg, .png, etc.)")
            
            if process_limit > 0 and process_limit < total_rows:
                st.warning(f"You've chosen to process only {process_limit} rows out of {total_rows} total rows.")
            
            if st.button("Process and Fetch Product Details", key="process_button_unique", help="Click to start processing the uploaded file"):
                if csv_type == 'unknown':
                    st.error("Could not detect file format. Please ensure your file contains either 'Asin' column for Amazon products or direct image URLs.")
                else:
                    with st.spinner("Processing data and fetching details..."):
                        max_rows = process_limit if process_limit > 0 else None
                        st.session_state.processed_data = process_csv_data(df, max_rows)
                        
                        if st.session_state.processed_data is not None:
                            if csv_type == 'amazon':
                                st.success("Amazon data processed successfully! Switch to Amazon Grid Images tab to view results.")
                            else:
                                st.success(f"Data from last sheet ('{last_sheet}') processed successfully! Switch to Excel Grid Images tab to view results.")
                        else:
                            st.error("Failed to process data. Please check your file format.")
        
        except Exception as e:
            st.error(f"Error reading the file: {str(e)}")
            st.markdown("""
            <div class="raw-data-container">
            <p>Troubleshooting tips:</p>
            <ul>
                <li>Ensure your file is properly formatted (CSV or Excel)</li>
                <li>For Amazon: Check that your file contains an 'Asin' column</li>
                <li>For Direct URLs: Ensure your file contains direct links to images (.jpg, .png, .jpeg)</li>
                <li>Verify there are no special characters or encoding issues</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

# Main app function
def main():
    add_custom_css()
    
    st.markdown("""
    <div class="main-header">
        <h1>Universal <span class="accent-text">Product Viewer</span></h1>
        <div class="subtitle">Upload CSV files with Amazon ASINs or direct image URLs to view products in grid format</div>
    </div>
    """, unsafe_allow_html=True)
    
    query_params = st.query_params
    if 'fullscreen' in query_params and query_params.get('fullscreen') == 'true':
        if st.session_state.processed_data is not None:
            search_term = query_params.get('search', '')
            min_price = float(query_params.get('min_price', 0))
            max_price = float(query_params.get('max_price', 10000))
            sort_by = query_params.get('sort_by', 'None')
            
            display_fullscreen_grid(
                st.session_state.processed_data,
                search_term=search_term if search_term else None,
                min_price=min_price if min_price > 0 else None,
                max_price=max_price if max_price < 10000 else None,
                sort_by=sort_by if sort_by != "None" else None
            )
            return
    
    # Now 3 tabs - Upload, Amazon Grid, and Excel Grid
    tab_names = ["📤 Upload CSV", "📦 Amazon Grid Images", "📋 Excel Grid Images"]
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        render_upload_tab()
    
    with tabs[1]:
        render_amazon_grid_tab()
    
    with tabs[2]:
        render_excel_grid_tab()
    
    st.markdown("""
    <div class="footer">
        <p>Universal Product Viewer App | Support for Amazon ASINs & Direct Image URLs</p>
        <p>Enhanced for reliable product image retrieval and grid display from multiple sources</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
