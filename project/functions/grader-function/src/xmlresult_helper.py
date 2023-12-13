import xml.etree.ElementTree as ET
import chevron
import os
from typing import Optional, List
import json
from datetime import datetime

XML_NAMESPACE = "{http://microsoft.com/schemas/VisualStudio/TeamTest/2010}"


# Custom xml result models to create a json or dict from the dotnet result xml
class Output:
    message: str
    stacktrace: str

    def __init__(self, message: str, stacktrace: str) -> None:
        self.message = message
        self.stacktrace = stacktrace


class Test:
    name: str
    outcome: str
    duration: int
    output: Optional[Output]
    has_error: bool

    def __init__(self, name: str, outcome: str, duration: int, output: Optional[Output]) -> None:
        self.name = name
        self.outcome = 'failed' if outcome == 'Failed' else 'success'
        self.duration = duration
        self.output = output
        self.has_error = outcome == "Failed"


class TestClass:
    test_class_id: str
    name: str
    total_runtime_in_ms: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    tests: List[Test]

    def __init__(self, test_class_id: str, name: str, total_runtime_in_ms: int, total_tests: int, passed_tests: int,
                 failed_tests: int, tests: List[Test]) -> None:
        self.test_class_id = test_class_id
        self.name = name
        self.total_runtime_in_ms = total_runtime_in_ms
        self.total_tests = total_tests
        self.passed_tests = passed_tests
        self.failed_tests = failed_tests
        self.tests = tests


class Category:
    category_id: str
    name: str
    classes: List[TestClass]
    total_tests: int
    passed_tests: int
    failed_tests: int

    def __init__(self, category_id: str, name: str, classes: List[TestClass]) -> None:
        self.category_id = category_id
        self.name = name
        self.classes = classes
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0


class XmlResultData:
    title: str
    total_runtime_in_ms: int
    total_tests: int
    failed_tests: int
    passed_tests: int
    categories: List[Category]
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
                            "stacktrace": test.output.stacktrace if test.output else None
                        },
                        "has_error": test.has_error,
                    }
                    class_data["tests"].append(test_data)
                category_data["classes"].append(class_data)
            data["categories"].append(category_data)

        return data


# End of custom xml result models


# Models to map to a result xml from dotnet test
class TestResult:
    test_result_id: str
    name: str
    duration: int
    outcome: str
    output: Output

    def __init__(self, test_result_id: str, name: str, duration: int, outcome: str, output: Output) -> None:
        self.test_result_id = test_result_id
        self.name = name
        self.duration = duration
        self.outcome = outcome
        self.output = output


class TestCategoryItem:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class TestCategory:
    test_category_item: TestCategoryItem

    def __init__(self, test_category_item: TestCategoryItem) -> None:
        self.test_category_item = test_category_item


class TestDefinition:
    test_definition_id: str
    name: str
    test_category: TestCategory
    class_name: str

    def __init__(self, test_definition_id: str, name: str, category: TestCategory, class_name: str) -> None:
        self.test_definition_id = test_definition_id
        self.name = name
        self.test_category = category
        self.class_name = class_name


class Testrun:
    run_id: str
    name: str
    results: List[TestResult]
    test_definitions: List[TestDefinition]

    def __init__(self, run_id: str, name: str, results: List[TestResult],
                 test_definitions: List[TestDefinition]) -> None:
        self.run_id = run_id
        self.name = name
        self.results = results
        self.test_definitions = test_definitions


# End of models

def transform_duration_string_to_ms(duration_str):
    # If the length of the duration string is 0, return 0
    if duration_str is None or len(duration_str) == 0:
        return 0
    # Remove the last character from the duration string
    duration_str = duration_str[:-1]
    # Parse the duration string into a timedelta object
    duration = datetime.strptime(duration_str, "%H:%M:%S.%f").time()
    # Calculate the total milliseconds
    milliseconds = (duration.microsecond / 1000) + (duration.second * 1000) + \
                   (duration.minute * 60 * 1000) + (duration.hour * 60 * 60 * 1000)
    return milliseconds



