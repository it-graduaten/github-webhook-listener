import xml.etree.ElementTree as ET

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





   