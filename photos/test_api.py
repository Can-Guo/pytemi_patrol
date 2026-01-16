import requests

#API_URL = "http://172.25.20.165:6001/analyze" # https://645t2cmhz085.share.zrok.io/
API_URL = "https://645t2cmhz085.share.zrok.io/analyze"

def test_api(image_path: str, prompt: str):
    with open(image_path, "rb") as img_file:
        files = {"uploaded_file": img_file}
        data = {"prompt": prompt}
        response = requests.post(API_URL, files=files, data=data)

    if response.status_code == 200:
        print("Response JSON:")
        print(response.json())
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    # Example usage
    test_api("./pytemi/photos/a2_20260107_151657.png", "Please describe the image.")
