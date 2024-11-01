import requests
from bs4 import BeautifulSoup
import os
import re

def create_folder(folder_name):
    """Creates a folder if it does not exist."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def sanitize_folder_name(folder_name):
    """Sanitizes the folder name to avoid invalid characters."""
    # Remove invalid characters and strip leading/trailing spaces
    return re.sub(r'[<>:"/\\|?*]', '', folder_name).strip()

def scrape_category(url, parent_folder):
    """Scrapes the category page and retrieves card-body names and hrefs."""
    try:
        # Fetch the content from the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all category blocks (either <li> or <div>)
        category_blocks = soup.find_all(['li', 'div'], class_='category-block')

        if not category_blocks:
            print(f"No category blocks found at {url}")
            return

        for block in category_blocks:
            link = block.find('a')
            if link:
                # Get the category name and href
                name = link.text.strip()
                href = link['href']

                # Sanitize the category name to create a valid folder name
                sanitized_name = sanitize_folder_name(name)

                # Create a folder for the category name
                category_folder = os.path.join(parent_folder, sanitized_name)
                create_folder(category_folder)

                # Full URL for the next category
                full_url = requests.compat.urljoin(url, href)
                scrape_category(full_url, category_folder)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")

# Entry point
if __name__ == "__main__":
    # Start URL (base URL)
    base_url = "https://directory.wigan.gov.uk/kb5/wigan/fsd/home.page"

    # Create a main folder to store all results
    main_folder = "Wigan Categories"
    create_folder(main_folder)

    # Start scraping from the base URL
    scrape_category(base_url, main_folder)