import shutil
import os
import debug_helper

def delete_all_content(dir):
    """ Deletes all the content of a directory """
    # Check if the directory exists
    if os.path.exists(dir):
        # Get the contents of the directory
        contents = os.listdir(dir)
        # For each file in the directory, delete it
        for content in contents:
                # Check if the file is a directory
                if os.path.isdir(dir + "/" + content):
                    try:
                        # If so, delete the directory
                        shutil.rmtree(dir)
                    except:
                        debug_helper.print_error("Error while deleting " + content)

def make_dir(dir):
    """ Creates a directory if it does not exist """
    if not os.path.exists(dir):
        os.makedirs(dir)