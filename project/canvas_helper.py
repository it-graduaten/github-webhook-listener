from canvasapi import Canvas
import os
import json
from datetime import datetime
import pytz

class CanvasManager:
    def __init__(self, logger):
        self.logger = logger
        self.utc = pytz.UTC
        self.config = self.get_config()
        self.canvas = self.get_canvas_obj()
        self.course = self.get_course(self.config["oop"]['canvas_course_id'])
        self.all_students_in_course = self.get_students()
        self.all_assignments_in_course = list(self.course.get_assignments())

    def get_config(self):
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config

    def get_canvas_obj(self):
        canvas = Canvas(self.config["general"]["canvas_api_url"], os.environ.get('CANVAS_API_KEY'))
        return canvas

    def get_course(self, course_id):
        course = self.canvas.get_course(course_id)
        if course is None:
            self.logger.debug(f'No course found with id {course_id}')
            return None
        return course

    def get_students(self):
        students = self.course.get_users(enrollment_type=['student'])
        return students

    def filter_exercises_on_due_date(self, assignments):
        exercises_to_grade = []
        for exercise in assignments:
            self.logger.debug(f'Found exercise {exercise.name} with due date {exercise.due_at}')
            if exercise.due_at is None:
                continue
            now = datetime.utcnow().replace(tzinfo=self.utc)
            due_at = datetime.strptime(exercise.due_at, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=self.utc)
            if now < due_at:
                exercises_to_grade.append(exercise)

        self.logger.debug(f'Found {len(exercises_to_grade)} exercises to grade')
        return exercises_to_grade

    def get_all_exercises_in_assignment_group(self, assignment_group_name):
        self.logger.debug(f'Getting all exercises in assignment group {assignment_group_name}')
        assignment_groups = self.course.get_assignment_groups()
        assignment_group = None
        for ag in assignment_groups:
            if ag.name == assignment_group_name:
                assignment_group = ag
                break
        if assignment_group is None:
            self.logger.debug(f'No assignment group found with name {assignment_group_name}')
            return []
        assignments = self.course.get_assignments_for_group(assignment_group.id)
        assignments = list(assignments)
        self.logger.debug(f'Found {len(assignments)} assignments in assignment group {assignment_group_name}')
        return assignments

    def upload_results(self, student_identifier, results):
        self.logger.debug(f'Uploading results for {student_identifier}')
        # Find the student to update, based on the student identifier
        student_to_update = next((item for item in self.all_students_in_course if student_identifier in item.sis_user_id), None)

        # If no student is found, log this and return
        if student_to_update is None:
            self.logger.debug(f'No student found with identifier {student_identifier}')
            return

        for exercise in results:
            exercise_name = exercise["assignment"].replace("_", ".")
            grade = exercise["grade"]
            run_at_utc_datetime = exercise["run_at_utc_datetime"]

            if self.all_assignments_in_course == 0:
                self.logger.debug(f'No exercise found for {exercise_name}')
                continue

            # Find the assignment to update
            assignments_with_name = [item for item in self.all_assignments_in_course if exercise_name in item.name]

            if len(assignments_with_name) > 1:
                self.logger.debug(f'Multiple assignments found for {exercise_name}')
                continue

            course_assignment = assignments_with_name[0]
            submission = course_assignment.get_submission(student_to_update.id)
            submission.edit(
                submission={'posted_grade': grade},
                comment={'text_comment': f'Last graded at {datetime.fromisoformat(run_at_utc_datetime).strftime("%Y-%m-%d %H:%M:%S")} with a score of {grade}'}
            )
            self.logger.debug(f'Updated grade for {exercise_name} to {grade}')

    def manipulate_exercises(self, assignments):
        exercises = []
        for assignment in assignments:
            name = assignment.name
            due_at = None if (assignment.due_at is None) else datetime.strptime(assignment.due_at, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=self.utc)
            assignment_id = assignment.id
            exercise = {
                'name': name.replace('.', '_').replace("*", ""),
                'due_at': due_at,
                'id': assignment_id
            }
            self.logger.debug(f'Found exercise {name} with due date {due_at}')
            exercises.append(exercise)
        return exercises