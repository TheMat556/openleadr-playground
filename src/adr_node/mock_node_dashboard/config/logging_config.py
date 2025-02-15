from dataclasses import dataclass


@dataclass
class LoggingConfig:
  """
  Configuration for logging.

  :param level: Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
  :type level: str
  :param format: Format string for log messages.
  :type format: str
  """

  level: str = 'INFO'
  format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
