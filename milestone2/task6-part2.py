import streamlit as st
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time

# Target number of records
TARGET_RECORDS = 100

# Function to extract job data
def get_job_data_from_page(content):
    soup = BeautifulSoup(content, "html.parser")
    job_cards = soup.select("ul[class*='JobCardGrid-jobCardList'] li")
    
    job_data = []
    for job in job_cards:
        try:
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

# Function to scrape Behance jobs
def scrape_behance_jobs(keyword, target_records):
    job_data = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to job listings with search keyword
        url = f"https://www.behance.net/joblist?tracking_source=nav20&query={keyword}"
        page.goto(url)
        time.sleep(2)

        while len(job_data) < target_records:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            content = page.content()
            page_job_data = get_job_data_from_page(content)
            job_data.extend(page_job_data)

            if len(job_data) >= target_records:
                job_data = job_data[:target_records]
                break

        browser.close()

    df = pd.DataFrame(job_data)
    return df

# Placeholder function for assets (to be implemented if needed)
def scrape_behance_assets(keyword, target_records):
    # Implement scraping logic for assets here similar to scrape_behance_jobs
    # For demonstration, we'll return an empty DataFrame
    return pd.DataFrame(columns=["Asset Title", "Creator", "Description", "Posted Date"])

# Streamlit app interface
st.title("Behance Scraper")

# Choose scraping option: Jobs or Assets
scrape_option = st.selectbox("Choose what to scrape:", ["Jobs", "Assets"])

# Input for search keyword
search_keyword = st.text_input("Enter search keyword:", value="UI/UX")

# Input for number of records
num_records = st.number_input("Enter the number of records to scrape:", min_value=1, max_value=1000, value=30)

# Button to start scraping
if st.button("Scrape"):
    with st.spinner("Scraping data..."):
        if scrape_option == "Jobs":
            result_df = scrape_behance_jobs(search_keyword, num_records)
        else:
            result_df = scrape_behance_assets(search_keyword, num_records)

        st.success("Scraping completed!")

    # Display results
    if not result_df.empty:
        st.write(f"Here are the scraped {scrape_option.lower()} listings:")
        st.dataframe(result_df)

        # Option to download data as CSV
        csv = result_df.to_csv(index=False)
        st.download_button("Download data as CSV", data=csv, file_name=f"behance_{scrape_option.lower()}_data.csv", mime="text/csv")
    else:
        st.write("No data available to display.")
