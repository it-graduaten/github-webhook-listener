import chevron
from typing import Optional, List
import json


# Custom xml result models to create a json or dict from the dotnet result xml
class DotnetOutput:
    message: str
    stacktrace: str
    stdout: str

    def __init__(self, message: str, stacktrace: str, stdout: str) -> None:
        self.message = message
        self.stacktrace = stacktrace
        self.stdout = stdout


class DotnetTest:
    name: str
    outcome: str
    duration: int
    output: Optional[DotnetOutput]
    has_error: bool

    def __init__(self, name: str, outcome: str, duration: int, output: Optional[DotnetOutput]) -> None:
        self.name = name
        self.outcome = 'failed' if outcome == 'Failed' else 'success'
        self.duration = duration
        self.output = output
        self.has_error = outcome == "Failed"


class DotnetTestClass:
    test_class_id: str
    name: str
    total_runtime_in_ms: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    tests: List[DotnetTest]

    def __init__(self, test_class_id: str, name: str, total_runtime_in_ms: int, total_tests: int, passed_tests: int,
                 failed_tests: int, tests: List[DotnetTest]) -> None:
        self.test_class_id = test_class_id
        self.name = name
        self.total_runtime_in_ms = total_runtime_in_ms
        self.total_tests = total_tests
        self.passed_tests = passed_tests
        self.failed_tests = failed_tests
        self.tests = tests


class DotnetCategory:
    category_id: str
    name: str
    classes: List[DotnetTestClass]
    total_tests: int
    passed_tests: int
    failed_tests: int

    def __init__(self, category_id: str, name: str, classes: List[DotnetTestClass]) -> None:
        self.category_id = category_id
        self.name = name
        self.classes = classes
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0


class DotnetData:
    title: str
    total_runtime_in_ms: int
    total_tests: int
    failed_tests: int
    passed_tests: int
    categories: List[DotnetCategory]
    grade: float
    log_filename: str
    has_compile_error: bool
    output_log: str

    def __init__(self, title: str, log_filename, output_log) -> None:
        self.title = title
        self.total_runtime_in_ms = 0
        self.total_tests = 0
        self.failed_tests = 0
        self.passed_tests = 0
        self.categories = []
        self.grade = 0
        self.log_filename = log_filename
        self.has_compile_error = False
        self.output_log = output_log

    def update_totals(self):
        total_runtime_in_ms = 0
        for cat in self.categories:
            for cl in cat.classes:
                cl.total_tests = len(cl.tests)
                cl.failed_tests = len([test for test in cl.tests if test.outcome.lower() == "failed"])
                cl.passed_tests = len([test for test in cl.tests if
                                       test.outcome.lower() == "Passed" or test.outcome.lower() == "success"])
                cl.total_runtime_in_ms = sum([test.duration for test in cl.tests])
                total_runtime_in_ms += cl.total_runtime_in_ms
            cat.total_tests = sum([test_class.total_tests for test_class in cat.classes])
            cat.failed_tests = sum([test_class.failed_tests for test_class in cat.classes])
            cat.passed_tests = sum([test_class.passed_tests for test_class in cat.classes])
        self.total_runtime_in_ms = total_runtime_in_ms
        self.total_tests = sum([category.total_tests for category in self.categories])
        self.failed_tests = sum([category.failed_tests for category in self.categories])
        self.passed_tests = sum([category.passed_tests for category in self.categories])

    def update_grade(self):
        if self.total_tests == 0:
            self.grade = 0
        else:
            self.grade = round(10 - (self.failed_tests * (10 / self.total_tests)), 1)

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def to_dict(self):
        data = {
            "title": self.title,
            "total_runtime_in_ms": self.total_runtime_in_ms,
            "total_tests": self.total_tests,
            "failed_tests": self.failed_tests,
            "passed_tests": self.passed_tests,
            "categories": [],
            "grade": self.grade,
            "log_filename": self.log_filename,
            "has_compile_error": self.has_compile_error,
            "output_log": self.output_log
        }

        for category in self.categories:
            category_data = {
                "name": category.name,
                "classes": [],
                "id": category.category_id,
                "total_tests": category.total_tests,
                "failed_tests": category.failed_tests,
                "passed_tests": category.passed_tests
            }
            for test_class in category.classes:
                class_data = {
                    "name": test_class.name,
                    "total_runtime_in_ms": test_class.total_runtime_in_ms,
                    "total_tests": test_class.total_tests,
                    "passed_tests": test_class.passed_tests,
                    "failed_tests": test_class.failed_tests,
                    "tests": [],
                    "id": test_class.test_class_id
                }
                for test in test_class.tests:
                    test_data = {
                        "name": test.name,
                        "outcome": test.outcome,
                        "duration": test.duration,
                        "output": {
                            "message": test.output.message if test.output else None,
                            "stacktrace": test.output.stacktrace if test.output else None,
                            "stdout": test.output.stdout if test.output else None
                        },
                        "has_error": test.has_error,
                    }
                    class_data["tests"].append(test_data)
                category_data["classes"].append(class_data)
            data["categories"].append(category_data)

        return data


# End of custom xml result models

def create_html_report(path_to_template, output_path, data):
    # Read the template
    with open(path_to_template, 'r') as f:
        result = chevron.render(f, data)
    f.close()

    # Write the result
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    f.close()

    return output_path


def transform_to_mustache_dotnet_data(unittest_xml_data):
    data = DotnetData(title="TODO", log_filename="TODO", output_log="TODO")
    for result in unittest_xml_data.results:
        # Get the class name for this result
        test_definition = next((test_definition for test_definition in unittest_xml_data.test_definitions if
                                test_definition.test_definition_id == result.test_result_id), None)
        # Get the test category name
        category_name = test_definition.test_category.test_category_item.name
        # Get the test definition name
        test_definition_name = test_definition.name
        # Get the class name
        class_name = test_definition.class_name
        print("Test definition info: " + category_name + " - " + class_name + " - " + test_definition_name)
        # Check if a category with the name already exists
        if category_name not in [category.name for category in data.categories]:
            # If not, create a new category and append it to the data
            category_to_use = DotnetCategory(
                category_id=category_name,
                name=category_name,
                classes=[]
            )
            data.categories.append(category_to_use)
        else:
            # Get the existing category
            category_to_use = next((category for category in data.categories if category.name == category_name), None)

        # If the category_to_use is still None, something went wrong
        if category_to_use is None:
            print("Something went wrong while getting the category to use")
            continue

        # Check if the class already exists in the category
        if class_name not in [test_class.name for test_class in category_to_use.classes]:
            # If not, create a new class and append it to the category
            class_to_use = DotnetTestClass(
                test_class_id="",
                name=class_name,
                tests=[],
                total_tests=0,
                failed_tests=0,
                passed_tests=0,
                total_runtime_in_ms=0
            )
            category_to_use.classes.append(class_to_use)
        else:
            # Get the existing class
            class_to_use = next((test_class for test_class in category_to_use.classes if test_class.name == class_name),
                                None)

        # If the class_to_use is still None, something went wrong
        if class_to_use is None:
            print("Something went wrong while getting the class to use")
            continue

        # Add the test to the class
        class_to_use.tests.append(DotnetTest(
            name=test_definition_name,
            outcome=result.outcome,
            output=result.output,
            duration=result.duration
        ))

    data.update_totals()
    data.update_grade()

    return data


def get_empty_mustache_dotnet_data(assignment_name, log_filename, output_log):
    data = DotnetData(title=assignment_name, log_filename=log_filename, output_log=output_log)
    return data
