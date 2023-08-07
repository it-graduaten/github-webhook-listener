import os
import sys
import typing as t
import subprocess
import json
from xml.dom import minidom
import subprocess
import re
from custom_types import TestRunResult

class TestRunner:
    kXmlReportName = 'result.xml'
    logger = None

    def __init__(self, logger):
        self.logger = logger
        pass

    def run_tests(self, path_to_test_project):
        self.logger.debug(f'Running tests for {path_to_test_project}..')
        restore_command = f'dotnet restore {path_to_test_project}'
        self.logger.debug(restore_command)
        return_code = subprocess.call(restore_command, shell=True)
        command = f'dotnet test {path_to_test_project} -l:\"trx;LogFileName={self.kXmlReportName}\" --verbosity="quiet"'
        self.logger.debug(command)
        return_code = subprocess.call(command, shell=True)
        self.logger.debug(f'Finished running tests for {path_to_test_project}')

    def extract_weight_from_name(self, name: str):
        """Extract the weight and name from a step.

        :returns: A tuple with the weight (or ``None`` if not found) and the name
                  (stripped of the weight).
        """
        weight_match = self._WEIGHT_REGEX.match(name)
        if weight_match is None:
            weight = 1
        else:
            weight = int(weight_match.group('weight'))
            name = weight_match.group('test_name')

        return (weight, name)

    def get_test_run_result(self, path_to_test_project) -> TestRunResult:
        # Check if file exists
        if not os.path.exists(f'{path_to_test_project}/TestResults/result.xml'):
            self.logger.debug("It seems like your tests were not run. Check the correctness of the dotnet built step before.")
            return {
            'total': -1,
            'errors': -1,
            'grade': -1,
        }

        # Parse the XML file
        xmldoc = minidom.parse(f'{path_to_test_project}/TestResults/result.xml')
        testResults = xmldoc.getElementsByTagName('UnitTestResult')

        errors = 0
        total = 0

        for testResult in testResults:
            total += 1
            if testResult.getAttribute('outcome') == 'Failed':
                errors += 1

        grade_per_test = 10 / total

        return {
            'total': total,
            'errors': errors,
            'grade': round(10 - (errors * grade_per_test), 1),
        }