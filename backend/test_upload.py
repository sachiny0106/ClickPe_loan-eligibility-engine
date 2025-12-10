import requests
import sys

API_ENDPOINT = 'https://eowoa91n5f.execute-api.us-east-1.amazonaws.com/dev/upload-url'
FILE_PATH = '../user.csv'

def upload_file():
    try:
        # 1. Get Presigned URL
        print(f"Requesting upload URL from {API_ENDPOINT}...")
        response = requests.get(f"{API_ENDPOINT}?filename=user.csv")
        response.raise_for_status()
        data = response.json()
        upload_url = data['uploadUrl']
        print("Got upload URL.")

        # 2. Upload File
        print(f"Uploading {FILE_PATH}...")
        with open(FILE_PATH, 'rb') as f:
            # Important: The Content-Type header must match what might have been signed (if any)
            # In our Lambda, we didn't restrict Content-Type, but requests might add one.
            # We'll try sending it as binary data.
            upload_response = requests.put(upload_url, data=f)
        
        if upload_response.status_code == 200:
            print("Upload successful!")
        else:
            print(f"Upload failed: {upload_response.status_code}")
            print(upload_response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    upload_file()
