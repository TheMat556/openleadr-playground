from run_command import run_command
from startup_banner import print_startup_banner

COMPONENT_NAME = 'Mock Node'
COMMAND = 'python -m src.mock_node'

print_startup_banner(COMPONENT_NAME, COMMAND)
run_command(COMMAND)
