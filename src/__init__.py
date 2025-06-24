import os
import sys
import runpy

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    sys.path.insert(0, project_root)  # Ensure the project root is in the system path
    runpy.run_path("app.py", run_name="__main__")
