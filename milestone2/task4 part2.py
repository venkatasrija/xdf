import os
import csv
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://directory.wigan.gov.uk/kb5/wigan/fsd/'
MAIN_URL = "https://directory.wigan.gov.uk"

def fetch_page_content(url):
    """Fetch the HTML content of a given URL."""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def sanitize_folder_name(folder_name):
    """Sanitize folder names to avoid illegal characters."""
    return folder_name.strip().replace(' ', '_').replace('/', '_')

def create_folder(folder_name):
    """Create a folder if it doesn't exist."""
    os.makedirs(folder_name, exist_ok=True)
    print(f"Folder ready: {folder_name}")

def scrape_records_from_page(soup):
    """Scrape services/records from a page."""
    records = []
    services = soup.find_all("div", class_="result_hit_header")

    for service in services:
        title_tag = service.find("a", class_="flex-grow-1 text-dark font-weight-bold")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"
        link = MAIN_URL + title_tag["href"] if title_tag else "N/A"
        
        time_tag = service.find("div", class_="clearfix mt-1 mb-3 font-weight-bold")
        time = time_tag.get_text(strip=True) if time_tag else "N/A"
        
        description_tag = service.find_next("div", class_="mb-2")
        description = description_tag.get_text(strip=True) if description_tag else "No description available"
        
        address_tag = service.find_next("div", class_="mb-3 text-muted")
        address = address_tag.get_text(strip=True, separator=", ") if address_tag else "No address available"
        
        contact_info = service.find_next("div", class_="contact-links")
        phone = contact_info.find("a", href=lambda href: href and "tel" in href)
        phone = phone.get_text(strip=True) if phone else "No phone available"
        
        email = contact_info.find("a", href=lambda href: href and "mailto" in href)
        email = email["href"].replace("mailto:", "") if email else "No email available"
        
        website_tag = service.find("a", href=lambda href: href and href.startswith("http"))
        website = website_tag["href"] if website_tag else "No website available"
        
        records.append({
            "Title": title,
            "Link": link,
            "Time": time,
            "Description": description,
            "Address": address,
            "Phone": phone,
            "Email": email,
            "Website": website
        })
    
    return records

def save_records_to_csv(records, folder_path):
    """Save the scraped records to a CSV file."""
    if not records:
        print("No records to save.")
        return
    
    output_file = os.path.join(folder_path, 'scraped_records.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Records saved to {output_file}")

def parse_category_block(category_block, parent_folder):
    """Process a category block and handle subcategories or scrape records."""
    try:
        category_link = category_block.find('a')['href']
        category_name = sanitize_folder_name(category_block.find('div', class_='card-body').text.strip())
        category_folder = os.path.join(parent_folder, category_name)
        create_folder(category_folder)
        category_url = BASE_URL + category_link
        handle_subcategories(category_url, category_folder)
    except Exception as e:
        print(f"Error parsing category block: {e}")

def handle_subcategories(url, parent_folder):
    """Recursively handle subcategories or scrape records if no subcategories are found."""
    soup = fetch_page_content(url)
    if not soup:
        return

    subcategories = soup.find_all('div', class_='category-block')

    if not subcategories:
        print(f"No more subcategories at: {url}. Scraping records.")
        records = scrape_records_from_page(soup)
        save_records_to_csv(records, parent_folder)
        return

    for subcategory in subcategories:
        parse_category_block(subcategory, parent_folder)

    nested_links = soup.find_all('a', class_='btn-health')

    if not nested_links:
        print(f"No more nested links at: {url}. Recursion ends.")
        return

    for link in nested_links:
        subcategory_url = BASE_URL + link['href']
        print(f"Going deeper: {subcategory_url}")
        handle_subcategories(subcategory_url, parent_folder)

def main():
    """Main function to start the scraping process."""
    main_page_url = BASE_URL + "home.page"
    soup = fetch_page_content(main_page_url)
    
    if soup:
        category_blocks = soup.find_all('li', class_='category-block')
        base_folder = "Wigan_Categories"
        create_folder(base_folder)
        
        for category_block in category_blocks:
            parse_category_block(category_block, base_folder)
    else:
        print("Failed to fetch the main page content.")

if __name__ == "__main__":
    main()