def get_unit_test_results(xml_root):
    """
    Method to read the xml result file and return a list of TestResult objects
    @param xml_root:
    @return: List of TestResult objects
    """
    # Get every unit test result
    unit_test_results = xml_root.findall(XML_NAMESPACE + "Results/" + XML_NAMESPACE + "UnitTestResult")
    # Create a list of TestResult objects
    results = []

    for result in unit_test_results:
        duration_str = result.attrib["duration"] if "duration" in result.attrib else None
        duration = transform_duration_string_to_ms(duration_str)

        output = result.find(XML_NAMESPACE + "Output")
        if output is not None:
            output_message = output.find(XML_NAMESPACE + "ErrorInfo/" + XML_NAMESPACE + "Message")
            output_stacktrace = output.find(XML_NAMESPACE + "ErrorInfo/" + XML_NAMESPACE + "StackTrace")
            output_obj = Output(
                message=output_message.text if output_message is not None else None,
                stacktrace=output_stacktrace.text if output_stacktrace is not None else None
            )
        else:
            output_obj = None

        res = TestResult(
            test_result_id=result.attrib["testId"] if "testId" in result.attrib else None,
            name=result.attrib["testName"] if "testName" in result.attrib else None,
            duration=duration,
            outcome=result.attrib["outcome"] if "outcome" in result.attrib else None,
            output=output_obj
        )
        results.append(res)

    return results


def get_test_definitions(xml_root):
    # Get every unit test definition
    unit_test_definitions = xml_root.findall(XML_NAMESPACE + "TestDefinitions/" + XML_NAMESPACE + "UnitTest")
    # Create a list of TestDefinition objects
    definitions = []

    for definition in unit_test_definitions:
        category = definition.find(XML_NAMESPACE + "TestCategory")
        category_item = category.find(XML_NAMESPACE + "TestCategoryItem")
        test_category = TestCategory(
            test_category_item=TestCategoryItem(
                name=category_item.attrib["TestCategory"] if "TestCategory" in category_item.attrib else None
            )
        )
        method = definition.find(XML_NAMESPACE + "TestMethod")

        defi = TestDefinition(
            test_definition_id=definition.attrib["id"] if "id" in definition.attrib else None,
            name=definition.attrib["name"] if "name" in definition.attrib else None,
            category=test_category,
            class_name=method.attrib["className"] if "className" in method.attrib else None
        )
        definitions.append(defi)

    return definitions


def get_test_run_obj(xml_root):
    # Get the testrun id
    testrun_id = xml_root.attrib["id"] if "id" in xml_root.attrib else None
    # Get the testrun name
    testrun_name = xml_root.attrib["name"] if "name" in xml_root.attrib else None

    # Create a testrun object
    testrun = Testrun(
        run_id=testrun_id,
        name=testrun_name,
        results=get_unit_test_results(xml_root),
        test_definitions=get_test_definitions(xml_root)
    )

    return testrun


def get_mustache_data(path_to_xml, assignment_name, log_filename, output_log):
    # Create a data object
    data = XmlResultData(title=assignment_name, log_filename=log_filename, output_log=output_log)

    # If the xml file does not exist, there has been a compile error
    if not os.path.isfile(path_to_xml):
        data.has_compile_error = True
        return data

    # Parse the xml
    tree = ET.parse(path_to_xml)
    root = tree.getroot()
    run = get_test_run_obj(root)
    # Create the classes
    classes = []
    for result in run.results:
        # Get the class name for this result
        test_definition = next((test_definition for test_definition in run.test_definitions if
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
            category_to_use = Category(
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
            class_to_use = TestClass(
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
            class_to_use = next((test_class for test_class in category_to_use.classes if test_class.name == class_name), None)

        # If the class_to_use is still None, something went wrong
        if class_to_use is None:
            print("Something went wrong while getting the class to use")
            continue

        # Add the test to the class
        class_to_use.tests.append(Test(
                name=test_definition_name,
                outcome=result.outcome,
                output=result.output,
                duration=result.duration
            ))

    data.update_totals()
    data.update_grade()

    return data


def generate_html_report(template_path, output_path, data):
    # Read the template
    with open(template_path, 'r') as f:
        result = chevron.render(f, data)
    f.close()

    # Write the result
    with open(output_path, 'w') as f:
        f.write(result)
    f.close()

    return output_path
