import os
import subprocess
import sys


def execute(cmd):
    print("EXECUTE:", cmd)
    sys.stdout.flush()  # keeps print and subprocess output in sync
    rtv = subprocess.call(cmd, shell=True)
    return rtv


def execute_required(cmd, description, expected_outputs=()):
    for output_path in expected_outputs:
        if os.path.lexists(output_path):
            os.remove(output_path)

    rtv = execute(cmd)

    if rtv != 0:
        print(
            "ERROR: {} failed with exit code {}.".format(
                description,
                rtv,
            )
        )
        return False

    missing_outputs = [
        output_path for output_path in expected_outputs if not os.path.isfile(output_path)
    ]
    if missing_outputs:
        print(
            "ERROR: {} returned success but did not create required output files:".format(
                description
            )
        )
        for output_path in missing_outputs:
            print("  - {}".format(output_path))
        return False

    return True
