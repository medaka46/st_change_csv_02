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
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'rate_data' not in st.session_state:
    st.session_state.rate_data = None
if 'response_json' not in st.session_state:
    st.session_state.response_json = None

st.title("GitHub Token Authorization Checker")

# Get token from environment variable or input
github_token = os.getenv('GITHUB_TOKEN')
if not github_token:
    github_token = st.text_input("Enter your GitHub Personal Access Token:", type="password")

# Function to check token
def check_token():
    with st.spinner("Checking token..."):
        # Make a request to GitHub API
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Try to get user information (requires authentication)
        response = requests.get("https://api.github.com/user", headers=headers)
        
        # Store results in session state
        st.session_state.token_checked = True
        st.session_state.token_valid = (response.status_code == 200)
        
        if response.status_code == 200:
            st.session_state.user_data = response.json()
            st.session_state.response_json = response.json()
            
            # Get rate limit info
            rate_response = requests.get("https://api.github.com/rate_limit", headers=headers)
            if rate_response.status_code == 200:
                st.session_state.rate_data = rate_response.json()
        else:
            st.session_state.response_text = response.text

# Function to test repository access
def test_repo_access(repo_owner, repo_name):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    repo_response = requests.get(repo_url, headers=headers)
    
    return repo_response

# Function to test file access
def test_file_access(repo_owner, repo_name, file_path):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    file_response = requests.get(file_url, headers=headers)
    
    return file_response

# Button to test the token
if github_token and not st.session_state.token_checked:
    if st.button("Test Token Authorization"):
        check_token()

# If token has been checked, show results
if st.session_state.token_checked:
    st.subheader("Authorization Test Results:")
    
    # Create columns for better display
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.token_valid:
            st.success("✅ Token is valid and working!")
            
            if st.session_state.rate_data:
                st.write("API Rate Limit:", st.session_state.rate_data['resources']['core']['limit'])
                st.write("Remaining Calls:", st.session_state.rate_data['resources']['core']['remaining'])
        else:
            st.error("❌ Token authorization failed!")
    
    with col2:
        # Show user information
        if st.session_state.token_valid and st.session_state.user_data:
            st.write("Authenticated as:", st.session_state.user_data['login'])
            st.write("User ID:", st.session_state.user_data['id'])
            if 'name' in st.session_state.user_data and st.session_state.user_data['name']:
                st.write("Name:", st.session_state.user_data['name'])
    
    # Show full response for debugging
    with st.expander("View Full API Response"):
        if st.session_state.token_valid:
            st.json(st.session_state.response_json)
        else:
            if hasattr(st.session_state, 'response_text'):
                st.text(st.session_state.response_text)
    
    # Test specific repository access if token is valid
    if st.session_state.token_valid:
        st.subheader("Test Repository Access:")
        repo_owner = st.text_input("Repository Owner:", value=os.getenv('REPO_OWNER', ''))
        repo_name = st.text_input("Repository Name:", value=os.getenv('REPO_NAME', ''))
        
        if repo_owner and repo_name:
            if st.button("Test Repository Access"):
                repo_response = test_repo_access(repo_owner, repo_name)
                
                if repo_response.status_code == 200:
                    st.success(f"✅ Successfully accessed repository: {repo_owner}/{repo_name}")
                    
                    # Test file access if a file path is provided
                    file_path = st.text_input("Test File Path (optional):", value=os.getenv('FILE_PATH', ''))
                    if file_path:
                        if st.button("Test File Access"):
                            file_response = test_file_access(repo_owner, repo_name, file_path)
                            
                            if file_response.status_code == 200:
                                st.success(f"✅ Successfully accessed file: {file_path}")
                            else:
                                st.error(f"❌ Failed to access file: {file_path}")
                                st.text(f"Status: {file_response.status_code}")
                                st.text(file_response.text)
                else:
                    st.error(f"❌ Failed to access repository: {repo_owner}/{repo_name}")
                    st.text(f"Status: {repo_response.status_code}")
                    st.text(repo_response.text)

# Option to recheck token
if st.session_state.token_checked:
    if st.button("Check Another Token"):
        # Reset session state
        st.session_state.token_checked = False
        st.session_state.token_valid = False
        st.session_state.user_data = None
        st.session_state.rate_data = None
        st.session_state.response_json = None
        st.experimental_rerun()

else:
    st.info("Please enter your GitHub Personal Access Token to check authorization.")