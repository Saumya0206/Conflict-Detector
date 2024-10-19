import logging
import os

from github_api import get_branches
from branch_analysis import get_branch_files, find_latest_branch, find_conflicting_branches
from utils import get_my_pr_creation_date

# Configure logging settings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



# Main function to handle branch and conflict analysis
def main():
    repo_owner, repo_name, = os.getenv('GITHUB_REPOSITORY').split("/")
    username = os.getenv('GITHUB_ACTOR')
    base_branch = 'master'


    branches = get_branches(repo_owner, repo_name,)
    if not branches:
        logging.warning("No branches found.")
        return


    latest_branch, commit_time = find_latest_branch(repo_owner, repo_name, branches, username)

    if not latest_branch:
        logging.warning("No branches found with your commits.")
        return

    logging.info(f"The branch you are working on is: {latest_branch} (Last commit time: {commit_time})")
    base_branch_files = get_branch_files(repo_owner, repo_name, base_branch, latest_branch)

    if base_branch_files:
        logging.info(f"Files modified in branch '{latest_branch}':")
        for file in base_branch_files:
            logging.info(f"  - {file}")

        # Get the PR creation date for the current branch
        my_pr_date = get_my_pr_creation_date(repo_owner, repo_name, latest_branch)

        if not my_pr_date:
            logging.warning(f"No PR found for branch '{latest_branch}'.")
            return

        logging.info(f"My PR creation date: {my_pr_date}")

        # Find conflicting branches with only open PRs and merged PRs after my PR creation date
        conflicting_branches = find_conflicting_branches(repo_owner, repo_name, base_branch_files, latest_branch, my_pr_date)


        if conflicting_branches:
            logging.info("\nOther branches working on the same files (potential conflicts):")
            for branch, details in conflicting_branches.items():
                logging.info(f"\nBranch '{branch}' ({details['state']}) has modified the following files:")
                for file in details["files"]:
                    logging.info(f"  - {file}")
        else:
            logging.info("\nNo conflicting branches found.")

    else:
        logging.warning(f"No files found in branch '{latest_branch}'.")


if __name__ == "__main__":
    main()