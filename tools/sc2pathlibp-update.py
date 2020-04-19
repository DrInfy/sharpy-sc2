"""
Script to update sc2-pathlib in sc2pathlibp folder.
"""

import os
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlretrieve
from urllib.parse import urlparse

import requests
import json

# Set working dir to root of repository.
script_path = Path(os.path.abspath(__file__))
assert script_path.parent.stem == "tools", "`This script expects to be in tools folder under repository root.`"
os.chdir(script_path.parent.parent)

latest_release_url = "https://api.github.com/repos/DrInfy/sc2-pathlib/releases/latest"
sc2pathlibp = "sc2pathlibp"
sc2pathlibp_old = "sc2pathlibp_old"

print(f"Finding download url from ... {latest_release_url}")

response = requests.get(latest_release_url)
content = json.loads(response.content)
download_url = content["assets"][0]["browser_download_url"]

path = urlparse(download_url).path
filename = os.path.basename(path)
version = path.rsplit("/")[-2]

print(f"Downloading zip from ... {download_url}")
print(f"Saving to file ... {filename}")
print(f"Detected version: {version}")

urlretrieve(download_url, filename)

print(f"Renaming folder {sc2pathlibp} ... {sc2pathlibp_old}")
os.rename(sc2pathlibp, sc2pathlibp_old)

print(f"Extracting file ... {filename}")
with zipfile.ZipFile(filename, "r") as zip_ref:
    zip_ref.extractall()

print(f"Removing folder {sc2pathlibp_old}")
shutil.rmtree(sc2pathlibp_old)

print(f"Removing file {filename}")
os.remove(filename)
