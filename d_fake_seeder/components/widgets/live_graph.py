"""
LiveGraph - Real-time line graph widget using Cairo.

Provides System Monitor-style live graphs for metrics visualization.
"""

# isort: skip_file

# fmt: off
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from d_fake_seeder.lib.logger import logger  # noqa: E402

# fmt: on


class LiveGraph(Gtk.DrawingArea):
    """
    Real-time line graph widget using Cairo for rendering.

    Features:
    - Multiple data series with different colors
    - Auto-scaling or fixed range
    - Grid lines
    - Smooth line drawing
    - Efficient ring buffer for data points
    """

    def __init__(
        self,
        max_samples=60,
        min_value=0.0,
        max_value=100.0,
        auto_scale=False,
        show_grid=True,
        grid_lines=5,
    ):
        """
        Initialize LiveGraph.

        Args:
            max_samples: Maximum number of data points to display
            min_value: Minimum Y-axis value (if not auto-scaling)
            max_value: Maximum Y-axis value (if not auto-scaling)
            auto_scale: Whether to auto-scale Y-axis based on data
            show_grid: Whether to show grid lines
            grid_lines: Number of horizontal grid lines
        """
        super().__init__()
        logger.debug(
            "Initializing LiveGraph widget",
            extra={"class_name": self.__class__.__name__},
        )

        self.max_samples = max_samples
        self.min_value = min_value
        self.max_value = max_value
        self.auto_scale = auto_scale
        self.show_grid = show_grid
        self.grid_lines = grid_lines

        # Data series: {name: {'data': [], 'color': (r,g,b), 'visible': bool}}
        self.series = {}

        # Set up drawing callback
        self.set_draw_func(self._on_draw)

        # Set minimum size
        self.set_size_request(200, 80)

        # Set background color
        self.set_css_classes(["live-graph"])

        logger.debug(
            "LiveGraph widget initialized successfully",
            extra={"class_name": self.__class__.__name__},
        )

    def add_series(self, name, color=(0.2, 0.8, 0.2), visible=True):
        """
        Add a new data series.

        Args:
            name: Series identifier
            color: RGB tuple (values 0-1)
            visible: Whether series is visible
        """
        self.series[name] = {
            "data": [],
            "color": color,
            "visible": visible,
        }
        logger.debug(
            f"Added series '{name}' with color {color}",
            extra={"class_name": self.__class__.__name__},
        )

    def update_series(self, name, value):
        """
        Add a data point to a series.

        Args:
            name: Series identifier
            value: Data value to add
        """
        if name not in self.series:
            logger.warning(
                f"Attempted to update non-existent series '{name}'",
                extra={"class_name": self.__class__.__name__},
            )
            return

        # Add data point
        self.series[name]["data"].append(float(value))

        # Trim to max_samples (ring buffer)
        if len(self.series[name]["data"]) > self.max_samples:
            self.series[name]["data"].pop(0)

        # Trigger redraw
        self.queue_draw()

    def set_series_visible(self, name, visible):
        """Toggle series visibility."""
        if name in self.series:
            self.series[name]["visible"] = visible
            self.queue_draw()

    def clear_series(self, name=None):
        """
        Clear data from series.

        Args:
            name: Series to clear (None = all series)
        """
        if name is None:
            # Clear all series
            for series_data in self.series.values():
                series_data["data"].clear()
        elif name in self.series:
            self.series[name]["data"].clear()

        self.queue_draw()

    def _get_value_range(self):
        """Calculate current min/max values from all series."""
        if self.auto_scale:
            all_values = []
            for series_data in self.series.values():
                if series_data["visible"] and series_data["data"]:
                    all_values.extend(series_data["data"])

            if all_values:
                return min(all_values), max(all_values)

        return self.min_value, self.max_value

    def _on_draw(self, area, ctx, width, height):
        """
        Cairo drawing callback.

        Args:
            area: DrawingArea widget
            ctx: Cairo context
            width: Widget width in pixels
            height: Widget height in pixels
        """
        # Clear background (dark gray)
        ctx.set_source_rgb(0.12, 0.12, 0.12)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        # Get value range
        min_val, max_val = self._get_value_range()
        value_range = max_val - min_val
        if value_range == 0:
            value_range = 1  # Avoid division by zero

        # Draw grid lines
        if self.show_grid:
            self._draw_grid(ctx, width, height, min_val, max_val)

        # Draw each series
        for name, series_data in self.series.items():
            if not series_data["visible"]:
                continue

            data = series_data["data"]
            if len(data) < 2:
                continue

            self._draw_series_line(ctx, width, height, data, series_data["color"], min_val, value_range)

    def _draw_grid(self, ctx, width, height, min_val, max_val):
        """Draw horizontal grid lines."""
        ctx.set_source_rgba(0.3, 0.3, 0.3, 0.5)
        ctx.set_line_width(1)

        for i in range(self.grid_lines + 1):
            y = height * (i / self.grid_lines)
            ctx.move_to(0, y)
            ctx.line_to(width, y)

        ctx.stroke()

    def _draw_series_line(self, ctx, width, height, data, color, min_val, value_range):
        """Draw a single data series as a line."""
        ctx.set_source_rgb(*color)
        ctx.set_line_width(2)

        # Calculate x-axis spacing
        x_spacing = width / (self.max_samples - 1) if self.max_samples > 1 else 0

        # Draw line through all points
        for i, value in enumerate(data):
            # Normalize value to 0-1 range
            normalized = (value - min_val) / value_range if value_range > 0 else 0
            normalized = max(0, min(1, normalized))  # Clamp to 0-1

            # Calculate position (invert Y because Cairo Y increases downward)
            x = i * x_spacing
            y = height * (1 - normalized)

            if i == 0:
                ctx.move_to(x, y)
            else:
                ctx.line_to(x, y)

        ctx.stroke()

    def get_series_latest_value(self, name):
        """Get the latest value from a series."""
        if name in self.series and self.series[name]["data"]:
            return self.series[name]["data"][-1]
        return None
