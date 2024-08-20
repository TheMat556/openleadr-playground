import subprocess
import sys

def run_command(command):
    """
    Execute a shell command and handle errors.

    This function runs a shell command using `subprocess.run`. If the command
    returns a non-zero exit status, an error message is printed to the standard
    error stream and the program exits with the same status code as the command.

    Args:
        command (str): The shell command to execute.

    Raises:
        SystemExit: If the command returns a non-zero exit status.
    """
    result = subprocess.run(command, shell=True, check=True)
    if result.returncode != 0:
        print(f"Command failed: {command}", file=sys.stderr)
        sys.exit(result.returncode)