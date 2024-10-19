from github_api import get_pull_request_for_branch, github_api_request

def get_my_pr_creation_date(repo_owner, repo_name, branch_name):
    """
    Fetches the creation date of the pull request for the current branch.
    """
    pr_data = get_pull_request_for_branch(branch_name)

    if pr_data:
        created_at = pr_data['created_at']
        return created_at
    return None

def get_merged_prs_after(repo_owner, repo_name, date_str):
    """
    Fetches all merged pull requests that were merged after the specified date.
    """
    pr_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls?state=closed"
    pr_data = github_api_request(pr_url)

    merged_prs = []
    if pr_data:
        for pr in pr_data:
            if pr['merged_at'] and pr['merged_at'] > date_str:
                merged_prs.append(pr)
    return merged_prs
