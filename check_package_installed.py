import subprocess

conda_cmd = 'C:/Soft/miniconda3/Library/bin/conda.bat'

def get_conda_envs():
    result = subprocess.run([conda_cmd, "env", "list"], capture_output=True, text=True)
    result_lines = result.stdout.splitlines()[3:]  # Skip over the heading lines
    envs = [line.split()[0] for line in result_lines if line]
    return envs


def check_package_in_envs(package_name):
    envs = get_conda_envs()

    for env in envs:
        result = subprocess.run([conda_cmd, "list", "-n", env], capture_output=True, text=True)
        if package_name in result.stdout:
            print(f"'{package_name}' is installed in {env}")
        else:
            print(f"'{package_name}' is NOT installed in {env}")


check_package_in_envs('transformers')7