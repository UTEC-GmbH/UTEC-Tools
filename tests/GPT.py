import os
import datetime as dt
from typing import Dict, Any
import pytz
from github import Github

# Cache commit message and date
commit_data = {}

def get_commit_message_date() -> Dict[str, Any]:
    """Commit message and date from GitHub to show in the header."""
    global commit_data

    if "sha" in commit_data:
        # Return cached data if commit SHA is the same
        return commit_data

    # Get personal access token from environment variable
    personal_access_token = os.environ.get("GITHUB_PAT")
    if not personal_access_token:
        error_msg = "GITHUB_PAT environment variable not set."
        return {"com_date": "ERROR", "com_msg": error_msg}

    # Get commit data from GitHub API
    gith = Github(personal_access_token)
    repo = gith.get_user().get_repo("repo_name")
    branch = getattr(repo, "main", None)
    if not branch:
        error_msg = "Failed to get 'main' branch for repository."
        return {"com_date": "ERROR", "com_msg": error_msg}

    sha = branch.commit.sha
    commit = repo.get_commit(sha).commit
    commit_data = {
        "com_date": get_commit_date(commit),
        "com_msg": get_commit_message(commit),
        "sha": sha,
    }
    return commit_data

def get_commit_date(commit) -> dt.datetime:
    """Get commit date in Europe/Berlin timezone."""
    utc = pytz.utc
    eur = pytz.timezone("Europe/Berlin")
    date_now = dt.datetime.now()
    tz_diff = (utc.localize(date_now) - eur.localize(date_now)).total_seconds() / 3600
    return commit.author.date + dt.timedelta(hours=tz_diff)

def get_commit_message(commit) -> str:
    """Get last line of commit message."""
    return commit.message.split("\n")[-1]
