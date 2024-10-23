import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# URL to scrape
base_url = "https://publiclibraries.com/state/"

# Function to get state URLs  
def get_state_urls(base_url):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all the state links
    state_links = soup.select('ul li a[href^="/state/"]')
    state_urls = {link.text: base_url + link['href'].split('/')[-1] for link in state_links}
    
    return state_urls

# Function to scrape library details from each state page
def scrape_state_libraries(state_url):
    response = requests.get(state_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    libraries = []
    # Assuming each library info is inside a div with the class "library"
    library_entries = soup.find_all('div', class_='library')

    for entry in library_entries:
        # Extracting city, library name, address, zip, phone, state
        try:
            city = entry.find('span', class_='city').text.strip()
            name = entry.find('span', class_='name').text.strip()
            address = entry.find('span', class_='address').text.strip()
            zip_code = entry.find('span', class_='zip').text.strip()
            phone = entry.find('span', class_='phone').text.strip()
            # State is inferred from the URL, not in the entry
            state = state_url.split('/')[-1].replace('-', ' ').title()

            libraries.append({
                'City': city,
                'Library': name,
                'Address': address,
                'Zip': zip_code,
                'Phone': phone,
                'State': state
            })
        except AttributeError:
            continue
     
    return libraries

# Function to save data to CSV file
def save_to_csv(state_name, libraries):
    if not os.path.exists('libraries_data'):
        os.makedirs('libraries_data')
    
    df = pd.DataFrame(libraries)
    csv_file = f"libraries_data/{state_name}.csv"
    df.to_csv(csv_file, index=False)
    print(f"Data saved to {csv_file}")

# Main function
def main():
    state_urls = get_state_urls(base_url)
    
    for state_name, state_url in state_urls.items():
        print(f"Scraping data for {state_name}")
        libraries = scrape_state_libraries(state_url)
        save_to_csv(state_name, libraries)

if __name__ == "__main__":
    main()
