import os
from datetime import timedelta

import numpy as np
from dotenv import load_dotenv

from src.openadr_node.models import ReportConfiguration
from src.openadr_node.node_manager import NodeManager

def sample_callback_1():
  print("callback 1")
  return np.random.rand() * 10

def sample_callback_2():
  print("callback 2")
  return np.random.rand() * 10

def main():
  load_dotenv()
  reports = [
    ReportConfiguration(
      resource_id="res_123",
      measurement="energy",
      sampling_rate=timedelta(seconds=5),
      callback=sample_callback_1,
      additional_metadata={"unit": "Celsius", "location": "Room 101"}
    ),
    ReportConfiguration(
      resource_id="res_456",
      measurement="energy",
      sampling_rate=timedelta(seconds=5),
      callback=sample_callback_2,
      additional_metadata={"unit": "%", "location": "Room 202"}
    )
  ]

  node_manager = NodeManager(
    # vtn_name=os.getenv('SERVER_NAME'),
    ven_name=os.getenv('VEN_NAME'),
    vtn_url=os.getenv('VTN_URL'),
  )
  node_manager.add_report(reports)
  node_manager.run_node()
  pass


if __name__ == '__main__':
  main()
