import os
import stat
import shutil
import json
import csv

class FileOperations:
    logger = None

    def __init__(self, logger):
        self.logger = logger
        pass

    def rmtree(self, top):
        # Check if the path exists
        if not os.path.exists(top):
            return

        self.logger.debug(f'Removing {top}..')
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                filename = os.path.join(root, name)
                os.chmod(filename, stat.S_IWUSR)
                os.remove(filename)
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(top)
        self.logger.debug(f'Removed {top}')

    def save_results_to_file(self, new_results, filename='results.json'):
        self.logger.debug(f'Saving results to file..')
        directory = './results'
        path = f"{directory}/{filename}"
        
        existing_results = []

        # Sort the results by the 'assignment' key
        new_results = sorted(new_results, key=lambda k: k['assignment'])

        # Check if the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        # If no file with the given name exists, create it, and write the results
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump(new_results, f)
            f.close()
            return new_results

        # If the file already exists, read the existing results in memory
        with open(path, 'r') as f:
            existing_results = json.load(f)
        f.close()

        # Merge the existing results with the new results
        for new_result in new_results:
            # Check if the assignment already exists in the existing results
            existing_result = next((item for item in existing_results if item["assignment"] == new_result["assignment"]), None)
            if existing_result is None:
                existing_results.append(new_result)
            else:
                # If the assignment already exists, update the existing result
                existing_result["total"] = new_result["total"]
                existing_result["errors"] = new_result["errors"]
                existing_result["run_at_utc_datetime"] = new_result["run_at_utc_datetime"]
                if existing_result["grade"] != new_result["grade"]:
                    existing_result["should_update_canvas"] = True
                    existing_result["grade"] = new_result["grade"]
                else:
                    existing_result["should_update_canvas"] = False
                    
        # Write the merged results to the file
        with open(path, 'w') as f:
            json.dump(existing_results, f)
        f.close()

        return existing_results

    def copy_dir(self, source, destination, delete_existing=False):
        self.logger.debug(f'Copying {source} to {destination}..')
        if delete_existing:
            self.rmtree(destination)
        shutil.copytree(source, destination)
        self.logger.debug(f'Copied {source} to {destination}')

    def get_classroom_roster(self):
        roster = []
        self.logger.debug(f'Getting classroom roster..')
        filename = './classroom_roster.csv'
        if not os.path.exists(filename):
            self.logger.debug(f'Classroom roster not found')
            return None
        with open('./classroom_roster.csv', 'r') as f:
            csvreader = csv.reader(f)
            for idx, row in enumerate(iterable=csvreader):
                # Skip the header
                if idx == 0:
                    continue
                roster.append({
                    'identifier': row[0],
                    'github_username': row[1],
                    'github_id': row[2],
                    'name': row[3],
                })
        self.logger.debug(f'Got classroom roster')
        return roster

    def get_all_folders_in_dir(self, dir):
        folders = []
        for item in os.listdir(dir):
            if os.path.isdir(os.path.join(dir, item)):
                folders.append(item)
        return folders

    def mkdir(self, path):
        self.logger.debug(f'Creating directory {path}..')
        os.mkdir(path)
        self.logger.debug(f'Created directory {path}')
