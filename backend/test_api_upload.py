import os
import requests

API_URL = "http://localhost:8000/api/v1"

# To test upload, we need a valid JWT token. 
# So first we create a user, login, and then upload.

def test_flow():
    # 1. Register User
    print("Registering user...")
    res = requests.post(f"{API_URL}/auth/register", json={
        "email": "testupload@example.com",
        "password": "password123",
        "full_name": "Test Upload User"
    })
    if res.status_code not in (200, 201, 400):
        print("Registration failed:", res.json())
        return
    elif res.status_code == 400:
        print("User might already exist, proceeding to login...")
    
    # 2. Login
    print("Logging in...")
    res = requests.post(f"{API_URL}/auth/login", data={
        "username": "testupload@example.com",
        "password": "password123"
    })
    
    if res.status_code != 200:
        print("Login failed:", res.json())
        return
        
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create a dummy file
    with open("dummy.txt", "w") as f:
        f.write("This is a dummy test file for RAG platform.")
        
    # 4. Upload file
    print("Uploading file...")
    with open("dummy.txt", "rb") as f:
        files = {"file": ("dummy.txt", f, "text/plain")}
        upload_res = requests.post(f"{API_URL}/documents/", headers=headers, files=files)
        
    print("Upload Status:", upload_res.status_code)
    print("Upload Response:", upload_res.json())
        
    # 4. Upload fake PDF (should fail content validation)
    print("Uploading fake PDF...")
    with open("fake.pdf", "w") as f:
        f.write("This is a text file disguised as a PDF.")
        
    with open("fake.pdf", "rb") as f:
        files = {"file": ("fake.pdf", f, "application/pdf")}
        upload_res = requests.post(f"{API_URL}/documents/", headers=headers, files=files)
        
    print("Fake PDF Upload Status:", upload_res.status_code)
    print("Fake PDF Upload Response:", upload_res.json())
    
    os.remove("fake.pdf")
    os.remove("dummy.txt")

if __name__ == "__main__":
    test_flow()
