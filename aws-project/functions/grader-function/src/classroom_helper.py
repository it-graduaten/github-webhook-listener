import pandas as pd
import os


def get_student_identifier(github_classroom_id, student_github_id):
    """
    Get the student identifier from the classroom roster csv file
    :param github_classroom_id: The Github classroom ID
    :param student_github_id: The Github ID of the student
    :return: The student identifier
    """
    # TODO: Read this CSV from s3-mock storage
    # Read all students from the classroom roster csv file
    roster = pd.read_csv(
        os.path.join("s3-mock", "classroom-rosters", f"classroom_roster_{github_classroom_id}.csv"))
    # Get the student identifier
    roster_identifier = roster[roster['github_id'] == student_github_id]['identifier'].values
    # If no student identifier is found, return None
    if len(roster_identifier) == 0:
        print(f"No student identifier found for student with Github ID: {student_github_id}")
        return None
    # If more than one student identifier is found, return None
    if len(roster_identifier) > 1:
        print(f"More than one student identifier found: {roster_identifier}")
        return None
    # Return the student identifier
    start_index = roster_identifier[0].find("(")
    end_index = roster_identifier[0].find(")")
    student_identifier = roster_identifier[0][start_index + 1:end_index]
    print(f"Student identifier found: {student_identifier}")
    return student_identifier
