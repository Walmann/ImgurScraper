import os
import sys
import git
from github import Github

# Define the repository information
REPO_OWNER = "Walmann"
REPO_NAME = "ImgurScraper"
IGNORE_FILES = ["settings.ini"]  # files to ignore when updating

# Create a PyGithub instance
g = Github()

# Get the repository object
try:
    repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
except Exception as e:
    print(f"Error getting repository: {e}")
    sys.exit()

# Get the latest commit SHA
latest_commit_sha = repo.get_commits()[0].sha

# Get the current commit SHA
current_commit_sha = git.Repo(search_parent_directories=True).head.object.hexsha

# If the latest commit SHA is different from the current commit SHA
if latest_commit_sha != current_commit_sha:
    print("Updating repository...")

    # Pull the latest changes from the repository
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    repo = git.Repo(repo_dir)
    origin = repo.remote(name="origin")
    origin.pull()

    # Ignore specified files
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file in IGNORE_FILES:
                os.chdir(root)
                repo.git.checkout("HEAD", "--", file)

    # Restart the script
    os.execv(sys.executable, [sys.executable, "ImgurDownloader.py"])
else:
    print("Repository is up-to-date. ")
    os.system("python3 ImgurDownloader.py")