import streamlit as st
import pandas as pd
import requests
import json
import base64
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Check if running locally or remotely
def is_local():
    return os.path.exists('test.csv')

# GitHub repository details
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Get token from environment variable
REPO_OWNER = os.getenv('REPO_OWNER')  # Get owner from environment variable 
REPO_NAME = os.getenv('REPO_NAME')  # Get repo name from environment variable
FILE_PATH = os.getenv('FILE_PATH')  # Path to your CSV file in the repo

def read_csv_file_remote():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_info = response.json()
        content = base64.b64decode(file_info['content']).decode('utf-8')
        return pd.read_csv(pd.StringIO(content))
    else:
        st.error(f"Failed to fetch file: {response.json()}")
        return None

def read_csv_file_local():
    try:
        return pd.read_csv('test.csv')
    except Exception as e:
        st.error(f"Failed to read local CSV file: {str(e)}")
        return None

def read_csv_file():
    if is_local():
        return read_csv_file_local()
    else:
        return read_csv_file_remote()

def update_csv_file_remote(new_data):
    # Get the current content of the file
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Get the current file content
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_info = response.json()
        current_content = base64.b64decode(file_info['content']).decode('utf-8')
        # Update the CSV content
        updated_content = current_content + "\n" + new_data
        # Prepare the data for the update
        update_data = {
            "message": "Update CSV file",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": file_info['sha']  # Required to update the file
        }
        # Update the file
        update_response = requests.put(url, headers=headers, data=json.dumps(update_data))
        if update_response.status_code == 200:
            st.success("CSV file updated successfully!")
        else:
            st.error(f"Failed to update CSV file: {update_response.json()}")
    else:
        st.error(f"Failed to fetch file: {response.json()}")

def update_csv_file_local(new_data):
    try:
        with open('test.csv', 'a') as f:
            f.write('\n' + new_data)
        st.success("CSV file updated successfully!")
    except Exception as e:
        st.error(f"Failed to update local CSV file: {str(e)}")

def update_csv_file(new_data):
    if is_local():
        update_csv_file_local(new_data)
    else:
        update_csv_file_remote(new_data)

# Streamlit UI
st.title("Update CSV File on GitHub")

# Input for new data
new_data = st.text_area("Enter new data to append to the CSV (comma-separated):")

if st.button("Update CSV"):
    if new_data:
        update_csv_file(new_data)
    else:
        st.error("Please enter some data.")

# Add button to read and display CSV
if st.button("Read and Display CSV"):
    df = read_csv_file()
    if df is not None:
        st.write("Current CSV Content:")
        st.dataframe(df)