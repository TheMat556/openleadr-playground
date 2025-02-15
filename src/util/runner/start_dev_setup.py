from src.util.helper.run_command import run_command
from src.util.helper.startup_banner import print_startup_banner

COMPONENT_NAME = 'Development Environment'
COMMAND = 'python -m development'
print_startup_banner(COMPONENT_NAME, COMMAND)
run_command(COMMAND)
