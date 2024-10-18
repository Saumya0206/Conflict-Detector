import requests
import os
from datetime import datetime

# Load GitHub token from environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
# Extract repository owner and name
REPO_OWNER = os.getenv('GITHUB_REPOSITORY').split('/')[0]   # Get the owner of the repository
REPO_NAME = os.getenv('GITHUB_REPOSITORY').split('/')[-1]   # Get the name of the repository
BASE_BRANCH = 'master'
PR_NUMBER = os.getenv('GITHUB_REF').split('/')[-2]

print(f"GITHUB_REPOSITORY: {os.getenv('GITHUB_REPOSITORY')}")
print(f"GITHUB_REF: {os.getenv('GITHUB_REF')}")
print(f"PR_NUMBER: {PR_NUMBER}")



# Helper function to make GitHub API requests
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

# Check if a branch has an open pull request and return its details
def get_pull_request_for_branch(branch_name):
    pr_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=all&head={REPO_OWNER}:{branch_name}"
    pr_data = github_api_request(pr_url)

    if pr_data and len(pr_data) > 0:
        return pr_data[0]  # Return the first PR (since there can only be one open PR for a branch)
    return None

# Get files changed in a pull request
def get_pr_files(pr_number):
    pr_files_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/files"
    pr_files_data = github_api_request(pr_files_url)

    if pr_files_data:
        return {file_info['filename'] for file_info in pr_files_data}
    return set()


# Get files modified between base branch and working branch, considering merged PRs
def get_branch_files(branch_name):
    pr_data = get_pull_request_for_branch(branch_name)

    if pr_data:
        # If there's a pull request, fetch the files from the PR (whether merged or open)
        pr_number = pr_data['number']
        return get_pr_files(pr_number)

    else:
        # If no PR exists, we compare with the base branch
        compare_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/compare/{BASE_BRANCH}...{branch_name}"
        comparison_data = github_api_request(compare_url)

        if comparison_data:
            return {file_info['filename'] for file_info in comparison_data.get('files', [])}

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


# Get the details of the PR for the current branch
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

    # Fetch all open PRs
    pr_url_open = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=open"
    open_pr_data = github_api_request(pr_url_open)

    # Fetch merged PRs after my PR date
    merged_prs_after_date = get_merged_prs_after(my_pr_date)

    # Process both open PRs and merged PRs after the specified date
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

# Fetch pull request details using the PR number directly
def get_pull_request_by_number(pr_number):
    pr_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    pr_data = github_api_request(pr_url)

    if pr_data:
        return pr_data  # Return the PR details
    return None

def main():
    branches = get_branches()
    if not branches:
        print("No branches found.")
        return


    # Fetch pull request details by PR number
    pr_data = get_pull_request_by_number(PR_NUMBER)

    if not pr_data:
        print(f"No PR found for PR number '{PR_NUMBER}'.")
        return

    # Extract the actual head branch from the PR details
    head_branch = pr_data['head']['ref']  # This gives the branch name from which the PR was made
    print(f"Head branch for PR {PR_NUMBER}: {head_branch}")

    # Use this head branch in the comparison
    base_branch_files = get_branch_files(head_branch)

    if base_branch_files:
        print(f"Files modified in PR '{PR_NUMBER}' from branch '{head_branch}':")
        for file in base_branch_files:
            print(f"  - {file}")

        # Get the PR creation date
        my_pr_date = pr_data['created_at']
        print(f"My PR creation date: {my_pr_date}")

        # Find conflicting branches
        conflicting_branches = find_conflicting_branches(base_branch_files, branches, head_branch, my_pr_date)

        if conflicting_branches:
            print("\nOther branches working on the same files (potential conflicts):")
            for branch, files in conflicting_branches.items():
                print(f"\nBranch '{branch}' has modified the following files:")
                for file in files:
                    print(f"  - {file}")
        else:
            print("\nNo conflicting branches found.")
    else:
        print(f"No files found in PR '{PR_NUMBER}'.")

if __name__ == "__main__":
    main()