import json
import os


class Config:
    _instance = None  # Class-level variable to hold the singleton instance
    CONFIG_FILE = "config.json"  # The file where the config will be saved

    def __new__(cls):
        if cls._instance is None:
            # Create a new instance if one doesn't exist
            cls._instance = super(Config, cls).__new__(cls)
            # Load the configuration from a file, if available
            cls._instance.load_config()
        return cls._instance

    def __init__(self):
        """Ensure __init__ only runs once (after loading config)"""
        if not hasattr(self, "initialized"):
            # If the instance is newly created or reset
            self.initialized = True

    def load_config(self):
        """Load configuration from a JSON file if it exists"""
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as file:
                config_data = json.load(file)
                self.DATABASE_URL = config_data.get("DATABASE_URL", "localhost:5432")
                self.API_KEY = config_data.get("API_KEY", "your-api-key")
                self.DEBUG_MODE = config_data.get("DEBUG_MODE", True)
                print("Configuration loaded from file.")
        else:
            # If no config file, set default values
            self.DATABASE_URL = "localhost:5432"
            self.API_KEY = "your-api-key"
            self.DEBUG_MODE = True
            print("Default configuration loaded.")

    def save_config(self):
        """Save the current configuration to a JSON file"""
        config_data = {
            "DATABASE_URL": self.DATABASE_URL,
            "API_KEY": self.API_KEY,
            "DEBUG_MODE": self.DEBUG_MODE,
        }
        with open(self.CONFIG_FILE, "w") as file:
            json.dump(config_data, file, indent=4)
        print("Configuration saved to file.")

    def update_config(self, database_url=None, api_key=None, debug_mode=None):
        """Update config values dynamically and save them"""
        if database_url:
            self.DATABASE_URL = database_url
        if api_key:
            self.API_KEY = api_key
        if debug_mode is not None:
            self.DEBUG_MODE = debug_mode

        # Automatically save the updated configuration
        self.save_config()

    def show_config(self):
        """Display the current config values"""
        print(f"Database URL: {self.DATABASE_URL}")
        print(f"API Key: {self.API_KEY}")
        print(f"Debug Mode: {self.DEBUG_MODE}")


# Test example to demonstrate Singleton behavior with save/load functionality
if __name__ == "__main__":
    # First instance
    config1 = Config()
    config1.show_config()

    # Modify config and save it to file
    config1.update_config(database_url="localhost:5433", api_key="new-api-key")

    # Second instance should load from file, reflecting changes
    config2 = Config()
    config2.show_config()

    # Verify both are the same instance
    print(f"config1 is config2: {config1 is config2}")
