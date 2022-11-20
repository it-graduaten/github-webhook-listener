import json
import codegrade
import os
import re
import shutil
import codegrade.models as cgmodels
from codegrade.models import PatchCourseData
from codegrade.models import CreateAutoTestData, JsonCreateAutoTest, PutRubricAssignmentData, UpdateSuiteAutoTestData, RunProgramInputAsJSON, RunProgramData, UpdateSetAutoTestData
from codegrade.models.types import File
import github_helper

with codegrade.login(
            username=os.getenv("CG_USERNAME"),
            password=os.getenv('CG_PASSWORD'),
            tenant="7b13b097-a2b3-4b71-a488-e84d38851210"
        ) as client:
            pass
    

def check_if_codegrade_assignment_exists(assignment_name, course_id):
    """ This method searches codegrade for the assignment with the given name. Returns he assignment if it exists, otherwise None.
    """
    # Get the course
    c = client.course.get(course_id=course_id)
    # Get all the assignments
    for a in c.assignments:
        # Check if the assignment name matches the given name
        if assignment_name == a.name:
            # Return the assignment
            return a
    # Return None if no assignment was found
    return None

def delete_existing_autotest(assignment_id):
    """ Deletes the existing autotest configuration if one exists. """
    res = client.assignment.get(assignment_id=assignment_id)
    if res.auto_test_id is not None:
        current_auto_test_id = res.auto_test_id
        # Get current auto test
        res = client.auto_test.get(auto_test_id=current_auto_test_id)
        # Stop current autotest run if it is running
        if len(res.runs) == 1:
            print("Stopping auto test..")
            current_run_id = res.runs[0].id
            res = client.auto_test.stop_run(
                auto_test_id=current_auto_test_id, run_id=current_run_id)
        print("Deleting auto test..")
        client.auto_test.delete(auto_test_id=current_auto_test_id)

    try:
        print("Deleting rubric..")
        res = client.assignment.delete_rubric(assignment_id=assignment_id)
    except:
        print("No rubric to delete")

def get_test_configurations(resources_dir):
    test_configs = []

    # For each file in the resources directory
    for file in os.listdir(resources_dir + "/test"):
        if 'Base' not in file and '.csproj' not in file and '.cs' in file:
            # Read file line by line
            model_name = file[:file.index("Tests.cs")]

            with open(resources_dir + "/test/" + file, 'r') as f:
                lines = f.readlines()
                test_name_pattern = re.compile("public .*\(")
                test_weight_pattern = re.compile("Weight\([0-9]*\.*[0-9]*\)")        
                weights = []
                test_names = []
                for line in lines:
                    for match in re.finditer(test_weight_pattern, line):
                        weight = line[line.index("(") + 1:line.index(")")]
                        weights.append(weight)

                    for match in re.finditer(test_name_pattern, line):
                        pieces = line.strip().split(" ")
                        test_name = pieces[2][:pieces[2].index("(")]
                        test_names.append(test_name)

                    if "namespace" in line:
                        namespace = line.replace("namespace", "").strip()

                    if "class" in line:
                        pieces = line.strip().split(" ")
                        class_name = pieces[2]
                zip_iterator = zip(test_names, weights)
                test_dict = dict(zip_iterator)
                # Class weight is the sum of all test weights
                class_weight = sum(float(weight) for weight in weights)
                test_configs.append({"name": model_name, "tests": test_dict, "class_weight": class_weight, "namespace": namespace, "class_name": class_name})

    return test_configs

def create_rubrics(assignment, test_configurations):
    """ Create rubrics for the assignment. """

    rubric = {
    "max_points": 0,
    "rows": [
      {
        "header": "Unit tests",
        "description": "This is my description",
        "items": [
          {
            "description": "",
            "header": "Min points",
            "points": 0
          },
          {
            "description": "",
            "header": "Max points",
            "points": 10
          }
        ],
        "type": "continuous"
      }
    ]
  }

    rubric = {'rows': [], 'max_points': 0}
    rubric['max_points'] = 1
    rubric["rows"].append({
        "header": "Compile code",
        "description": "Checks if your code compiles.",
        "type": "continuous",
        "items": [
                {
                    "description": "",
                    "header": "Min points",
                    "points": 0
                },
            {
                    "description": "",
                    "header": "Max points",
                    "points": 1
            }
        ]
    })

    for test_dict in test_configurations:
        rubric['max_points'] += float(test_dict['class_weight'])
        rubric["rows"].append({
            "header": test_dict["name"],
            "description": "",
            "type": "continuous",
            "items": [
                {
                    "description": "",
                    "header": "Min points",
                    "points": 0
                },
                {
                    "description": "",
                    "header": "Max points",
                    "points": float(test_dict['class_weight'])
                }
            ]
        })

    # Create rubric and get ID's of rubric rows in order of creation
    print("Creating rubric..")
    res = client.assignment.put_rubric(json_body=rubric, assignment_id=assignment.id)
    rubric_row_ids = []
    for r in res:
        rubric_row_ids.append(r.id)
    return rubric_row_ids

