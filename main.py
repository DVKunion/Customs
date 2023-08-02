import os.path
import sys

from github.github import GithubCode

if __name__ == '__main__':
    args = sys.argv[1:]
    token = args[0].split(",")
    date = ""
    token_select = 0
    if len(args) < 1:
        print("empty arg")
        sys.exit(1)

    if len(args) == 2:
        date = args[1]

    if len(args) == 3:
        date = args[1]
        token_select = args[2]

    if len(token) == 0:
        print("empty token")
        sys.exit(1)

    if int(token_select) > len(token) - 1:
        print("token select error")
        sys.exit(1)
    t = token[int(token_select)]
    print("select token ", t)
    # temp check date for some error:
    date_slice = date.split("-")
    if os.path.exists(f"dataset/{date_slice[0]}/{date_slice[1]}/github-{date}.json"):
        # means already get it
        print("already scan it, try next")
        sys.exit(0)
    github = GithubCode(t, date)
    github.fetch_code_detail()
    github.save_result()
