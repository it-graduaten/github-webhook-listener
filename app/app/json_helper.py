def get_changed_and_added_files(commits):
    files = []
    for commit in commits:
        for file in commit['added']:
            # If file is not already in the list, add it
            if file not in files:
                files.append(file)
        for file in commit['modified']:
            # If file is not already in the list, add it
            if file not in files:
                files.append(file)
    # Return both arrays merged as one
    return files

def get_repo_url(json_data):
    # Return the repository URL
    return json_data['repository']['html_url']

def get_parent_dirs(files):
    """ This methodes gets the parent directories of the files """
    # Create an empty array
    parent_dirs = []
    # For each file, get the parent directory and add it to the array
    for file in files:
        parent_dir = file.rsplit('/', 2)[0]
        if parent_dir not in parent_dirs:            
            parent_dirs.append(parent_dir)
    # Return the array
    return parent_dirs