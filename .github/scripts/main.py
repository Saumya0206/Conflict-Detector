import logging
import os

from github_api import get_branches, get_branch_commits
from branch_analysis import get_branch_files, find_latest_branch, find_conflicting_branches
from utils import get_my_pr_creation_date, get_merged_prs_after

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

REPO_OWNER, REPO_NAME = os.getenv('GITHUB_REPOSITORY').split("/")
USERNAME = os.getenv('GITHUB_ACTOR')
BASE_BRANCH = 'master'

def main():
    # Fetch branches
    branches = get_branches(REPO_OWNER, REPO_NAME)
    if not branches:
        logging.warning("No branches found.")
        return

    # Find the latest branch with your commits
    latest_branch, commit_time = find_latest_branch(branches, lambda branch: get_branch_commits(REPO_OWNER, REPO_NAME, branch), USERNAME)
    if not latest_branch:
        logging.warning("No branches found with your commits.")
        return

    logging.info(f"The branch you are working on is: {latest_branch} (Last commit time: {commit_time})")

    # Get modified files for the latest branch
    base_branch_files = get_branch_files(REPO_OWNER, REPO_NAME, BASE_BRANCH, latest_branch)
    if not base_branch_files:
        logging.warning(f"No files found in branch '{latest_branch}'.")
        return

    logging.info(f"Files modified in branch '{latest_branch}':")
    for file in base_branch_files:
        logging.info(f"  - {file}")

    # Get PR creation date for the current branch
    my_pr_date = get_my_pr_creation_date(REPO_OWNER, REPO_NAME, latest_branch)
    if not my_pr_date:
        logging.warning(f"No PR found for branch '{latest_branch}'.")
        return

    logging.info(f"My PR creation date: {my_pr_date}")

    # Fetch open PRs and recently merged PRs
    merged_prs_after_date = get_merged_prs_after(REPO_OWNER, REPO_NAME, my_pr_date)

    # Analyze conflicting branches
    conflicting_branches = find_conflicting_branches(REPO_OWNER, REPO_NAME, base_branch_files, latest_branch, merged_prs_after_date)
    if conflicting_branches:
        logging.info("\nOther branches working on the same files (potential conflicts):")
        for branch, details in conflicting_branches.items():
            logging.info(f"\nBranch '{branch}' ({details['state']}) has modified the following files:")
            for file in details["files"]:
                logging.info(f"  - {file}")
    else:
        logging.info("\nNo conflicting branches found.")

if __name__ == "__main__":
    main()