def create_test_suite(rubric_row_id, test_dict):
    test_suite = {
        "submission_info": False,
        "command_time_limit": 120,
        "steps": [],
        "rubric_row_id": 0,
        "network_disabled": True
        }

    test_suite["rubric_row_id"] = rubric_row_id

    for key, val in test_dict['tests'].items():
        step = {
            "type": "junit_test",
            "data": {
                "wrapper": "cg_xunit",
                "metadata": {
                "testProject": "project_test/project_test.csproj",
                "xunitArguments": "--filter FullyQualifiedName=project_test.ClassTests.MethodTest"
                },
                "program": "cg-xunit run -- pakjesdienst_test/pakjesdienst_test.csproj --filter FullyQualifiedName=pakjesdienst_test.PackageTests.ToStringTest"
            },
            "description": "",
            "name": "ControlesTests",
            "weight": 10,
            "hidden": False
            }
        step['weight'] = float(val)
        step['data']['metadata']['testProject'] = f"test/test.csproj"
        step['data']['metadata'][
            'xunitArguments'] = f"--filter FullyQualifiedName={test_dict['namespace']}.{test_dict['class_name']}.{key}"
        step['name'] = key
        step['data'][
            'program'] = f"cg-xunit run -- test/test.csproj --filter FullyQualifiedName={test_dict['namespace']}.{test_dict['class_name']}.{key}"
        test_suite['steps'].append(step)

    return test_suite

def create_autotest(assignment, files):
    print("Creating autotest configruation..")
    data = codegrade.models.CreateAutoTestData(
        json=codegrade.models.json_create_auto_test.JsonCreateAutoTest(
            assignment_id=assignment.id,
            setup_script="\"$FIXTURES\"/setup.sh;",
            run_setup_script=f"unzip codegrade_temp.zip && cg-xunit install_extra test/",
            has_new_fixtures=True,
            enable_caching=True,
            grade_calculation="full",
            results_always_visible=True,
            prefer_teacher_revision=False),
        fixture=files
    )
    res = client.auto_test.create(multipart_data=data)
    # Close all files
    for f in files:
        f.payload.close()
    return res.id

def create_compilation_level(auto_test_id, compilation_rubric_row_id):
    res = client.auto_test.add_set(auto_test_id=auto_test_id)
    steps = []
    steps.append(RunProgramInputAsJSON(type="run_program",
                                       name="Compile code",
                                       weight=1,
                                       hidden=False,
                                       description="Checks if your code compiles.",
                 data=RunProgramData(program=f"dotnet build test")))
    client.auto_test.update_suite(
        json_body=UpdateSuiteAutoTestData(
            steps=steps, rubric_row_id=compilation_rubric_row_id, network_disabled=True),
        auto_test_id=auto_test_id, set_id=res.id)

    client.auto_test.update_set(json_body=UpdateSetAutoTestData(
        stop_points=1), auto_test_id=auto_test_id, auto_test_set_id=res.id)

def create_unittest_level(auto_test_id, test_rubric_ids, test_configurations):
    del test_rubric_ids[0]
    print("Creating suite with steps..")
    res = client.auto_test.add_set(auto_test_id=auto_test_id)
    for idx in range(len(test_configurations)):
        test_suite = create_test_suite(rubric_row_id=test_rubric_ids[idx], test_dict=test_configurations[idx])
        res = client.auto_test.update_suite(
            json_body=test_suite, auto_test_id=auto_test_id, set_id=res.id)

def start_autotest(auto_test_id):
    # Start the autotest
    print("Starting autotest..")
    res = client.auto_test.start_run(auto_test_id=auto_test_id)

def create_zip_file(dir):
    """ Creates the zip file which is needed for the autotest """
    """ Creates a zipfile of the project directory. """
    temp_dir = "codegrade_temp"
    # Delete temp dir if it exists
    if os.path.exists(os.path.join(dir, temp_dir)):
        shutil.rmtree(os.path.join(dir, temp_dir))
    # Create temp dir
    os.mkdir(os.path.join(dir, temp_dir))
    # Copy test folder to the temporary directory
    shutil.copytree(os.path.join(dir, "test"),
                    os.path.join(dir, temp_dir, "test"))
    # Copy models folder to the temporary directory
    shutil.copytree(os.path.join(dir, "models"),
                    os.path.join(dir, temp_dir, "models"),
                    ignore=shutil.ignore_patterns("*.cs"))
    # Create zip file of the temporary directory
    shutil.make_archive(os.path.join(dir, temp_dir), 'zip',
                        os.path.join(dir, temp_dir))

    # Remove the temporary directory
    shutil.rmtree(os.path.join(dir, temp_dir))

    zipfile_path = os.path.join(dir, temp_dir + ".zip")

    zipfile = File(payload=open(zipfile_path, 'rb'),
                   file_name=f"{temp_dir}.zip")
    return zipfile

def get_resources():
    """ Gets the resources which are needed for the autotest """
    files = [File(payload=open('codegrade_resources/setup.sh', 'rb'), file_name="setup.sh")]
    return files

def update_codegrade_assignment(assignment, evaluation_files, resources_dir):
    """ Configures the assignment with the given evaluation files. """
    delete_existing_autotest(assignment_id=assignment.id)
    test_configs = get_test_configurations(resources_dir)
    rubrics = create_rubrics(assignment=assignment, test_configurations=test_configs)
    files = get_resources()
    files.append(create_zip_file(resources_dir))
    auto_test_id = create_autotest(assignment=assignment, files=files)
    compilation_set_id = create_compilation_level(auto_test_id, rubrics[0])
    create_unittest_level(auto_test_id, rubrics, test_configs)
    start_autotest(auto_test_id)
