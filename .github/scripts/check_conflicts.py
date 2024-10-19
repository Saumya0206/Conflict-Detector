import requests
import os
from datetime import datetime

# Load environment variables automatically provided by GitHub Actions
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER, REPO_NAME = os.getenv('GITHUB_REPOSITORY').split("/")
USERNAME = os.getenv('GITHUB_ACTOR')
BASE_BRANCH = 'master'


def github_api_request(url):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data from {url}: {response.status_code}")
        return None


# Get list of branches in the repository
def get_branches():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches"
    return github_api_request(url)

# Get the commits for a specific branch
def get_branch_commits(branch_name):
    commits_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits?sha={branch_name}&per_page=5"
    return github_api_request(commits_url)

# Check if a branch has an open pull request
def get_pull_request_for_branch(branch_name):
    pr_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=all&head={REPO_OWNER}:{branch_name}"
    pr_data = github_api_request(pr_url)

    if pr_data and len(pr_data) > 0:
        return pr_data[0]
    return None

# Get files changed in a pull request
def get_pr_files(pr_number):
    pr_files_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/files"
    pr_files_data = github_api_request(pr_files_url)

    if pr_files_data:
        return {file_info['filename'] for file_info in pr_files_data}
    return set()


# Find the latest branch with commits by the user
def find_latest_branch(branches):
    latest_branch = None
    latest_commit_time = None

    for branch in branches:
        branch_name = branch['name']
        commits = get_branch_commits(branch_name)

        if commits:
            for commit_info in commits:
                commit_author = commit_info['author']
                if commit_author and commit_author['login'] == USERNAME:
                    commit_date = commit_info['commit']['committer']['date']
                    if not latest_commit_time or commit_date > latest_commit_time:
                        latest_commit_time = commit_date
                        latest_branch = branch_name

    return latest_branch, latest_commit_time


def get_my_pr_creation_date(branch_name):
    pr_data = get_pull_request_for_branch(branch_name)

    if pr_data:
        created_at = pr_data['created_at']
        return created_at
    return None

# Get all pull requests (open and closed) and return those merged after a specific date
def get_merged_prs_after(date_str):
    pr_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=closed"
    pr_data = github_api_request(pr_url)

    merged_prs = []
    if pr_data:
        for pr in pr_data:
            if pr['merged_at'] and pr['merged_at'] > date_str:
                merged_prs.append(pr)
    return merged_prs

# Find conflicting branches considering only open PRs and merged PRs after the specific date
def find_conflicting_branches(base_branch_files, branches, latest_branch, my_pr_date):
    conflicting_branches = {}

    pr_url_open = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=open"
    open_pr_data = github_api_request(pr_url_open)

    merged_prs_after_date = get_merged_prs_after(my_pr_date)

    pr_data_to_check = open_pr_data + merged_prs_after_date

    for pr in pr_data_to_check:
        branch_name = pr['head']['ref']
        if branch_name == latest_branch:
            continue

        branch_files = get_pr_files(pr['number'])

        if branch_files:
            common_files = base_branch_files.intersection(branch_files)
            if common_files:
                conflicting_branches[branch_name] = common_files

    return conflicting_branches

# Main function to handle branch and conflict analysis
def main():
    branches = get_branches()
    if not branches:
        print("No branches found.")
        return

    latest_branch, commit_time = find_latest_branch(branches)

    if not latest_branch:
        print("No branches found with your commits.")
        return

    print(f"The branch you are working on is: {latest_branch} (Last commit time: {commit_time})")
    base_branch_files = get_branch_files(latest_branch)

    if base_branch_files:
        print(f"Files modified in branch '{latest_branch}':")
        for file in base_branch_files:
            print(f"  - {file}")

        my_pr_date = get_my_pr_creation_date(latest_branch)

        if not my_pr_date:
            print(f"No PR found for branch '{latest_branch}'.")
            return

        print(f"My PR creation date: {my_pr_date}")

        conflicting_branches = find_conflicting_branches(base_branch_files, branches, latest_branch, my_pr_date)

        if conflicting_branches:
            print("\nOther branches working on the same files (potential conflicts):")
            for branch, files in conflicting_branches.items():
                print(f"\nBranch '{branch}' has modified the following files:")
                for file in files:
                    print(f"  - {file}")
        else:
            print("\nNo conflicting branches found.")
    else:
        print(f"No files found in branch '{latest_branch}'.")


if __name__ == "__main__":
    main()