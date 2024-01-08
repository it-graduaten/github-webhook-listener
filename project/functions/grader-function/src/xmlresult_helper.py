import xml.etree.ElementTree as ET
import chevron
import os
from typing import Optional, List
import json
from datetime import datetime

XML_NAMESPACE = "{http://microsoft.com/schemas/VisualStudio/TeamTest/2010}"


# Models to map to a result xml from dotnet test
class UnitTestResultXmlOutput:
    message: str
    stacktrace: str
    stdout: str

    def __init__(self, message: str, stacktrace: str, stdout: str) -> None:
        self.message = message
        self.stacktrace = stacktrace
        self.stdout = stdout


class UnitTestResultXmlTestResult:
    test_result_id: str
    name: str
    duration: int
    outcome: str
    output: UnitTestResultXmlOutput

    def __init__(self, test_result_id: str, name: str, duration: int, outcome: str,
                 output: UnitTestResultXmlOutput) -> None:
        self.test_result_id = test_result_id
        self.name = name
        self.duration = duration
        self.outcome = outcome
        self.output = output


class UnitTestResultXmlTestCategoryItem:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class UnitTestResultXmlTestCategory:
    test_category_item: UnitTestResultXmlTestCategoryItem

    def __init__(self, test_category_item: UnitTestResultXmlTestCategoryItem) -> None:
        self.test_category_item = test_category_item


class UnitTestResultXmlTestDefinition:
    test_definition_id: str
    name: str
    test_category: UnitTestResultXmlTestCategory
    class_name: str

    def __init__(self, test_definition_id: str, name: str, category: UnitTestResultXmlTestCategory,
                 class_name: str) -> None:
        self.test_definition_id = test_definition_id
        self.name = name
        self.test_category = category
        self.class_name = class_name


class UnitTestResultXmlTestrun:
    run_id: str
    name: str
    results: List[UnitTestResultXmlTestResult]
    test_definitions: List[UnitTestResultXmlTestDefinition]

    def __init__(self, run_id: str, name: str, results: List[UnitTestResultXmlTestResult],
                 test_definitions: List[UnitTestResultXmlTestDefinition]) -> None:
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
            output_stdout = output.find(XML_NAMESPACE + "StdOut")
            stdout_text = output_stdout.text if output_stdout is not None else None
            print(stdout_text)
            if stdout_text is not None and 'Debug Trace:\n' in stdout_text:
                stdout_text = stdout_text.replace('Debug Trace:\n', '')
            output_obj = UnitTestResultXmlOutput(
                message=output_message.text if output_message is not None else None,
                stacktrace=output_stacktrace.text if output_stacktrace is not None else None,
                stdout=stdout_text
            )
        else:
            output_obj = None

        res = UnitTestResultXmlTestResult(
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
        test_category = UnitTestResultXmlTestCategory(
            test_category_item=UnitTestResultXmlTestCategoryItem(
                name=category_item.attrib["TestCategory"] if "TestCategory" in category_item.attrib else None
            )
        )
        method = definition.find(XML_NAMESPACE + "TestMethod")

        defi = UnitTestResultXmlTestDefinition(
            test_definition_id=definition.attrib["id"] if "id" in definition.attrib else None,
            name=definition.attrib["name"] if "name" in definition.attrib else None,
            category=test_category,
            class_name=method.attrib["className"] if "className" in method.attrib else None
        )
        definitions.append(defi)

    return definitions


def transform_xml_to_unittest_result(path_to_xml):
    """
    @param path_to_xml: The path to the xml file
    @return: A Testrun object if the xml file exists, otherwise None
    """
    # Check if the xml file exists
    if not os.path.isfile(path_to_xml):
        return None
    # Parse the xml
    tree = ET.parse(path_to_xml)
    root = tree.getroot()
    # Get the testrun id
    testrun_id = root.attrib["id"] if "id" in root.attrib else None
    # Get the testrun name
    testrun_name = root.attrib["name"] if "name" in root.attrib else None

    # Create a testrun object
    testrun = UnitTestResultXmlTestrun(
        run_id=testrun_id,
        name=testrun_name,
        results=get_unit_test_results(root),
        test_definitions=get_test_definitions(root)
    )

    return testrun
