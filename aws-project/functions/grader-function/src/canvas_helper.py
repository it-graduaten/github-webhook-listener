from canvasapi import Canvas
import os
import json
from datetime import datetime
import pytz


def create_canvas_object():
    canvas = Canvas(os.environ.get('CANVAS_API_URL'), os.environ.get('CANVAS_API_KEY'))
    return canvas


def get_course(canvas_obj, course_id):
    course = canvas_obj.get_course(course_id)
    if course is None:
        print(f"Course with id {course_id} not found")
        return None
    return course


def get_all_students_in_course(course_obj):
    students = course_obj.get_users(enrollment_type=['student'])
    return students


def get_all_exercises_in_assignment_group(course_obj, assignment_group_name):
    assignment_groups = course_obj.get_assignment_groups()
    assignment_group = None
    for ag in assignment_groups:
        if ag.name == assignment_group_name:
            assignment_group = ag
            break
    if assignment_group is None:
        print(f'No assignment group found with name {assignment_group_name}')
        return []
    assignments = course_obj.get_assignments_for_group(assignment_group.id)
    assignments = list(assignments)
    return assignments


def upload_grades(canvas_course_id, student_identifier, push_timestamp, assignments_with_grade):
    # Create a canvas object
    canvas = create_canvas_object()
    # Get the course
    course = get_course(canvas, canvas_course_id)
    # Get all students
    all_students_in_course = get_all_students_in_course(course)
    # Find the student
    student_to_update = next(
        (item for item in all_students_in_course if student_identifier in item.sis_user_id), None)

    if student_to_update is None:
        print(f'Could not find student with identifier {student_identifier}')
        return

    # Get all assignments in the assignment group
    # TODO: Change this to the correct assignment group name using config
    all_assignments_in_assignment_group = get_all_exercises_in_assignment_group(course, 'Permanente evaluatie')

    for assignment_with_grade in assignments_with_grade:
        # Replace underscores with dots, so it matches the name on Canvas
        assignment_name = assignment_with_grade['assignment'].replace('_', '.')
        # Get the grade
        grade = assignment_with_grade['grade']        
        # Find the assignment that matches the name, so we can update it
        assignments_where_name = [item for item in all_assignments_in_assignment_group if assignment_name in item.name]

        if len(assignments_where_name) == 0:
            print(f'Could not find assignment with name {assignment_name}')
            return

        if len(assignments_where_name) > 1:
            print(f'Found multiple assignments with name {assignment_name}')
            return

        assignment_to_update = assignments_where_name[0]

        # If the due date of the assignment is before the push_timestamp, don't update the grade
        if assignment_to_update.due_at is not None:
            if assignment_to_update.due_at < push_timestamp:
                print(f'Assignment {assignment_to_update.name} was due before the push timestamp, not updating grade')
                return

        # Update the grade
        submission = assignment_to_update.get_submission(student_to_update.id)
        # TODO: Add a link to an html page where the user can see the test results
        submission.edit(
            submission={'posted_grade': grade},
            comment={
                'text_comment': f'Graded using the automatic grader'}
        )
        print(f'Updated grade for student {student_to_update.name} to {grade} in assignment {assignment_to_update.name}')
