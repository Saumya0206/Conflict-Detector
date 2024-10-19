from github_api import get_pull_request_for_branch, get_pr_files, compare_branches


def get_branch_files(repo_owner, repo_name, base_branch, branch_name):
    """
    Get files modified in a specific branch, either via pull request or by comparing with the base branch.
    """
    pr_data = get_pull_request_for_branch(repo_owner, repo_name, branch_name)

    if pr_data:
        pr_number = pr_data['number']
        return get_pr_files(repo_owner, repo_name, pr_number)
    else:
        return compare_branches(repo_owner, repo_name, base_branch, branch_name)

def find_latest_branch(branches, commits_fn, username):
    """
    Finds the latest branch with commits by the given user.
    """
    latest_branch = None
    latest_commit_time = None

    for branch in branches:
        branch_name = branch['name']
        commits = commits_fn(branch_name)

        if commits:
            for commit_info in commits:
                commit_author = commit_info['author']
                if commit_author and commit_author['login'] == username:
                    commit_date = commit_info['commit']['committer']['date']
                    if not latest_commit_time or commit_date > latest_commit_time:
                        latest_commit_time = commit_date
                        latest_branch = branch_name

    return latest_branch, latest_commit_time

def find_conflicting_branches(repo_owner, repo_name, base_branch_files, latest_branch, pr_data_to_check):
    """
    Find conflicting branches by checking for common files modified in both open and recently merged pull requests.
    """
    conflicting_branches = {}

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
