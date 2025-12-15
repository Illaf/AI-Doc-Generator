import subprocess

from git import Optional

def list_remote_branches(repo_url: str, token: Optional[str] = None) -> list[str]:
    if token and repo_url.startswith("https://"):
        repo_url = repo_url.replace("https://", f"https://{token}@")

    result = subprocess.run(
        ["git", "ls-remote", "--heads", repo_url],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(result.stderr.strip())

    branches = []
    for line in result.stdout.splitlines():
        # refs/heads/branch-name
        ref = line.split("\t")[1]
        branches.append(ref.replace("refs/heads/", ""))

    return branches



def branch_exists(repo_url: str, branch: str, token: Optional[str] = None) -> bool:
    if token and repo_url.startswith("https://"):
        repo_url = repo_url.replace("https://", f"https://{token}@")

    result = subprocess.run(
        ["git", "ls-remote", "--heads", repo_url, branch],
        capture_output=True,
        text=True
    )

    return bool(result.stdout.strip())

