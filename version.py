"""
Writes latest git commit hash and date to version.txt file.
"""

import subprocess


def update_version_txt():
    try:
        commit_hash = subprocess.check_output("git rev-parse --short HEAD", stderr=subprocess.STDOUT).decode().strip()
        commit_date = subprocess.check_output("git log -1 --date=short --pretty=format:%cd", stderr=subprocess.STDOUT).decode().strip()

        with open("version.txt", mode="w") as file:
            file.write(commit_date + '\n')
            file.write(commit_hash)
            print(f"Updated version.txt with: {commit_date} {commit_hash}")
    except Exception:
        print(f"unable to update version.txt. Using previous values instead (if found).")


if __name__ == '__main__':
    update_version_txt()
