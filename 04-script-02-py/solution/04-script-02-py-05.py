#!/usr/bin/env python3
# параметры запуска: script_name "<commit_msg>" <configs_uri> [local_repo]
# требуется установленный в системе rsync, и модули GitPython и PyGithub
# некоторые предположения, для пользователя от имени которого выполняется скрипт:
# - все удалённые сервера с конфигами доступны по SSH с аутентификацией по ключу для user@
# - git config настроен правильно, имя-емейл и всё прочее
# - репозиторий в GitHub сконфигурирован как origin, он доступен без дополнительной авторизации
#   (имя добывается из remote origin / Fetch URL), можно переопределить в переменной GITHUB_REPO
# - бранч master называется по-новомодному main, можно переопределить в переменной MASTER_BRANCH
# - есть токен доступа в GitHub, он предоставляется в переменной GITHUB_TOKEN

import sys
import os
import subprocess
import time
from pathlib import Path
from git import Repo
from github import Github


def print_usage(err_msg):
    print(f"Error: {err_msg}\n",
          f"Usage: {sys.argv[0].split('/')[-1]} <commit_msg> <configs_uri> [local_repo]",
          "<commit_msg>\t- your commit message",
          "<configs_uri>\t- where configs should be taken, /local/path or user@remote.srv:/path",
          "[local_repo]\t- path to local git repo with configs, if missed - current dir",
          "GitHub token must be provided in GITHUB_TOKEN env",
          "GitHub repo can be provided in GITHUB_REPO env",
          "master branch name can be provided in MASTER_BRANCH env",
          sep="\n", file=sys.stderr
          )
    return ""


def err_exit(err_msg):
    print(f"Error: {err_msg}", file=sys.stderr)
    exit(1)


def path_normalization(rel_path):
    return os.path.abspath(rel_path.replace('~', str(Path.home())))


# configuration
gh_token = os.environ.get('GITHUB_TOKEN')
if not gh_token:
    raise SystemExit(print_usage("GitHub token must be provided in GITHUB_TOKEN environment variable"))

master_branch = os.environ.get('MASTER_BRANCH')
if not master_branch:
    master_branch = 'main'

try:
    commit_msg = sys.argv[1]
except IndexError:
    raise SystemExit(print_usage("Please provide a commit message"))

try:
    configs_uri = sys.argv[2]
except IndexError:
    raise SystemExit(print_usage("Please provide path to configs"))

try:
    git_repo = sys.argv[3]
except IndexError:
    git_repo = "."

git_repo = path_normalization(git_repo)

if not os.path.isdir(git_repo):
    err_exit(f"Directory {git_repo} doesn't exist")

if not os.path.isdir(git_repo + "/.git"):
    err_exit(f"Directory {git_repo} is not a GIT repository")

if configs_uri.endswith(':/') or configs_uri == '/':
    err_exit("<configs_uri> can't be a root directory")

# преобразуем <configs_uri> вида srv:/path/to в директорию srv/path/to
# в случае локального пути - localhost/path/to
if configs_uri.find(':') != -1:
    if configs_uri.find(':/') == -1:
        err_exit("Please use absolute path for remote <configs_uri>")
    # without user@ part
    repo_conf_path = configs_uri.split('@')[-1].replace(':', '')
else:
    repo_conf_path = 'localhost' + path_normalization(configs_uri)

repo_full_conf_path = f"{git_repo}/{repo_conf_path}"
os.makedirs(repo_full_conf_path, exist_ok=True)

# забираем изменения в конфигах с удалённого сервера с локальным репо
print(f"Get configs changes from remote server {configs_uri}...")
rsync_cmd = f"rsync -rtl --delete {configs_uri}/ {repo_full_conf_path}/"
run_res = subprocess.run(rsync_cmd.split(" "))
if run_res.returncode != 0:
    err_exit(f"Error synchronize {configs_uri} with local repo")

working_branch_name = f"{repo_conf_path.replace('/', '-')}-{int(time.time())}"
os.chdir(git_repo)

git = Repo('.').git
# синхронизируем изменения с origin
print("Update changes from origin repo...")
git.checkout(master_branch)
git.pull("origin")
# Очищаем ссылки на удалённые в origin ветки
git.remote('prune', 'origin')
# создаём новую рабочую ветку и добавляем все изменения забранные с удалённого сервера
git.checkout('-b', working_branch_name)
git.add(repo_conf_path.split('/')[0])

git_status = ''
if git.diff('--cached'):
    git_status = git.status()
    print("Changes in configs:\n", git_status)
else:
    print("No any configs changes detected, nothing to commit")
    git.checkout(master_branch)
    git.branch('-d', working_branch_name)
    exit(2)

git.commit('-m', commit_msg)

# get GitHub repo name (git remote show -n origin / Fetch URL:)
github_repo = os.environ.get("GITHUB_REPO")
if not github_repo:
    for remote_info in git.remote('show', '-n', 'origin').split("\n"):
        if remote_info.find("URL:") != -1:
            github_repo = remote_info.split(':')[-1].split('.')[0]
            break

print(f"Push changes to GitHub repo {github_repo}, branch {working_branch_name}...")
git.push('origin',  working_branch_name)

print("Create pull request...")
gh = Github(gh_token)
gh_repo = gh.get_repo(github_repo)

gh_pr = gh_repo.create_pull(title=commit_msg, body=git_status, head=working_branch_name, base=master_branch)
print(
    f"Successfully created pull request #{gh_pr.number}: \"{gh_pr.title}\"",
    f"Please review and merge: {gh_pr.html_url}", sep="\n"
)

# local cleanup
git.checkout(master_branch)
git.merge(working_branch_name)
git.branch('-d', working_branch_name)

print("All done.")
exit(0)
