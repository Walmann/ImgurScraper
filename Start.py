import os
import sys
import git
from github import Github
from configparser import ConfigParser

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

# Check if there are changes in the settings.ini file
config = ConfigParser()
config.read("settings.ini")
local_settings_sha = git.Repo(search_parent_directories=True).git.hash_object("settings.ini")

# If the latest commit SHA or the settings.ini SHA is different from the current commit SHA
if latest_commit_sha != current_commit_sha or local_settings_sha != config.get("general", "sha"):
    print("Updating repository and settings.ini...")

    # Pull the latest changes from the repository
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    repo = git.Repo(repo_dir)
    origin = repo.remote(name="origin")
    origin.pull()

    # Merge changes in the settings.ini file
    config.read("settings.ini")
    config.set("general", "sha", local_settings_sha)
    with open("settings.ini", "w") as configfile:
        config.write(configfile)

    # Restart the script
    os.execv(sys.executable, [sys.executable] + sys.argv)
else:
    print("Repository and settings.ini are up-to-date.")
