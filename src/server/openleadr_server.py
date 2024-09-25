import logging
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Union, Tuple

from openleadr import OpenADRServer, enable_default_logging
from openleadr.objects import Interval
from openleadr.utils import generate_id

from ..openleadr_node.config.config import Config
from ..sqlite.sqlite import Database

# Setup logging
enable_default_logging()
logger = logging.getLogger(__name__)


class OpenLeADRServer:
  """
  A class to represent and manage the OpenADR server, handle party registrations, and process reports.

  Attributes
  ----------
  server : OpenADRServer
      The OpenADR server instance.
  db_conn : Database
      The database connection instance.
  loop : asyncio.AbstractEventLoop
      The asyncio event loop.
  """

  def __init__(self, server_name: str, db_name: str, config: Config):
    """
    Initializes the OpenLeADRServer with the provided server name and database name.

    Parameters
    ----------
    server_name : str
        The name of the server.
    db_name : str
        The name of the SQLite database file.
    """
    self.server = OpenADRServer(vtn_id=server_name)
    self.server.add_handler(
      'on_create_party_registration', self.on_create_party_registration
    )
    self.server.add_handler('on_register_report', self.on_register_report)

    self.db_conn = Database(db_name)
    self.config = config

  async def on_create_party_registration(
    self, registration_info: dict
  ) -> Union[Tuple[str, str], bool]:
    """
    Handles the creation of party registrations, assigning VEN IDs and registration IDs as needed.

    Parameters
    ----------
    registration_info : dict
        Dictionary containing registration information including ven_name.

    Returns
    -------
    Union[Tuple[str, str], bool]
        Returns a tuple (ven_id, registration_id) if the registration was processed successfully.
        Returns False if the VEN already exists or if no VEN name is provided.
    """
    ven_name = registration_info.get('ven_name')
    result = self.db_conn.fetch_ven(ven_name=ven_name)

    if result is not None:
      ven_id = generate_id()
      registration_id = generate_id()

      self.db_conn.update_ven(ven_name, ven_id, registration_id)
      self.config.set_ven_id(ven_id)
      logger.info(f'Registered new VEN: {ven_name} with ID: {ven_id}')

      return ven_id, registration_id
    else:
      logger.info(f'VEN {ven_name} already exists.')
      return False

  async def on_register_report(
    self,
    ven_id: str,
    resource_id: str,
    measurement: str,
    unit: str,
    scale: str,
    min_sampling_interval: int,
    max_sampling_interval: int,
  ) -> tuple:
    """
    Handles report registrations from VENs and provides a callback and sampling interval.

    Parameters
    ----------
    ven_id : str
        The ID of the VEN.
    resource_id : str
        The ID of the resource.
    measurement : str
        The type of measurement.
    unit : str
        The unit of measurement.
    scale : str
        The scale of measurement.
    min_sampling_interval : int
        The minimum sampling interval.
    max_sampling_interval : int
        The maximum sampling interval.

    Returns
    -------
    tuple
        A tuple containing the callback function and the sampling interval.
    """
    callback = partial(
      self.on_update_report,
      ven_id=ven_id,
      resource_id=resource_id,
      measurement=measurement,
    )

    sampling_interval = min_sampling_interval
    return callback, sampling_interval

  async def store_voltage(self, data):
    pass

  async def on_update_report(
    self, data: list, ven_id: str, resource_id: str, measurement: str
  ):
    """
    Handles and logs report data received from VENs.

    Parameters
    ----------
    data : list
        A list of tuples containing (time, value) pairs.
    ven_id : str
        The ID of the VEN.
    resource_id : str
        The ID of the resource.
    measurement : str
        The type of measurement.
    """
    for time, value in data:
      print(
        f'VEN {ven_id} reported {measurement} = {value} at {time} for resource {resource_id}'
      )

      self.db_conn.store_values(ven_id, time, value)

      if value < 200:
        self.server.add_event(
          ven_id=ven_id,
          signal_name='simple',
          signal_type='level',
          intervals=[
            Interval(
              dtstart=datetime.now(tz=timezone.utc),
              duration=timedelta(minutes=10),
              signal_payload=1,
            ),
          ],
          callback=self.event_callback,
        )

  async def event_callback(self, ven_id: str, event_id: str, opt_type: str):
    print(f'The VEN decided to {opt_type}')
