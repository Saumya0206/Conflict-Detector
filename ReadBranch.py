import requests

GITHUB_TOKEN = 'GITHUB_TOKEN'
REPO_OWNER = 'Saumya0206'
REPO_NAME = 'VideoCall-and-Chat'
USERNAME = 'Saumya0206'
BASE_BRANCH = 'master'


def getConflictingBranches():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch branches: {response.status_code}")
        return None

def get_branches():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        branches = response.json()
        for branch in branches:
            print(branch['name'])
        latest_branch = None
        latest_commit_time = None

        for branch in branches:
            branch_name = branch['name']
            commits_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits?sha={branch_name}&per_page=5"
            commit_response = requests.get(commits_url, headers=headers)

            if commit_response.status_code == 200:
                commits = commit_response.json()
                for commit_info in commits:
                    # Print the full commit info for debugging
                    # print(f"Commit Info: {commit_info}")

                    # Check if 'author' is not None
                    if commit_info['author'] is not None:
                        commit_author_login = commit_info['author']['login']  # GitHub username of the commit author
                        commit_date = commit_info['commit']['committer']['date']  # Get commit time

                        # Check if the commit author login matches your GitHub username
                        if commit_author_login == USERNAME:
                            # Update if this commit is the latest
                            if latest_commit_time is None or commit_date > latest_commit_time:
                                latest_commit_time = commit_date
                                latest_branch = branch_name
                    else:
                        print(f"Skipped commit {commit_info['sha']} due to missing author information.")
            else:
                print(f"Failed to fetch commits for branch {branch_name}: {commit_response.status_code}")

        return latest_branch, latest_commit_time
    else:
        print(f"Failed to fetch branches: {response.status_code}")
        return None, None

def get_branch_files(branch_name):
    # Use the compare API to find the difference between the base branch and the working branch
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/compare/{BASE_BRANCH}...{branch_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        comparison_data = response.json()
        files_changed = set()  # Use a set to avoid duplicates

        # Loop through the 'files' list to get the filenames
        for file_info in comparison_data.get('files', []):
            files_changed.add(file_info['filename'])

        return files_changed
    else:
        print(f"Failed to fetch comparison for branch {branch_name}: {response.status_code}")
        return None

def find_conflicting_branches(base_branch_files, latest_branch):
    branches = getConflictingBranches()
    conflicting_branches = {}

    if branches:
        for branch in branches:
            branch_name = branch['name']
            print("branch_name: ",branch_name)
            if branch_name != latest_branch:  # Skip the current branch itself
                branch_files = get_branch_files(branch_name)
                print("branch_files: ", branch_files)
                if branch_files:
                    # Find common files between base_branch_files and this branch's files
                    common_files = base_branch_files.intersection(branch_files)
                    print("common_files: ",common_files)
                    if common_files:
                        conflicting_branches[branch_name] = common_files
    return conflicting_branches

if __name__ == "__main__":
    latest_branch, commit_time = get_branches()
    if latest_branch:
        print(f"The branch you are working on is: {latest_branch} (Last commit time: {commit_time})")
        base_branch_files = get_branch_files(latest_branch)
        if base_branch_files:
            print(f"Files modified in branch '{latest_branch}':")
            for file in base_branch_files:
                print(f"  - {file}")

            # Find which other branches are modifying the same files
            conflicting_branches = find_conflicting_branches(base_branch_files, latest_branch)

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
    else:
        print("No branches found with your commits.")
