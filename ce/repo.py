from ce.utils import __, local


def clone(repo_url, local_path):
    '''
    Git clone a repo to a local path.
    :param repo_url: str
    :param local_path: str
    :return: None
    '''
    __('git clone {url} {local}'.format(
        url=repo_url,
        local=local_path, ))


def get_commit(repo_path, short=False):
    '''
    Get the commitid of a local repo.
    :param repo_path: str
    :return: str
    '''
    with local.cwd(repo_path):
        commit = __('git log -1 --pretty=format:%h').strip() if short else __(
            'git log -1 --pretty=format:%H').strip()
        return commit
