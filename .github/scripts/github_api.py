import requests
import logging
import os

# Load environment variables automatically provided by GitHub Actions
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    logging.error("GITHUB_TOKEN not found. Exiting.")
    exit(1)

# Helper function to make GitHub API requests
def github_api_request(url):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        logging.debug(f"Successful response from {url}")
        return response.json()
    else:
        logging.error(f"Failed to fetch data from {url}: {response.status_code}")
        return None

def get_branches(repo_owner, repo_name):
    """
    Fetches all branches in the repository.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches"
    return github_api_request(url)

def get_branch_commits(repo_owner, repo_name, branch_name):
    """
    Fetches commits from a specific branch.
    """
    commits_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits?sha={branch_name}&per_page=5"
    return github_api_request(commits_url)

def get_pull_request_for_branch(repo_owner, repo_name, branch_name):
    """
    Checks if a branch has an open or closed pull request.
    """
    pr_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls?state=all&head={repo_owner}:{branch_name}"
    pr_data = github_api_request(pr_url)

    # Return the first pull request if it exists (since a branch can only have one active PR)
    if pr_data and len(pr_data) > 0:
        return pr_data[0]
    return None


def get_pr_files(repo_owner, repo_name, pr_number):
    """
    Retrieves files modified in a specific pull request.
    """
    pr_files_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
    pr_files_data = github_api_request(pr_files_url)

    if pr_files_data:
        return {file_info['filename'] for file_info in pr_files_data}
    return set()

def compare_branches(repo_owner, repo_name, base_branch, target_branch):
    """
    Compares two branches and returns the list of files modified.
    """
    compare_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/compare/{base_branch}...{target_branch}"
    comparison_data = github_api_request(compare_url)

    if comparison_data:
        return {file_info['filename'] for file_info in comparison_data.get('files', [])}
    return set()
