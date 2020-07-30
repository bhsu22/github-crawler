"""
Crawl and download repositories from github using the
GitHub api to search for relevant repositories.
"""
import argparse
import urllib
import logging
import json
import os
import math
import sys

from tqdm import tqdm
import wget


DEFAULT_TASK = "text-classification"
DEFAULT_URL = "https://api.github.com/search/repositories?q="  # The basic URL to use the GitHub API
DEFAULT_PER_PAGE = 100


logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    stream=sys.stdout,
    level=logging.INFO,
)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--task",
        type=str,
        default=DEFAULT_TASK,
        help="Task or use case to search for across git repos, e.g. text-classification. Dash separated terms.",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_URL,
        help="Base url to the repositories, e.g. https://api.github.com/search/repositories?q=",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="python",
        help="Programming language to search for.",
    )
    parser.add_argument(
        "--folder",
        type=str,
        default="./",
        help="Directory to save downloaded repositories to.",
    )
    parser.add_argument(
        "--per_page",
        type=int,
        default=DEFAULT_PER_PAGE,
        help="Number of repositiories to return per page of query results.",
    )
    parser.add_argument(
        "--branch", type=str, default="master", help="The branch of code to download."
    )

    return parser.parse_args()


def download_repo(repo_url, download_filename, branch="master"):
    """Download the repository contents from the branch."""
    repo_master = repo_url[:-4] + f"/archive/{branch}.zip"

    try:
        wget.download(repo_master, out=download_filename)
    except:
        logger.error(f"Could not get: {repo_url}")


if __name__ == "__main__":
    args = parse_args()
    task = args.task
    url = args.url
    lang = args.language
    output_dir = args.folder
    per_page = args.per_page
    branch = args.branch

    QUERY = f"{task.replace('-','+')}+language:{lang.lower()}+created%3A>%3D2019-06-01"
    URL = f"https://api.github.com/search/repositories?q={QUERY}"
    PER_PAGE = f"&per_page={per_page}"

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    output_json = os.path.join(output_dir, "repositories.json")

    repositories = []
    seen_repos = set()

    with urllib.request.urlopen(URL) as response:
        rep = response.read().decode("utf8")
        rep = json.loads(rep)

        total_count = rep["total_count"]
        n_pages = int(math.ceil(total_count / 100))

        for i in range(n_pages):
            url = URL + PER_PAGE + f"&page={i}"
            with urllib.request.urlopen(url) as response:
                rep = response.read().decode("utf8")
                rep = json.loads(rep)

                for repo in tqdm(rep["items"], desc=f"page {i+1}/{n_pages}"):
                    user = repo["owner"]["login"]
                    repository = repo["name"]

                    if (user, repository) in seen_repos:
                        continue

                    seen_repos.add((user, repository))
                    repositories.append(
                        {"user": user, "repository": repository, "keyword": task}
                    )

                    download_filename = repo["full_name"].replace("/", "#") + ".zip"
                    output_filename = os.path.join(output_dir, download_filename)
                    download_repo(repo["clone_url"], output_filename, branch)

    json.dump(repositories, open(output_json, "w"))
