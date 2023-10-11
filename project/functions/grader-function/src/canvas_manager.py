from canvasapi import Canvas


class CanvasAPIManager:
    def __init__(self, credentials, canvas_course_id):
        self.canvas = Canvas(credentials['api_url'], credentials['api_key'])
        self.canvas_course_id = canvas_course_id
        self.course = None

    def get_course(self):
        self.course = self.canvas.get_course(self.canvas_course_id)
        if self.course is None:
            print(f"Course with id {self.canvas_course_id} not found")
            return None
        return self.course

    def get_students_in_course(self):
        if self.course is None:
            self.get_course()
        students = self.course.get_users(enrollment_type=['student'])
        return students

    def get_all_assignments_in_assignment_group(self, assignment_group_name):
        print(f'Getting all assignments in assignment group {assignment_group_name}')
        if self.course is None:
            self.get_course()
        assignment_groups = self.course.get_assignment_groups()
        assignment_group = None
        for ag in assignment_groups:
            if ag.name == assignment_group_name:
                assignment_group = ag
                break
        if assignment_group is None:
            print(
                f'No assignment group found with name {assignment_group_name}')
            return []
        assignments = self.course.get_assignments_for_group(assignment_group.id)
        assignments = list(assignments)
        return assignments

    def update_grade(self, student_identifier, assignment, grade):
        # Get all students
        all_students_in_course = self.get_students_in_course()
        # Find the student for which we want to update the grade
        student_to_update = next(
            (item for item in all_students_in_course if student_identifier in item.sis_user_id), None)

        if student_to_update is None:
            print(f'Could not find student with identifier {student_identifier}')
            print("Grade not updated")
            return

        # Update the grade
        submission = assignment.get_submission(student_to_update.id)
        submission.edit(
            submission={'posted_grade': grade},
            comment={
                'text_comment': f'Graded using the automatic grader'}
        )
        print(
            f'Updated grade for student {student_to_update.name} to {grade} in assignment {assignment.name}')

    def update_multiple_grades(self, student_identifier, push_timestamp, assignments_with_grade):
        # Get all students
        all_students_in_course = self.get_students_in_course()
        # Find the student for which we want to update the grade
        student_to_update = next(
            (item for item in all_students_in_course if student_identifier in item.sis_user_id), None)

        if student_to_update is None:
            print(f'Could not find student with identifier {student_identifier}')
            return

        for assignment_with_grade in assignments_with_grade:
            # Get the grade
            grade = assignment_with_grade['grade']
            assignment = assignment_with_grade['assignment']

            # Update the grade
            submission = assignment.get_submission(student_to_update.id)
            # TODO: Attach an html file with the results of the tests
            submission.edit(
                submission={'posted_grade': grade},
                comment={
                    'text_comment': f'Graded using the automatic grader'}
            )
            print(
                f'Updated grade for student {student_to_update.name} to {grade} in assignment {assignment.name}')
