"""
Application initialization helpers for DFakeSeeder.

This module provides utilities for application startup and environment
configuration that should be done before GTK initialization.
"""

# fmt: off
import os

from d_fake_seeder.lib.logger import logger

# fmt: on


class AppInitializationHelper:
    """Helper class for application initialization and environment setup."""

    @classmethod
    def initialize_application_settings(cls) -> None:
        """
        Initialize application settings and configuration.

        This method ensures that the application settings are properly
        loaded and initialized before other components start using them.
        """
        try:
            from domain.app_settings import AppSettings

            # Initialize settings singleton
            AppSettings.get_instance()

            logger.debug("Application settings initialized")

        except Exception as e:
            logger.error(f"Error initializing application settings: {e}")

    @classmethod
    def setup_resource_paths(cls) -> None:
        """
        Set up resource paths for the application.

        This method configures the DFS_PATH environment variable and other
        resource path configurations needed by the application.
        """
        try:
            import importlib.util

            # Set DFS_PATH if not already set
            if "DFS_PATH" not in os.environ:
                # Find the package root directory
                spec = importlib.util.find_spec("d_fake_seeder")
                if spec and spec.origin:
                    package_root = os.path.dirname(spec.origin)
                    os.environ["DFS_PATH"] = package_root
                    logger.debug(f"DFS_PATH set to: {package_root}")
                else:
                    # Fallback: use the directory containing this file
                    current_file = os.path.abspath(__file__)
                    # Go up from lib/util/app_initialization.py to the package root
                    package_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
                    os.environ["DFS_PATH"] = package_root
                    logger.debug(f"DFS_PATH set to fallback path: {package_root}")

        except Exception as e:
            logger.error(f"Error setting up resource paths: {e}")

    @classmethod
    def perform_full_initialization(cls) -> None:
        """
        Perform complete application initialization.

        This is a convenience method that performs all necessary initialization
        steps in the correct order.
        """
        try:
            # Initialize settings first
            cls.initialize_application_settings()

            # Set up resource paths
            cls.setup_resource_paths()

            logger.info("Full application initialization completed")

        except Exception as e:
            logger.error(f"Error during full application initialization: {e}")
