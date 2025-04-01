import json
import os
import time
from datetime import datetime
from collections import deque
import threading


class HistoryStorage:
    """
    Store and manage sensor history data
    """

    def __init__(self, config, max_points=1000, save_interval=300):
        """
        Initialize history storage

        Args:
            config: Config instance
            max_points: Maximum number of data points to store in memory
            save_interval: How often to save to disk (seconds)
        """
        self.config = config
        self.max_points = max_points
        self.save_interval = save_interval

        # Data storage
        self.history = {
            "timestamps": deque(maxlen=max_points),
            "ph": deque(maxlen=max_points),
            "orp": deque(maxlen=max_points),
            "ec": deque(maxlen=max_points),
            "water_temperature": deque(maxlen=max_points),
            "air_temperature": deque(maxlen=max_points),
            "humidity": deque(maxlen=max_points),
        }

        # File paths
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.history_file = os.path.join(self.data_dir, "sensor_history.json")

        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Load existing data
        self.load()

        # Set up automatic saving
        self.last_save_time = time.time()
        self.save_lock = threading.Lock()

    def add_data_point(self, sensor_data):
        """
        Add a new data point to history

        Args:
            sensor_data: Dictionary of sensor readings
        """
        # Add timestamp
        timestamp = datetime.now().isoformat()
        self.history["timestamps"].append(timestamp)

        # Add sensor values
        for key in self.history.keys():
            if key != "timestamps":
                self.history[key].append(sensor_data.get(key, None))

        # Check if we should save to disk
        current_time = time.time()
        if current_time - self.last_save_time > self.save_interval:
            self.save()
            self.last_save_time = current_time

    def get_history(self, limit=None):
        """
        Get history data

        Args:
            limit: Maximum number of points to return (newest first)

        Returns:
            dict: History data
        """
        result = {}

        # Convert deques to lists
        for key, values in self.history.items():
            if limit:
                result[key] = list(values)[-limit:]
            else:
                result[key] = list(values)

        return result

    def save(self):
        """Save history to disk"""
        with self.save_lock:
            try:
                # Convert deques to lists for JSON serialization
                data_to_save = {}
                for key, values in self.history.items():
                    data_to_save[key] = list(values)

                with open(self.history_file, "w") as f:
                    json.dump(data_to_save, f)

            except Exception as e:
                print(f"Error saving history data: {e}")

    def load(self):
        """Load history from disk"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    data = json.load(f)

                # Load data into deques
                for key, values in data.items():
                    if key in self.history:
                        self.history[key] = deque(values, maxlen=self.max_points)

        except Exception as e:
            print(f"Error loading history data: {e}")
