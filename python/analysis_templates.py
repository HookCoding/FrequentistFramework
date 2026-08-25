from __future__ import annotations

import re
import sys


def replaceinfile(file_path, old_new_list):
    with open(file_path, "r") as file:
        filedata = file.read()

    try:
        for old_text, new_text in old_new_list:
            filedata = re.sub(old_text, new_text, filedata)
    except Exception:
        print(
            "ERROR: replaceinfile expects a list of tuples of strings " "[(old1,new1),...] as input"
        )
        print(old_new_list)
        sys.exit(-1)

    with open(file_path, "w") as file:
        file.write(filedata)
