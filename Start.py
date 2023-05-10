import os
# import sys
import git
from github import Github

# Define the repository information
REPO_OWNER = "Walmann"
REPO_NAME = "ImgurScraper"

# Create a PyGithub instance
g = Github()

# Get the repository object
repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")

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

# Run the ImgurDownloader script
print("Staring ImgurDownloader.py")
os.system("python3 ImgurDownloader.py")