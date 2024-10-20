from github_api import get_pull_request_for_branch, get_pr_files, compare_branches, get_branch_commits, github_api_request
from utils import get_merged_prs_after

def get_branch_files(repo_owner, repo_name, base_branch, branch_name):
    """
    Get files modified in a branch. If a pull request exists, get files from the PR;
    otherwise, compare the branch with the base branch.
    """
    pr_data = get_pull_request_for_branch(repo_owner, repo_name, branch_name)

    if pr_data:
        # If there's a pull request, fetch the files from the PR (whether merged or open)
        pr_number = pr_data['number']
        return get_pr_files(repo_owner, repo_name, pr_number)
    else:
        return compare_branches(repo_owner, repo_name, base_branch, branch_name)

def find_latest_branch(repo_owner, repo_name, branches, username):
    """
    Find the most recent branch with commits by the given user.
    Iterates over the branches and checks the commits to find the latest.
    """
    latest_branch = None
    latest_commit_time = None

    for branch in branches:
        branch_name = branch['name']
        commits = get_branch_commits(repo_owner, repo_name, branch_name)

        if commits:
            for commit_info in commits:
                commit_author = commit_info['author']

                if commit_author and commit_author['login'] == username:
                    commit_date = commit_info['commit']['committer']['date']

                    if not latest_commit_time or commit_date > latest_commit_time:
                        latest_commit_time = commit_date
                        latest_branch = branch_name

    return latest_branch, latest_commit_time

def find_conflicting_branches(repo_owner, repo_name, base_branch_files, latest_branch, my_pr_date):
    """
    Find branches that may have conflicts with the current branch.
    Checks open PRs and recently merged PRs after a given date for common modified files.
    """
    conflicting_branches = {}

    pr_url_open = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls?state=open"
    open_pr_data = github_api_request(pr_url_open)
    merged_prs_after_date = get_merged_prs_after(repo_owner, repo_name, my_pr_date)

    pr_data_to_check = open_pr_data + merged_prs_after_date

    for pr in pr_data_to_check:
        branch_name = pr['head']['ref']
        if branch_name == latest_branch:
            continue

        branch_files = get_pr_files(repo_owner, repo_name, pr['number'])

        if branch_files:
            common_files = base_branch_files.intersection(branch_files)

            if common_files:
                pr_state = "open" if pr['state'] == "open" else f"merged at {pr['merged_at']}"
                conflicting_branches[branch_name] = {"files": common_files, "state": pr_state}

    return conflicting_branches
