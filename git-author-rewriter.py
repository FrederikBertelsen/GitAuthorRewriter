#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import getpass


def check_dependencies():
    required_cmds = ["gh", "git"]
    for cmd in required_cmds:
        if shutil.which(cmd) is None:
            print(f"Error: '{cmd}' not found. Please install it.")
            sys.exit(1)


def prompt_credentials():
    print("Please enter your GitHub credentials.")
    username = input("GitHub Username: ")
    token = getpass.getpass("GitHub Token (Personal Access Token): ")
    return username, token


def fetch_repositories(username):
    cmd = [
        "gh",
        "repo",
        "list",
        username,
        "--limit",
        "1000",
        "--json",
        "name",
        "-q",
        ".[].name",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: Unable to fetch repositories.\n{result.stderr}")
        sys.exit(1)

    repos = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    return repos


def clone_repositories(username, token, repos):
    total_repos = len(repos)
    for i, repo in enumerate(repos, start=1):
        print(f"Cloning repositories... ({i}/{total_repos})", end="\r")
        if os.path.isdir(repo):
            continue
        clone_url = f"https://{username}:{token}@github.com/{username}/{repo}.git"
        result = subprocess.run(["git", "clone", "-q", clone_url, repo])
        if result.returncode != 0:
            continue
    print("")


def collect_unique_authors(repos):
    authors_set = set()
    for repo in repos:
        git_dir = os.path.join(repo, ".git")
        if os.path.isdir(git_dir):
            result = subprocess.run(
                ["git", "log", "--format=%aN"], capture_output=True, text=True, cwd=repo
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if line:
                        authors_set.add(line)
    authors_list = sorted(authors_set)
    return authors_list


def select_authors(authors):
    if not authors:
        sys.exit(0)

    print("Unique authors:")
    print("---------------------------------")
    for i, author in enumerate(authors, start=1):
        print(f"{i:3d}) {author}")
    print("---------------------------------")

    choices = input("Enter the numbers of authors to overwrite (e.g., 1,3,5): ")
    choices = choices.replace(" ", "")
    indices = [x for x in choices.split(",") if x]

    old_authors = []
    new_names = []
    new_emails = []

    for index_str in indices:
        try:
            idx = int(index_str)
            if 1 <= idx <= len(authors):
                old_author = authors[idx - 1]
                new_name = input(f"New Name for '{old_author}': ")
                new_email = input(f"New Email for '{old_author}': ")
                old_authors.append(old_author)
                new_names.append(new_name)
                new_emails.append(new_email)
        except ValueError:
            continue

    if not old_authors:
        sys.exit(0)

    return old_authors, new_names, new_emails


def rewrite_history_and_push(username, repos, old_authors, new_names, new_emails):
    total_repos = len(repos)
    for i, repo in enumerate(repos, start=1):
        git_dir = os.path.join(repo, ".git")
        if not os.path.isdir(git_dir):
            continue

        try:
            os.chdir(repo)
        except Exception:
            continue

        before_file = "../before_refs.txt"
        with open(before_file, "w", encoding="utf-8") as f:
            subprocess.run(["git", "rev-list", "--all"], stdout=f, check=True)

        env_filter_script = ""
        for old, new_n, new_e in zip(old_authors, new_names, new_emails):
            old_esc = old.replace('"', '\\"')
            new_n_esc = new_n.replace('"', '\\"')
            new_e_esc = new_e.replace('"', '\\"')
            env_filter_script += f"""
if [ "$GIT_AUTHOR_NAME" = "{old_esc}" ]; then
    GIT_AUTHOR_NAME="{new_n_esc}"
    GIT_AUTHOR_EMAIL="{new_e_esc}"
fi
if [ "$GIT_COMMITTER_NAME" = "{old_esc}" ]; then
    GIT_COMMITTER_NAME="{new_n_esc}"
    GIT_COMMITTER_EMAIL="{new_e_esc}"
fi
"""

        try:
            env = os.environ.copy()
            env["FILTER_BRANCH_SQUELCH_WARNING"] = "1"

            subprocess.run(
                [
                    "git",
                    "filter-branch",
                    "--force",
                    "--env-filter",
                    env_filter_script,
                    "--",
                    "--all",
                ],
                check=True,
                shell=False,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                [
                    "git",
                    "filter-branch",
                    "--force",
                    "--tag-name-filter",
                    "cat",
                    "--",
                    "--all",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            os.chdir("..")
            continue

        after_file = "../after_refs.txt"
        with open(after_file, "w", encoding="utf-8") as f:
            subprocess.run(["git", "rev-list", "--all"], stdout=f, check=True)

        with (
            open(before_file, "r", encoding="utf-8") as bf,
            open(after_file, "r", encoding="utf-8") as af,
        ):
            before_data = bf.read()
            after_data = af.read()

        if before_data != after_data:
            subprocess.run(
                ["git", "remote", "remove", "origin"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            new_origin = f"git@github.com:{username}/{repo}.git"
            subprocess.run(
                ["git", "remote", "add", "origin", new_origin],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            try:
                subprocess.run(
                    ["git", "push", "origin", "--force", "--all"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                subprocess.run(
                    ["git", "push", "origin", "--force", "--tags"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError as e:
                print(f"Error: Failed to push changes for repo '{repo}'.\n{e}")
                os.chdir("..")
                continue

        try:
            os.remove(before_file)
            os.remove(after_file)
        except Exception:
            pass

        os.chdir("..")
        print(f"Rewriting history and pushing changes... ({i}/{total_repos})", end="\r")
    print("")


def cleanup(repos):
    for repo in repos:
        if os.path.isdir(repo) and os.path.isdir(os.path.join(repo, ".git")):
            shutil.rmtree(repo)

    for filename in ["repos.txt", "authors.txt"]:
        if os.path.isfile(filename):
            os.remove(filename)


def main():
    check_dependencies()

    username, token = prompt_credentials()
    repos = fetch_repositories(username)
    clone_repositories(username, token, repos)

    authors = collect_unique_authors(repos)
    old_authors, new_names, new_emails = select_authors(authors)

    rewrite_history_and_push(username, repos, old_authors, new_names, new_emails)
    cleanup(repos)

    print("\nAll done! Your commit histories have been updated.")


if __name__ == "__main__":
    main()
