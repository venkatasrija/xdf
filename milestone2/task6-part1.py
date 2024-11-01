from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time

TARGET_RECORDS = 200

def get_job_data_from_page(content):
    """Extracts job data from a page's HTML content."""
    soup = BeautifulSoup(content, "html.parser")
    job_cards = soup.select("ul[class*='JobCardGrid-jobCardList'] li")
    
    job_data = []
    for job in job_cards:
        try:
            # Extract job details
            title = job.select_one("h3[class*='JobCard-jobTitle']").get_text(strip=True)
            company = job.select_one("p[class*='JobCard-company']").get_text(strip=True)
            location = job.select_one("p[class*='JobCard-jobLocation']").get_text(strip=True)
            description = job.select_one("p[class*='JobCard-jobDescription']").get_text(strip=True)
            posted_on = job.select_one("span[class*='JobCard-time']").get_text(strip=True)

            job_data.append({
                "Job Title": title,
                "Company": company,
                "Location": location,
                "Job Summary": description,
                "Posted Date": posted_on
            })
        except Exception as e:
            print(f"Error extracting data for a job card: {e}")
            continue
    return job_data

def scrape_behance_jobs():
    """Main function to handle browser setup and job scraping logic."""
    job_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to the job listings page
        page.goto("https://www.behance.net/joblist?tracking_source=nav20")
        time.sleep(2)  # Wait for initial page load

        while len(job_data) < TARGET_RECORDS:
            # Scroll down and wait for new content to load
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # Extract the current page content
            content = page.content()
            page_job_data = get_job_data_from_page(content)
            job_data.extend(page_job_data)

            # Break if the target record count is reached
            if len(job_data) >= TARGET_RECORDS:
                job_data = job_data[:TARGET_RECORDS]  # Trim excess data
                break

        browser.close()

    # Convert to DataFrame and save to CSV
    df = pd.DataFrame(job_data)
    df.to_csv('behance_job_data.csv', index=False)
    print("Scraping completed! Data saved to behance_job_data.csv.")
    print(df)

# Run the scraper
if __name__ == "__main__":
    scrape_behance_jobs()
