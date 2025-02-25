import requests
import streamlit as st
import os
from dotenv import load_dotenv

# Load token from .env file if available
load_dotenv()

st.title("GitHub Token Authorization Checker")

# Get token from environment variable or input
github_token = os.getenv('GITHUB_TOKEN')
if not github_token:
    github_token = st.text_input("Enter your GitHub Personal Access Token:", type="password")

if github_token:
    # Button to test the token
    if st.button("Test Token Authorization"):
        with st.spinner("Checking token..."):
            # Make a request to GitHub API
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Try to get user information (requires authentication)
            response = requests.get("https://api.github.com/user", headers=headers)
            
            # Display detailed response
            st.subheader("Authorization Test Results:")
            
            # Create columns for better display
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Status Code:", response.status_code)
                if response.status_code == 200:
                    st.success("✅ Token is valid and working!")
                    
                    # Get and display rate limit info
                    rate_response = requests.get("https://api.github.com/rate_limit", headers=headers)
                    if rate_response.status_code == 200:
                        rate_data = rate_response.json()
                        st.write("API Rate Limit:", rate_data['resources']['core']['limit'])
                        st.write("Remaining Calls:", rate_data['resources']['core']['remaining'])
                else:
                    st.error("❌ Token authorization failed!")
            
            with col2:
                # Show user information
                if response.status_code == 200:
                    user_data = response.json()
                    st.write("Authenticated as:", user_data['login'])
                    st.write("User ID:", user_data['id'])
                    if 'name' in user_data and user_data['name']:
                        st.write("Name:", user_data['name'])
                
            # Show full response for debugging
            with st.expander("View Full API Response"):
                if response.status_code == 200:
                    st.json(response.json())
                else:
                    st.text(response.text)
                    
            # Test specific repository access if token is valid
            if response.status_code == 200:
                st.subheader("Test Repository Access:")
                repo_owner = st.text_input("Repository Owner:", value=os.getenv('REPO_OWNER', ''))
                repo_name = st.text_input("Repository Name:", value=os.getenv('REPO_NAME', ''))
                
                if repo_owner and repo_name and st.button("Test Repository Access"):
                    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
                    repo_response = requests.get(repo_url, headers=headers)
                    
                    if repo_response.status_code == 200:
                        st.success(f"✅ Successfully accessed repository: {repo_owner}/{repo_name}")
                        
                        # Test file access if a file path is provided
                        file_path = st.text_input("Test File Path (optional):", value=os.getenv('FILE_PATH', ''))
                        if file_path and st.button("Test File Access"):
                            file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
                            file_response = requests.get(file_url, headers=headers)
                            
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
else:
    st.info("Please enter your GitHub Personal Access Token to check authorization.")