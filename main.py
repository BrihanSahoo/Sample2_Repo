import streamlit as st
import requests
import urllib.parse
import base64


CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URL = st.secrets["REDIRECT_URL"]

def git_login():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URL,
        "scope": "repo"
    }
    url = "https://github.com/login/oauth/authorize?" + urllib.parse.urlencode(params)
    st.markdown(f"[Login with GitHub]({url})")

def access_token(code):
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code
    }
    res = requests.post(url, headers=headers, data=data)
    return res.json().get("access_token")

def create_repo(token, repo_name):
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": repo_name, "private": False}
    return requests.post(url, headers=headers, json=data).json()

def create_or_update_file(token, owner, repo, path, content, message):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    if isinstance(content, str):
        content_bytes = content.encode()
    else:
        content_bytes = content
    encoded_content = base64.b64encode(content_bytes).decode()
    data = {"message": message, "content": encoded_content}
    if sha:
        data["sha"] = sha
    return requests.put(url, headers=headers, json=data).json()

st.title("GitHub Automation App")

query_params = st.query_params
code = query_params.get("code")

if "token" not in st.session_state and not code:
    git_login()
    st.stop()

if "token" not in st.session_state and code:
    token = access_token(code)
    if not token:
        st.error("OAuth failed")
        st.stop()
    st.session_state["token"] = token
    st.query_params.clear()

token = st.session_state["token"]

st.success("Authenticated with GitHub")

repo_name = st.text_input("Repository Name")

if st.button("Create Repository"):
    st.write(create_repo(token, repo_name))

owner = st.text_input("Owner")

st.subheader("Option 1: Write File Content")

file_path = st.text_input("File Path", "hello.txt")
content = st.text_area("File Content")

if st.button("Push Text File"):
    st.write(create_or_update_file(
        token, owner, repo_name, file_path, content, "text commit"
    ))

st.subheader("Option 2: Upload File")

uploaded_file = st.file_uploader("Upload file")

upload_path = st.text_input("Upload Path",uploaded_file.name)

if st.button("Upload File"):
    if uploaded_file:
        st.write(create_or_update_file(
            token,
            owner,
            repo_name,
            upload_path,
            uploaded_file.read(),
            "file upload"
        ))
    else:
        st.warning("Upload a file first")