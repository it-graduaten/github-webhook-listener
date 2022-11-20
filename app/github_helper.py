from github import Github
import json
import os

# using an access token
print("Logging in to Github")
print(os.getenv("GITHUB_ACCESS_TOKEN"))

g = Github(os.getenv("GITHUB_ACCESS_TOKEN"))
repo = g.get_repo('it-graduaten/Objectgeorienteerd-Programmeren')

def get_assignment_name_from_config(config_dir):
    # Get contents of the config file
    content = repo.get_contents(config_dir + "/config.json")
    # Decode the contents
    my_json = content.decoded_content.decode('utf8').replace("'", '"')
    # Load the JSON
    data = json.loads(my_json)
    # Return the assignment name
    return data['codegradeAssignmentName']

def get_evaluation_files(path_to_config):
    # Remove the 'config.json' from the path
    path_to_evaluation = path_to_config.replace('/config.json', '/evaluation')
    # Check if the path excists
    if repo.get_contents(path_to_evaluation):
        # Get the contents of the evaluation directory
        contents = repo.get_contents(path_to_evaluation)
        # Create an empty array
        files = []
        # For each file in the directory, add it to the array
        for content in contents:
            files.append(content.path)
        # Return the array
        return files

def get_file_contents(path):
    # Get the contents of the file
    content = repo.get_contents(path)
    # Decode the contents
    return content.decoded_content.decode('utf8')

def is_assignment_dir(dir):
    try:
        # Check if the directory contains a 'config.json' file
        if repo.get_contents(dir + '/config.json'):
            return True
        else:
            return False
    except Exception as e:
        return False;

def get_dir_contents(dir):
    """ This methodes gets the contents of a directory """
    # Get the contents of the directory
    contents = repo.get_contents(dir)
    # Create an empty array
    files = []
    # For each file in the directory, add it to the array
    for content in contents:
        files.append(content.path)
    # Return the array
    return files

def download_dir(dir, output_dir):
    """ Download all the files in a directory recursively """
    # Get the contents of the directory
    contents = repo.get_contents(dir)
    # For each file in the directory, download it
    for content in contents:
        # Check if the file is a directory
        if content.type == "dir":
            # If so, download the directory
            download_dir(content.path, output_dir)
        else:
            # If not, download the file
            download_file(content.path, output_dir)

def download_file(file, output_dir):
    """ Download a file from Github """
    # Get the contents of the file
    file_content = repo.get_contents(file)
    # Create the output directory
    os.makedirs(os.path.dirname(output_dir + "/" + file), exist_ok=True)
    # Write the contents to a file
    with open(output_dir + "/" + file, "wb") as f:
        f.write(file_content.decoded_content)
