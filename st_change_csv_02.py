import requests
import streamlit as st
import pandas as pd
import base64
import io
import os
from dotenv import load_dotenv

# Load environment variables
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
if 'csv_data' not in st.session_state:
    st.session_state.csv_data = None
if 'file_sha' not in st.session_state:
    st.session_state.file_sha = None

st.title("GitHub CSV Editor")

# Get token from environment variable or input
github_token = os.getenv('GITHUB_TOKEN')
if not github_token:
    github_token = st.text_input("Enter your GitHub Personal Access Token:", type="password")

# Helper function to create headers
def get_headers():
    return {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

# Check token function
def check_token():
    response = requests.get("https://api.github.com/user", headers=get_headers())
    
    st.session_state.token_checked = True
    st.session_state.token_valid = (response.status_code == 200)
    
    if response.status_code == 200:
        st.session_state.user_data = response.json()
        
        # Get rate limit info
        rate_response = requests.get("https://api.github.com/rate_limit", headers=get_headers())
        if rate_response.status_code == 200:
            st.session_state.rate_data = rate_response.json()
    else:
        st.session_state.user_error = response.text

# Check repository function
def check_repository(repo_owner, repo_name):
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    response = requests.get(repo_url, headers=get_headers())
    
    st.session_state.repo_checked = True
    st.session_state.repo_valid = (response.status_code == 200)
    
    if response.status_code == 200:
        st.session_state.repo_data = response.json()
    else:
        st.session_state.repo_error = response.text

# Check file function and load CSV
def check_file(repo_owner, repo_name, file_path):
    file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    response = requests.get(file_url, headers=get_headers())
    
    st.session_state.file_checked = True
    st.session_state.file_valid = (response.status_code == 200)
    
    if response.status_code == 200:
        file_data = response.json()
        st.session_state.file_data = file_data
        st.session_state.file_sha = file_data['sha']
        
        # Decode content and load as CSV if it's a csv file
        if file_path.endswith('.csv'):
            try:
                content = base64.b64decode(file_data['content']).decode('utf-8')
                df = pd.read_csv(io.StringIO(content))
                st.session_state.csv_data = df
            except Exception as e:
                st.session_state.file_error = f"Error parsing CSV: {str(e)}"
    else:
        st.session_state.file_error = response.text

# Function to save edited CSV back to GitHub
def save_csv_to_github(repo_owner, repo_name, file_path, df):
    if not st.session_state.file_sha:
        return False, "File SHA is missing. Cannot update file."
    
    file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    
    try:
        # Convert DataFrame to CSV string
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Encode content to base64
        encoded_content = base64.b64encode(csv_content.encode()).decode()
        
        # Prepare update data
        update_data = {
            "message": "Update CSV via Streamlit app",
            "content": encoded_content,
            "sha": st.session_state.file_sha
        }
        
        # Update the file
        response = requests.put(file_url, headers=get_headers(), json=update_data)
        
        if response.status_code == 200 or response.status_code == 201:
            # Update the SHA for future updates
            st.session_state.file_sha = response.json()['content']['sha']
            return True, "File updated successfully!"
        else:
            return False, f"Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

# Reset function
def reset_all():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.experimental_rerun()

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
            if hasattr(st.session_state, 'user_data'):
                user_data = st.session_state.user_data
                st.write(f"Authenticated as: {user_data['login']}")
        else:
            st.error("❌ Token authorization failed!")
            if hasattr(st.session_state, 'user_error'):
                st.text(st.session_state.user_error)
    
    # Repository test section
    if st.session_state.token_valid:
        st.subheader("Step 2: Test Repository Access")
        
        col1, col2 = st.columns(2)
        with col1:
            repo_owner = st.text_input("Repository Owner:", value=os.getenv('REPO_OWNER', ''))
        with col2:
            repo_name = st.text_input("Repository Name:", value=os.getenv('REPO_NAME', ''))
        
        if repo_owner and repo_name and not st.session_state.repo_checked:
            if st.button("Test Repository Access"):
                with st.spinner("Checking repository access..."):
                    check_repository(repo_owner, repo_name)
        
        if st.session_state.repo_checked:
            if st.session_state.repo_valid:
                st.success(f"✅ Successfully accessed repository: {repo_owner}/{repo_name}")
            else:
                st.error(f"❌ Failed to access repository: {repo_owner}/{repo_name}")
                if hasattr(st.session_state, 'repo_error'):
                    st.text(st.session_state.repo_error)
        
        # File test section
        if st.session_state.repo_valid:
            st.subheader("Step 3: Select CSV File")
            
            file_path = st.text_input("CSV File Path:", value=os.getenv('FILE_PATH', ''))
            
            if file_path and not st.session_state.file_checked:
                if st.button("Load CSV File"):
                    with st.spinner("Loading CSV file..."):
                        check_file(repo_owner, repo_name, file_path)
            
            if st.session_state.file_checked:
                if st.session_state.file_valid:
                    if file_path.endswith('.csv') and st.session_state.csv_data is not None:
                        st.success(f"✅ Successfully loaded CSV file: {file_path}")
                        
                        # CSV Editor Section
                        st.subheader("Step 4: Edit CSV Data")
                        
                        # Show original data
                        with st.expander("View Original Data", expanded=False):
                            st.dataframe(st.session_state.csv_data)
                        
                        # Edit data
                        st.write("Make your changes below:")
                        edited_df = st.data_editor(
                            st.session_state.csv_data,
                            num_rows="dynamic",
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Save changes
                        if st.button("Save Changes to GitHub"):
                            with st.spinner("Saving changes..."):
                                success, message = save_csv_to_github(
                                    repo_owner, repo_name, file_path, edited_df
                                )
                                if success:
                                    st.session_state.csv_data = edited_df  # Update the local data
                                    st.success(message)
                                else:
                                    st.error(message)
                    else:
                        st.error("The selected file is not a valid CSV or could not be parsed.")
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