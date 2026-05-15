import subprocess
import sys
import os

# Set which test to run: "test1" (IPA) or "test2" (LOX)
TEST = "test1"

os.environ["TEST"] = TEST

scripts = [
    "process_raw.py",
    "calc_mass_flow.py",
    "cda_calculations.py",
    "graph_cda.py",
]

for script in scripts:
    print(f"Running {script}...")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"Error running {script}, stopping.")
        sys.exit(1)

print("All done.")
