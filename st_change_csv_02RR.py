import requests
import streamlit as st
import os
from dotenv import load_dotenv

# Load token from .env file if available
load_dotenv()

# Initialize session state variables
if 'token_checked' not in st.session_state:
    st.session_state.token_checked = False
if 'token_valid' not in st.session_state:
    st.session_state.token_valid = False
if 'repo_checked' not in st.session_state:
    st.session_state.repo_checked = False
if 'repo_valid' not in st.session_state:
    st.session_state.repo_valid = False
if 'file_checked' not in st.session_state:
    st.session_state.file_checked = False
if 'file_valid' not in st.session_state:
    st.session_state.file_valid = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'repo_data' not in st.session_state:
    st.session_state.repo_data = None
if 'file_data' not in st.session_state:
    st.session_state.file_data = None

st.title("GitHub Token Authorization Checker")

# Get token from environment variable or input
github_token = os.getenv('GITHUB_TOKEN')
if not github_token:
    github_token = st.text_input("Enter your GitHub Personal Access Token:", type="password")

# Check token function
def check_token():
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get("https://api.github.com/user", headers=headers)
    
    st.session_state.token_checked = True
    st.session_state.token_valid = (response.status_code == 200)
    
    if response.status_code == 200:
        st.session_state.user_data = response.json()
        
        # Get rate limit info
        rate_response = requests.get("https://api.github.com/rate_limit", headers=headers)
        if rate_response.status_code == 200:
            st.session_state.rate_data = rate_response.json()
    else:
        st.session_state.user_error = response.text

# Check repository function
def check_repository(repo_owner, repo_name):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    response = requests.get(repo_url, headers=headers)
    
    st.session_state.repo_checked = True
    st.session_state.repo_valid = (response.status_code == 200)
    
    if response.status_code == 200:
        st.session_state.repo_data = response.json()
    else:
        st.session_state.repo_error = response.text

# Check file function
def check_file(repo_owner, repo_name, file_path):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    response = requests.get(file_url, headers=headers)
    
    st.session_state.file_checked = True
    st.session_state.file_valid = (response.status_code == 200)
    
    if response.status_code == 200:
        st.session_state.file_data = response.json()
    else:
        st.session_state.file_error = response.text

# Reset function
def reset_all():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()
    # st.experimental_rerun()

# Main UI flow
if github_token:
    # Token test section
    st.subheader("Step 1: Test Token Authorization")
    if not st.session_state.token_checked:
        if st.button("Test Token Authorization"):
            with st.spinner("Checking token..."):
                check_token()
    
    if st.session_state.token_checked:
        if st.session_state.token_valid:
            st.success("✅ Token is valid and working!")
            if hasattr(st.session_state, 'rate_data'):
                rate_data = st.session_state.rate_data
                st.write(f"API Rate Limit: {rate_data['resources']['core']['limit']}")
                st.write(f"Remaining Calls: {rate_data['resources']['core']['remaining']}")
            
            if st.session_state.user_data:
                user_data = st.session_state.user_data
                st.write(f"Authenticated as: {user_data['login']}")
                st.write(f"User ID: {user_data['id']}")
                if 'name' in user_data and user_data['name']:
                    st.write(f"Name: {user_data['name']}")
        else:
            st.error("❌ Token authorization failed!")
            if hasattr(st.session_state, 'user_error'):
                st.text(st.session_state.user_error)
    
    # Repository test section
    if st.session_state.token_valid:
        st.subheader("Step 2: Test Repository Access")
        
        repo_owner = st.text_input("Repository Owner:", value=os.getenv('REPO_OWNER', ''))
        repo_name = st.text_input("Repository Name:", value=os.getenv('REPO_NAME', ''))
        
        if repo_owner and repo_name and not st.session_state.repo_checked:
            if st.button("Test Repository Access"):
                with st.spinner("Checking repository access..."):
                    check_repository(repo_owner, repo_name)
        
        if st.session_state.repo_checked:
            if st.session_state.repo_valid:
                st.success(f"✅ Successfully accessed repository: {repo_owner}/{repo_name}")
                if st.session_state.repo_data:
                    st.write(f"Repository ID: {st.session_state.repo_data['id']}")
                    st.write(f"Default Branch: {st.session_state.repo_data['default_branch']}")
            else:
                st.error(f"❌ Failed to access repository: {repo_owner}/{repo_name}")
                if hasattr(st.session_state, 'repo_error'):
                    st.text(st.session_state.repo_error)
        
        # File test section
        if st.session_state.repo_valid:
            st.subheader("Step 3: Test File Access")
            
            file_path = st.text_input("File Path:", value=os.getenv('FILE_PATH', ''))
            
            if file_path and not st.session_state.file_checked:
                if st.button("Test File Access"):
                    with st.spinner("Checking file access..."):
                        check_file(repo_owner, repo_name, file_path)
            
            if st.session_state.file_checked:
                if st.session_state.file_valid:
                    st.success(f"✅ Successfully accessed file: {file_path}")
                    if st.session_state.file_data:
                        st.write(f"File Size: {st.session_state.file_data.get('size', 'N/A')} bytes")
                        st.write(f"File Type: {st.session_state.file_data.get('type', 'N/A')}")
                else:
                    st.error(f"❌ Failed to access file: {file_path}")
                    if hasattr(st.session_state, 'file_error'):
                        st.text(st.session_state.file_error)

    # Add a reset button at the bottom
    if st.session_state.token_checked:
        if st.button("Start Over"):
            reset_all()

else:
    st.info("Please enter your GitHub Personal Access Token to check authorization.")