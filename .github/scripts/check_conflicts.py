import requests
import os
import logging

# Configure logging settings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Load environment variables automatically provided by GitHub Actions
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER, REPO_NAME = os.getenv('GITHUB_REPOSITORY').split("/")
USERNAME = os.getenv('GITHUB_ACTOR')
BASE_BRANCH = 'master'

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

    # Return the first pull request if it exists (since a branch can only have one active PR)
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

# Main function to handle branch and conflict analysis
def main():
    branches = get_branches()
    if not branches:
        logging.warning("No branches found.")
        return

    latest_branch, commit_time = find_latest_branch(branches)

    if not latest_branch:
        logging.warning("No branches found with your commits.")
        return

    logging.info(f"The branch you are working on is: {latest_branch} (Last commit time: {commit_time})")
    base_branch_files = get_branch_files(latest_branch)

    if base_branch_files:
        logging.info(f"Files modified in branch '{latest_branch}':")
        for file in base_branch_files:
            logging.info(f"  - {file}")

        # Get the PR creation date for the current branch
        my_pr_date = get_my_pr_creation_date(latest_branch)

        if not my_pr_date:
            logging.warning(f"No PR found for branch '{latest_branch}'.")
            return

        logging.info(f"My PR creation date: {my_pr_date}")

        # Find conflicting branches with only open PRs and merged PRs after my PR creation date
        conflicting_branches = find_conflicting_branches(base_branch_files, branches, latest_branch, my_pr_date)

        if conflicting_branches:
            logging.info("\nOther branches working on the same files (potential conflicts):")
            for branch, files in conflicting_branches.items():
                logging.info(f"\nBranch '{branch}' has modified the following files:")
                for file in files:
                    logging.info(f"  - {file}")
        else:
            logging.info("\nNo conflicting branches found.")
    else:
        logging.warning(f"No files found in branch '{latest_branch}'.")


if __name__ == "__main__":
    main()