# Branch Conflict Checker

This repository extends any project by introducing a **Branch Conflict Checker**. This tool is implemented as a GitHub Action that automatically checks for potential conflicts between branches whenever a pull request (PR) is created or updated. It helps identify potential file conflicts with open or recently merged pull requests that modify the same files, allowing teams to catch conflicts early in the development process.

## Problem Statement

In collaborative development, multiple developers often work on different branches of the same codebase. When two or more pull requests modify the same files, conflicts can arise during the merging process. Detecting these conflicts early can save time and prevent integration issues.

The Branch Conflict Checker automates this conflict detection by comparing the files in a pull request against other branches with open or recently merged pull requests. It then reports any potential conflicts, enabling developers to resolve them before merging.

## How Does It Work?

The **Branch Conflict Checker** runs whenever a pull request is created or updated. The workflow is triggered by GitHub Actions and automatically compares the branch associated with the pull request to other branches. Specifically, it:

1. **Identifies Modified Files**: It checks the files modified in the current branch (from the pull request).
2. **Fetches Open and Recently Merged PRs**: It then retrieves all open pull requests and any pull requests merged after the creation of the current PR.
3. **Compares Files**: The script compares the modified files in the current branch with those in other open or recently merged pull requests.
4. **Logs Potential Conflicts**: If any common files are detected, the conflicting branches are logged along with the status of their pull requests (open or merged).

The results are output in the GitHub Actions log, informing the developer whether any potential conflicts need to be addressed.

## Project Structure

The repository is structured as follows:

```plaintext
your-repository/
│
├── .github/
│   └── workflows/
│          └── conflict-check.yml   # The GitHub Action Workflow definition                     
├── scripts/
│       └── main.py                 # The Python script for checking branch conflicts
├── src/
│   └── ...                         # Your existing codebase (The code you will be working on)
│
└── README.md                       # Project's README file
