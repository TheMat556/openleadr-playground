from dataclasses import dataclass


@dataclass
class LoggingConfig:
  level: str = 'INFO'
  format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
