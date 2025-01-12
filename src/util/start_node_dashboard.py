from run_command import run_command
from startup_banner import print_startup_banner

COMPONENT_NAME = 'Node Dashboard'
COMMAND = 'python -m src.node_dashboard'

print_startup_banner(COMPONENT_NAME, COMMAND)
run_command(COMMAND)
