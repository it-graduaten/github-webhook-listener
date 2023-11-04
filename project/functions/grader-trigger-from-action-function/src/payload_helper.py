def get_changed_files(commits):
    files = list()

    for commit in commits:
        files.extend(commit["added"])
        files.extend(commit["modified"])
        files.extend(commit["removed"])

    return files
