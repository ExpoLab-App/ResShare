import os
import requests
from io import BytesIO

ipfs_cluster_api_url = None
ipfs_gateway_url = None


def read_config_file():
    global ipfs_cluster_api_url, ipfs_gateway_url
    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, 'config/ipfs.config')
    with open(config_path) as f:
        ipfs_cluster_api_url = f.readline().strip()
        ipfs_gateway_url = f.readline().strip()


def add_file_to_cluster(file_obj, filename):
    """
    Adds a file to the IPFS Cluster using an in-memory file-like object.

    :param file_obj: File-like object (e.g., BytesIO, or from Flask's request.files).
    :param filename: Name of the file to be uploaded.
    :return: CID if successful, else None
    """
    if ipfs_cluster_api_url is None or ipfs_gateway_url is None:
        read_config_file()

    url = ipfs_cluster_api_url + "add"
    files = {'file': (filename, file_obj)}
    response = requests.post(url, files=files)

    if response.status_code == 200:
        cid = response.json()['cid']
        return cid['/'] if isinstance(cid, dict) else cid
    else:
        return None


def get_file_status(cid):
    if ipfs_cluster_api_url is None or ipfs_gateway_url is None:
        read_config_file()

    url = f"{ipfs_cluster_api_url}pins/{cid}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to get file status from IPFS Cluster.")
        print(response.text)
        return None


def download_file_from_ipfs(cid):
    """
    Downloads a file from IPFS and returns a BytesIO object.

    :param cid: The CID of the file
    :return: dict with success flag and BytesIO stream or error message
    """
    if ipfs_cluster_api_url is None or ipfs_gateway_url is None:
        read_config_file()

    url = f"{ipfs_gateway_url}ipfs/{cid}"
    print(f"Download URL: {url}")

    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            buffer = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                buffer.write(chunk)
            buffer.seek(0)
            return {"success": True, "file": buffer}
        else:
            error = f"Download failed: {response.status_code}, {response.text}"
            return {"success": False, "message": error}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": str(e)}