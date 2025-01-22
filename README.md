> [!CAUTION]
> Use this script at your own risk.
> Rewriting commit history can have unintended consequences, especially for shared repositories.
> Ensure you have backups and understand the implications before proceeding.



# Git Author Rewriter

This script allows you to rewrite the commit history of your GitHub repositories to update author names and emails. It is useful for correcting mistakes or standardizing author information across multiple repositories.

## Prerequisites

- Python 3.x
- Git
- GitHub CLI (`gh`)

## Installation

1. Ensure you have Python 3.x installed on your system.
2. Install Git and GitHub CLI (`gh`).
3. Clone this repository:
    ```sh
    git clone https://github.com/yourusername/git-author-rewriter.git
    cd git-author-rewriter
    ```

## Usage

```sh
python3 git-git-author-rewriter.py
```

OR


1. Make the script executable:
    ```sh
    chmod +x git-author-rewriter.py
    ```

2. Run the script:
    ```sh
    ./git-author-rewriter.py
    ```

3. Follow the prompts to enter your GitHub credentials, select authors to update, and provide new author information.

## Example execution

```sh
$ ./git-author-rewriter.py
Please enter your GitHub credentials.
GitHub Username: yourusername
GitHub Token (Personal Access Token): ********
Cloning repositories... (1/10)
...
Unique authors:
---------------------------------
  1) John Doe
  2) Jane Smith
---------------------------------
Enter the numbers of authors to overwrite (e.g., 1,3,5): 1
New Name for 'John Doe': Jonathan Doe
New Email for 'John Doe': jonathan.doe@example.com
Rewriting history and pushing changes... (1/10)
...
All done! Your commit histories have been updated.
```
