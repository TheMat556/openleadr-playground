from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from threading import Lock

import numpy as np
from src.openadr_node import logger
from src.openadr_node.models.event import ResourceConsumption
from src.openadr_node.database.loadprofile_manager import LoadProfileManager
from pydispatch import dispatcher


class NodeResourceController:
    def __init__(self, load_profile_manager: LoadProfileManager):
        self._load_profile_manager = load_profile_manager
        self._ven_data: Dict[str, Dict[str, float]] = {}
        self._current_consumption = 0.0
        self._lock = Lock()
        self._z = None

    @staticmethod
    def process_load_profile_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process the load profile data.

        Parameters
        ----------
        data : List[Dict[str, Any]]
            List of intervals containing load profile data.

        Returns
        -------
        List[Dict[str, Any]]
            Transformed load profile data.
        """
        if not isinstance(data, list):
            logger.error("Invalid data format: expected list of intervals")
            raise ValueError("Invalid data format: expected list of intervals")

        # Validate that each interval contains the required fields
        for interval in data:
            if not all(
                key in interval for key in ["dtstart", "duration", "signal_payload"]
            ):
                logger.error("Incomplete interval data: missing required fields")
                raise ValueError("Incomplete interval data: missing required fields")

        transformed_data = [
            {
                "dstart": int(interval["dtstart"].timestamp() * 1000),
                "duration": int(interval["duration"].total_seconds() * 1000),
                "signal_payload": interval["signal_payload"],
            }
            for interval in data
        ]

        return transformed_data

    def _get_current_data(
        self, current_timestamp: int
    ) -> tuple[Optional[dict], Optional[list]]:
        """Get current allowed consumption and consumption points."""
        current_allowed_consumption = self._load_profile_manager.get_closest_point(
            current_timestamp
        )
        current_consumption = self._load_profile_manager.get_closest_consumption_points(
            current_timestamp
        )
        return current_allowed_consumption, current_consumption

    def _prepare_consumption_array(
        self, current_consumption: List[Dict]
    ) -> tuple[np.ndarray, np.ndarray]:
        """Convert consumption data into NumPy arrays for values and VEN IDs."""
        if not current_consumption:
            return np.array([]), np.array([])

        # Extract VEN IDs and values into separate arrays
        ven_ids = np.array([item["ven_id"] for item in current_consumption])
        values = np.array(
            [item["value"] for item in current_consumption], dtype=np.float64
        )

        # Sum values for each unique VEN ID
        unique_vens, indices = np.unique(ven_ids, return_inverse=True)
        summed_values = np.zeros(len(unique_vens))
        np.add.at(summed_values, indices, values)

        return unique_vens, summed_values

    @staticmethod
    def _correction_factor(G_i: np.ndarray) -> np.ndarray:
        """Calculate the correction factor for given G_i values using vectorized operations."""
        return (5 * np.square(G_i)) / 1.5 - (5 * G_i) / 1.5 + 1.085

    def _calculate_z_value(
        self, current_allowed_consumption: Dict, unique_ven_count: int
    ) -> float:
        """Calculate initial Z value if not already set."""
        if self._z is None:
            self._z = current_allowed_consumption["signal_payload"] / unique_ven_count
        return self._z

    def _calculate_load_distribution(
        self, ven_ids: np.ndarray, consumption_values: np.ndarray, total_allowed: float
    ) -> tuple[np.ndarray, np.ndarray]:
        """Calculate load distribution parameters for each VEN using vectorized operations."""
        z = np.full_like(consumption_values, self._z)
        g = np.divide(z, consumption_values, where=consumption_values != 0)
        w = (1 - g) * consumption_values * self._correction_factor(g)
        w_total = np.sum(w)
        z_neu = w / w_total * total_allowed if w_total > 0 else np.zeros_like(w)

        return ven_ids, z_neu

    @staticmethod
    def generate_time_intervals(base_time: datetime) -> List[Dict[str, Any]]:
        """Generate 95 fifteen-minute intervals starting from the base time."""
        base_timestamp = base_time.timestamp() * 1000
        intervals = np.arange(95) * 15 * 60 * 1000  # 15 minutes in milliseconds

        return [
            {
                "dstart": int(base_timestamp + interval),
                "duration": 900000,  # 15 minutes in milliseconds
                "signal_payload": 0,
            }
            for interval in intervals
        ]

    def _create_ven_profiles(
        self, ven_ids: np.ndarray, z_neu: np.ndarray, intervals: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """Create load profiles for each VEN based on calculated z_neu values."""
        return {
            str(ven_id): [
                {**interval, "signal_payload": z_value} for interval in intervals
            ]
            for ven_id, z_value in zip(ven_ids, z_neu)
        }

    def update_load_profile(self, sender: str, data: List[Dict[str, Any]]) -> None:
        """Update the load profile with the provided data."""
        transformed_data = (
            self.process_load_profile_data(data)
            if not all(
                "dstart" in interval
                and "duration" in interval
                and "signal_payload" in interval
                for interval in data
            )
            else data
        )

        current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        current_allowed_consumption, current_consumption = self._get_current_data(
            current_timestamp
        )

        new_data_structure = {}
        if current_allowed_consumption and current_consumption:
            try:
                # Prepare consumption data using NumPy
                ven_ids, consumption_values = self._prepare_consumption_array(
                    current_consumption
                )

                if len(ven_ids) > 0:
                    # Calculate initial Z value if needed
                    self._z = self._calculate_z_value(
                        current_allowed_consumption, len(ven_ids)
                    )

                    # Calculate load distribution using NumPy operations
                    ven_ids, z_neu = self._calculate_load_distribution(
                        ven_ids,
                        consumption_values,
                        current_allowed_consumption["signal_payload"],
                    )

                    # Generate time intervals and create VEN profiles
                    intervals = self.generate_time_intervals(datetime.now(timezone.utc))
                    new_data_structure = self._create_ven_profiles(
                        ven_ids, z_neu, intervals
                    )

            except Exception as e:
                logger.error(f"Error calculating load distribution: {e}")
                raise

        # Update database and dispatch signal
        self._load_profile_manager.insert_load_profile(transformed_data)
        dispatcher.send(
            sender="nm", signal="update_load_profile", data=new_data_structure
        )

    def update_consumption_data(self, sender: str, data: ResourceConsumption) -> None:
        """
        Update the consumption data with the provided ResourceConsumption data.

        Parameters
        ----------
        sender : str
            The sender of the data.
        data : ResourceConsumption
            Resource consumption data.
        """
        try:
            with self._lock:
                self._current_consumption = 0.0
                ven_data = self._ven_data.setdefault(data.ven_id, {})
                ven_data[data.resource_id] = data.data[1]

                self._current_consumption = sum(
                    value
                    for resources in self._ven_data.values()
                    for value in resources.values()
                )

                timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
                consumption_data = {
                    "timestamp": timestamp_ms,
                    "ven_id": data.ven_id,
                    "resource_id": data.resource_id,
                    "value": data.data[1],
                }
                self._load_profile_manager.insert_consumption(consumption_data)

                logger.debug(
                    f"Updated consumption data - Total: {self._current_consumption}"
                )
                dispatcher.send(
                    sender="nm",
                    signal="update_consumption_data",
                    data=self._current_consumption,
                )
        except (AttributeError, IndexError) as e:
            logger.error(
                f"Error processing consumption data from sender {sender} with data {data}: {e}"
            )
            raise
