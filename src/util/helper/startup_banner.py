import os
import subprocess
from datetime import datetime, timezone


def clear_screen():
  """Clear the terminal screen."""
  command = 'cls' if os.name == 'nt' else 'clear'
  try:
    subprocess.run([command], shell=True, check=True)
  except subprocess.SubprocessError:
    print('\n' * 100)


def get_current_time():
  """Get formatted current UTC time."""
  return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def get_user():
  """Retrieve the current user or return 'unknown' if not available."""
  try:
    return os.getlogin() if hasattr(os, 'getlogin') else os.getenv('USER', 'unknown')
  except OSError:
    return 'unknown'


def print_startup_banner(component_name: str, command: str):
  """
  Print a banner with aligned text and emojis.

  Args:
      component_name (str): Name of the component being launched
      command (str): Command being executed
  """
  message = f"""
    ⚡️ Current Time (UTC): {get_current_time()}
    👤 User: {get_user()}

             @@@@@@@@@@@@@@@                     🚀 Welcome to OpenADR Node System!
         @@@@@@@@@@@@@@@@@@@@@                   ==============================
       @@@@@@@@@@@@@@@  @@@@@@@@
     @@@@@@@@@@@@@@    @@@@@@@@@@@              🔧 Development Mode
     @@@@@@@@@@        @@@@@@@@@@@              ⚙️ System: {os.name.upper()}
    @@@@@@@@@         @@@@@@@@@@@@              🌟 Version: 1.0.0
    @@@@@@@@@@@@@        @@@@@@@@@
     @@@@@@@@@@@      @@@@@@@@@@@@              🎯 Starting: {component_name}
      @@@@@@@@@   @@@@@@@@@@@@@@@               🔄 Command: {command}
        @@@@@@@@@@@@@@@@@@@@@@@                 ⏳ Please wait...
          @@@@@@@@@@@@@@@@@@@
              @@@@@@@@@@@

    🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧

        💻 You are launching {component_name}.
        🚀 Get ready to code!

    🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧🚧
    """
  clear_screen()
  print(message)
