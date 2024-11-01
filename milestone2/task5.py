import os
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

# Function to ensure the directory exists
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to sanitize filenames
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '_', name).strip()

# Function to save DataFrame to various formats
def save_dataframe(df, base_filename):
    csv_file = f"{base_filename}.csv"
    xml_file = f"{base_filename}.xml"
    json_file = f"{base_filename}.json"
    
    df.to_csv(csv_file, index=False, encoding='utf-8')
    df.to_xml(xml_file, index=False, encoding='utf-8', parser='etree')
    df.to_json(json_file, orient='records', lines=True)
    
    return csv_file, xml_file, json_file

# Function to extract data from a BeautifulSoup object
def extract_entries(soup):
    entries = []
    for result in soup.select("[id^='hit-']"):
        entry = {
            "Title": result.select_one("h3 a").get_text(strip=True) if result.select_one("h3 a") else None,
            "Schedule": result.select_one(".mt-1.mb-3.font-weight-bold").get_text(strip=True) if result.select_one(".mt-1.mb-3.font-weight-bold") else None,
            "Description": result.select_one("div.result-hit-body > div.mb-2, div.mb-2").get_text(strip=True) if result.select_one("div.result-hit-body > div.mb-2, div.mb-2") else None,
            "Address": " ".join(span.get_text(strip=True) for span in result.select(".mb-1 .icon-text span")) if result.select(".mb-1 .icon-text span") else None,
            "Phone": result.select_one(".contact-links ul li:nth-child(1) span.comma_split").get_text(strip=True) if result.select_one(".contact-links ul li:nth-child(1) span.comma_split") else None,
            "Email": result.select_one(".contact-links ul li:nth-child(2) a")["href"] if result.select_one(".contact-links ul li:nth-child(2) a") else None,
            "Website": result.select_one(".contact-links ul li:nth-child(3) a")["href"] if result.select_one(".contact-links ul li:nth-child(3) a") else None
        }
        entries.append(entry)
    return pd.DataFrame(entries)

# Function to scrape all pages recursively
def scrape_pages(url, base_url):
    all_data = pd.DataFrame()
    while url:
        full_url = requests.compat.urljoin(base_url, url)
        response = requests.get(full_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_data = pd.concat([all_data, extract_entries(soup)], ignore_index=True)
        url = find_next_page(soup)
    return all_data

# Function to find the next page link
def find_next_page(soup):
    next_link = soup.select_one("nav > ol > li.page-item.active + li a")
    return next_link['href'] if next_link else None

# Function to get subcategories
def fetch_subcategories(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    categories = {}
    
    for block in soup.find_all(['li', 'div'], class_='category-block'):
        sub_link = block.find('a')
        if sub_link:
            name = sub_link.find('div', class_='card-body').text.strip()
            categories[name] = requests.compat.urljoin(url, sub_link['href'])
    return categories

# Recursive function to select category
def select_category(url):
    categories = fetch_subcategories(url)
    if categories:
        selected = st.selectbox("Select a Subcategory", list(categories.keys()))
        return select_category(categories[selected])
    return url

# Streamlit app interface
st.title("Wigan Directory Scraper")
st.write("Select a category and subcategory to scrape data from the Wigan directory.")

base_url = "https://directory.wigan.gov.uk/kb5/wigan/fsd/home.page"
final_url = select_category(base_url)

# If the button is clicked, start scraping
if st.button("Scrape Data"):
    with st.spinner("Scraping data..."):
        # Scrape the selected category/subcategory data
        scraped_data = scrape_pages(final_url, base_url)
        st.success("Data scraping completed!")

    # Display the scraped data in a table format
    st.dataframe(scraped_data)

    # Ensure the directory for saving files exists
    output_directory = 'Wigan_Scraped_Data'
    ensure_directory(output_directory)

    # Create a sanitized filename based on the selected category URL
    sanitized_filename = sanitize_filename(final_url)
    base_filename = os.path.join(output_directory, sanitized_filename)

    # Save the data to CSV, XML, and JSON
    csv_file, xml_file, json_file = save_dataframe(scraped_data, base_filename)

    # Provide download options for CSV, XML, and JSON files
    st.write("Download the scraped data:")

    col1, col2, col3 = st.columns(3)

    with col1:
        with open(csv_file, "rb") as f:
            st.download_button(label="Download CSV", data=f, file_name=f"{sanitized_filename}.csv")

    with col2:
        with open(xml_file, "rb") as f:
            st.download_button(label="Download XML", data=f, file_name=f"{sanitized_filename}.xml")

    with col3:
        with open(json_file, "rb") as f:
            st.download_button(label="Download JSON", data=f, file_name=f"{sanitized_filename}.json")
