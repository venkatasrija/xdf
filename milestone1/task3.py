import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO

# Function to scrape library data from the given URL
def scrape_libraries(state):
    url = f"https://publiclibraries.com/state/{state}/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    libraries_table = soup.find('table')
    headers = ['City', 'Library', 'Address', 'Zip', 'Phone']
    rows = []
    
    for row in libraries_table.find_all('tr')[1:]:
        columns = row.find_all('td')
        city = columns[0].text.strip()
        library = columns[1].text.strip()
        address = columns[2].text.strip()
        zip_code = columns[3].text.strip()
        phone = columns[4].text.strip()
        rows.append([city, library, address, zip_code, phone])

    return pd.DataFrame(rows, columns=headers)

# Streamlit UI
st.title("Library Scraper")

# Dropdown to select the state
state = st.selectbox("Select a State", [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming"
])

# Scrape button
if st.button("Scrape Libraries"):
    data = scrape_libraries(state.lower().replace(' ', '-'))
    st.success(f"Data scraped successfully for {state}!")

    # Displaying the data in a table
    st.dataframe(data)

    # Download options
    st.markdown("### Download Options:")
    csv = data.to_csv(index=False).encode('utf-8')

    # Create an in-memory BytesIO object for Excel
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name='Libraries')
    excel_buffer.seek(0)  # Move to the beginning of the BytesIO object
    excel = excel_buffer.getvalue()  # Get the value of the BytesIO object

    json_data = data.to_json(orient='records')

    st.download_button(label="Download as CSV", data=csv, file_name=f"{state}_libraries.csv", mime="text/csv")
    st.download_button(label="Download as Excel", data=excel, file_name=f"{state}_libraries.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button(label="Download as JSON", data=json_data, file_name=f"{state}_libraries.json", mime="application/json")
