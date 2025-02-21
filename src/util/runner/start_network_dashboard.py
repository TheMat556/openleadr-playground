from src.util.helper.run_command import run_command
from src.util.helper.startup_banner import print_startup_banner

COMPONENT_NAME = 'Node Dashboard'
COMMAND = 'python -m src.network_dashboard'

print_startup_banner(COMPONENT_NAME, COMMAND)
run_command(COMMAND)
