import xml.etree.ElementTree as ET
import chevron
from typing import Optional, List
import json

XML_NAMESPACE = "{http://microsoft.com/schemas/VisualStudio/TeamTest/2010}"


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

    def __init__(self, name: str, outcome: str, duration: int, output: Optional[Output]) -> None:
        self.name = name
        self.outcome = outcome
        self.duration = duration
        self.output = output


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
    grade: int

    def __init__(self, title: str, total_runtime_in_ms: int, total_tests: int, failed_tests: int, passed_tests: int,
                 categories: List[Category]) -> None:
        self.title = title
        self.total_runtime_in_ms = total_runtime_in_ms
        self.total_tests = total_tests
        self.failed_tests = failed_tests
        self.passed_tests = passed_tests
        self.categories = categories
        self.grade = round(10 - (failed_tests * (10 / total_tests)), 1)

    def to_json(self):
        data = {
            "title": self.title,
            "total_runtime_in_ms": self.total_runtime_in_ms,
            "total_tests": self.total_tests,
            "failed_tests": self.failed_tests,
            "passed_tests": self.passed_tests,
            "categories": [],
            "grade": self.grade
        }

        for category in self.categories:
            category_data = {
                "name": category.name,
                "classes": []
            }
            for test_class in category.classes:
                class_data = {
                    "name": test_class.name,
                    "total_runtime_in_ms": test_class.total_runtime_in_ms,
                    "total_tests": test_class.total_tests,
                    "passed_tests": test_class.passed_tests,
                    "failed_tests": test_class.failed_tests,
                    "tests": []
                }
                for test in test_class.tests:
                    test_data = {
                        "name": test.name,
                        "outcome": test.outcome,
                        "duration": test.duration,
                        "output": {
                            "message": test.output.message if test.output else None,
                            "stacktrace": test.output.stacktrace if test.output else None
                        }
                    }
                    class_data["tests"].append(test_data)
                category_data["classes"].append(class_data)
            data["categories"].append(category_data)

        return json.dumps(data, indent=4)

    def to_dict(self):
        data = {
            "title": self.title,
            "total_runtime_in_ms": self.total_runtime_in_ms,
            "total_tests": self.total_tests,
            "failed_tests": self.failed_tests,
            "passed_tests": self.passed_tests,
            "categories": [],
            "grade": self.grade
        }

        for category in self.categories:
            category_data = {
                "name": category.name,
                "classes": [],
                "id": category.category_id
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
                    }
                    class_data["tests"].append(test_data)
                category_data["classes"].append(class_data)
            data["categories"].append(category_data)

        return data


class TestResult:
    test_result_id: str
    name: str
    duration: int
    outcome: str

    def __init__(self, test_result_id: str, name: str, duration: int, outcome: str) -> None:
        self.test_result_id = test_result_id
        self.name = name
        self.duration = duration
        self.outcome = outcome


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


def get_test_results_grade(path_to_xml):
    namespace = "{http://microsoft.com/schemas/VisualStudio/TeamTest/2010}"

    tree = ET.parse(path_to_xml)
    root = tree.getroot()

    # TODO: Generate a report the user can see
    # for el in root.iter(f'{namespace}UnitTestResult'):
    # print(el.tag)

    # Get the result summary
    result_summary = root.find(f'{namespace}ResultSummary')
    outcome = result_summary.attrib['outcome']
    # Get the counters
    counters = result_summary.find(f'{namespace}Counters')
    total = int(counters.attrib['total'])
    passed = int(counters.attrib['passed'])
    failed = int(counters.attrib['failed'])

    # Calculate the grade
    grade_per_test = 10 / total
    grade = round(10 - (failed * grade_per_test), 1)
    return grade


def get_unit_test_results(xml_root):
    # Get every unit test result
    unit_test_results = xml_root.findall(XML_NAMESPACE + "Results/" + XML_NAMESPACE + "UnitTestResult")
    # Create a list of TestResult objects
    results = []

    for result in unit_test_results:
        res = TestResult(
            test_result_id=result.attrib["testId"] if "testId" in result.attrib else None,
            name=result.attrib["testName"] if "testName" in result.attrib else None,
            # TODO: Fix duration to be in milliseconds
            duration=0,
            outcome=result.attrib["outcome"] if "outcome" in result.attrib else None
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


def get_mustache_data(path_to_xml):
    # Parse the xml
    tree = ET.parse(path_to_xml)
    root = tree.getroot()
    run = get_test_run_obj(root)
    # Create a data object
    data = XmlResultData(
        title="Test Results",
        total_runtime_in_ms=0,
        total_tests=5,
        failed_tests=4,
        passed_tests=1,
        categories=[]
    )
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
        # Check if a category with the name already exists
        if category_name not in [category.name for category in data.categories]:
            # Create a new category
            new_category = Category(
                category_id=category_name,
                name=category_name,
                classes=[]
            )
            # Check if the class already exists
            if class_name not in [test_class.name for test_class in classes]:
                # Create a new class
                new_class = TestClass(
                    test_class_id="",
                    name=class_name,
                    tests=[],
                    total_tests=0,
                    failed_tests=0,
                    passed_tests=0,
                    total_runtime_in_ms=0
                )
                # Add the test to the class
                new_class.tests.append(Test(
                    name=test_definition_name,
                    outcome=result.outcome,
                    output=None,  # Todo: fix output
                    duration=0  # Todo: Fix duration
                ))
                # Add the class to the category
                new_category.classes.append(new_class)
            else:
                # Get the class
                new_class = next((test_class for test_class in classes if test_class.name == class_name), None)
                # Add the test to the class
                new_class.tests.append(Test(
                    name=test_definition_name,
                    outcome=result.outcome,
                    output=None,  # Todo: fix output
                    duration=0  # Todo: Fix duration
                ))
            # Add the category to the data
            data.categories.append(new_category)
        else:
            # Get the category
            new_category = next((category for category in data.categories if category.name == category_name), None)
            # Get the class in the category
            new_class = next((test_class for test_class in new_category.classes if test_class.name == class_name), None)
            # Add the test to the class
            new_class.tests.append(Test(
                name=test_definition_name,
                outcome=result.outcome,
                output=None,  # Todo: fix output
                duration=0  # Todo: Fix duration
            ))

    # Calculate all totals
    for cat in data.categories:
        for cl in cat.classes:
            cl.total_tests = len(cl.tests)
            cl.failed_tests = len([test for test in cl.tests if test.outcome == "Failed"])
            cl.passed_tests = len([test for test in cl.tests if test.outcome == "Passed"])
            cl.total_runtime_in_ms = sum([test.duration for test in cl.tests])
        cat.total_tests = sum([test_class.total_tests for test_class in cat.classes])
        cat.failed_tests = sum([test_class.failed_tests for test_class in cat.classes])
        cat.passed_tests = sum([test_class.passed_tests for test_class in cat.classes])
    data.total_tests = sum([category.total_tests for category in data.categories])
    data.failed_tests = sum([category.failed_tests for category in data.categories])
    data.passed_tests = sum([category.passed_tests for category in data.categories])

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
