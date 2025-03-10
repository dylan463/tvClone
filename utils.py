import tkinter as tk
from functools import partial
from datetime import datetime, time
import pandas as pd
from typing import List, Tuple, Union, Optional, Dict, Any


class DragZoomApp:
    """
    A financial chart application with candlestick visualization and interactive
    zoom/pan capabilities.
    """
    
    def __init__(self, root: tk.Tk, df: pd.DataFrame):
        """
        Initialize the DragZoomApp with the root window and financial data.
        
        Args:
            root: The Tkinter root window
            df: DataFrame containing financial data with columns Time, Open, High, Low, Close
        """
        # Time frame settings
        self.time_frames = ["m1", "m5", "m15", "m30", "h1", "h2", "h4", "1d", "1W", "1M", "6M", "1Y", "4Y"]
        self.current_tf_index = 0
        self.label_tf_index = self.current_tf_index + 2
        
        # Data and UI elements
        self.df = df
        self.root = root
        
        # Configure root window layout
        self._configure_layout()
        self._create_ui_components()
        
        # Initialize state variables
        self.drag_state = {
            'last_x': None,
            'last_y': None
        }
        
        # Initialize zoom settings
        self.zoom_settings = {
            'scale_factor': [1.0, 1.0],
            'scale_label': [1.0, 1.0],
            'min_scale': [0.2, 0.5],
            'max_scale': [4.0, 4.0]
        }
        
        # Schedule initialization after UI is fully rendered
        self.root.after(100, self.initialize_chart)
    
    def _configure_layout(self) -> None:
        """Configure the grid layout for the application."""
        self.root.columnconfigure(0, weight=1)  # Expandable column for chart
        self.root.columnconfigure(1, weight=0, minsize=100)  # Fixed width for price labels
        self.root.rowconfigure(0, weight=1)  # Expandable row for chart
        self.root.rowconfigure(1, weight=0, minsize=30)  # Fixed height for time labels
    
    def _create_ui_components(self) -> None:
        """Create and arrange the UI components."""
        # Create canvas elements
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas_price = tk.Canvas(self.root, bg="white", width=100)
        self.canvas_date = tk.Canvas(self.root, bg="white", height=30)
        self.button_panel = tk.Canvas(self.root, bg="white", width=100, height=30)

        # Place them in the grid
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas_price.grid(row=0, column=1, sticky="ns")
        self.canvas_date.grid(row=1, column=0, sticky="ew")
        self.button_panel.grid(row=1, column=1)
    
    def initialize_chart(self) -> None:
        """Initialize the chart after the UI is fully rendered."""
        self._calculate_chart_parameters()
        self._setup_event_bindings()
        self.draw_chart()
    
    def _calculate_chart_parameters(self) -> None:
        """Calculate chart parameters based on data and canvas dimensions."""
        # Price range parameters
        self.price_min = self.df['Low'].min()
        self.price_max = self.df['High'].max()
        self.price_range = self.price_max - self.price_min
        
        # Canvas dimensions
        self.canvas_height = self.canvas.winfo_height()
        self.canvas_width = self.canvas.winfo_width()
        
        # Chart drawing parameters
        self.height_ratio = 0.9  # Percentage of canvas height used for chart
        self.height_price = self.canvas_height * self.height_ratio
        self.price_height_ratio = self.price_range / self.height_price
        self.margin = 50
        
        # Candlestick parameters
        self.candle_width = 10
        self.candle_space_between = 15
        
        # Calculate initial positions
        self.x_center = self.canvas_width - self.margin
        self.x_first = self.x_center
        
        # Store parameters used for drawing
        self.graph_params = {
            'price_min': self.price_min,
            'price_height_ratio': self.price_height_ratio,
            'height_ratio': self.height_ratio,
            'canvas_height': self.canvas_height
        }
    
    def _setup_event_bindings(self) -> None:
        """Set up mouse event bindings for interaction."""
        # Date canvas bindings (horizontal zoom)
        self.canvas_date.bind("<ButtonPress-1>", partial(self.start_drag, axis="x"))
        self.canvas_date.bind("<B1-Motion>", partial(self.drag_to_zoom, axis="x"))
        self.canvas_date.bind("<ButtonRelease-1>", partial(self.stop_drag, axis="x"))

        # Price canvas bindings (vertical zoom)
        self.canvas_price.bind("<ButtonPress-1>", partial(self.start_drag, axis="y"))
        self.canvas_price.bind("<B1-Motion>", partial(self.drag_to_zoom, axis="y"))
        self.canvas_price.bind("<ButtonRelease-1>", partial(self.stop_drag, axis="y"))

        # Main canvas bindings (panning)
        self.canvas.bind("<ButtonPress-1>", partial(self.start_drag, axis="canvas"))
        self.canvas.bind("<B1-Motion>", partial(self.drag_to_pan, axis="canvas"))
        self.canvas.bind("<ButtonRelease-1>", partial(self.stop_drag, axis="canvas"))
        
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self.mouse_wheel_zoom)
    
    def draw_chart(self) -> None:
        """Draw all chart components."""
        self.draw_candlesticks()
        self.draw_time_labels()
        self.draw_price_labels()
        self.draw_grid()
    
    def draw_candlesticks(self) -> None:
        """
        Draw candlestick chart on the main canvas.
        Only renders visible candlesticks for performance.
        """
        self.canvas.delete("candlesticks")
        
        # Calculate visible range
        visible_width = self.canvas_width / self.zoom_settings['scale_factor'][0]
        visible_count = int(visible_width / self.candle_space_between) + 2
        visible_start = max(0, len(self.df) - int((self.x_first - self.x_center) / self.candle_space_between))
        visible_end = min(len(self.df), visible_start + visible_count)
        
        # Get only visible data
        visible_data = self.df.iloc[visible_start:visible_end].iloc[::-1]
        x_pos = self.x_center
        
        for idx, (_, row) in enumerate(visible_data.iterrows()):
            # Determine candle color
            color = "green" if row["Close"] >= row["Open"] else "red"
            
            # Calculate y-coordinates
            high_y = self._calculate_y_position(row["High"])
            low_y = self._calculate_y_position(row["Low"])
            open_y = self._calculate_y_position(row["Open"])
            close_y = self._calculate_y_position(row["Close"])
            
            # Draw candlestick wick
            self.canvas.create_line(
                x_pos, high_y, x_pos, low_y, 
                fill=color, 
                tags=("candlesticks", f"candle-{idx}")
            )
            
            # Draw candlestick body
            self.canvas.create_rectangle(
                x_pos - self.candle_width / 2, open_y, 
                x_pos + self.candle_width / 2, close_y, 
                fill=color, outline=color, 
                tags=("candlesticks", f"candle-{idx}")
            )
            
            # Move to next position
            x_pos -= self.candle_space_between
    
    def draw_time_labels(self) -> None:
        """
        Draw time labels on the date canvas.
        Adjusts density and format based on the current time frame and zoom level.
        """
        self.canvas_date.delete("all")
        
        # Get current time frame parameters
        current_tf = self.time_frames[self.label_tf_index]
        units, interval = self._parse_time_frame(current_tf)
        
        # Calculate label spacing based on zoom
        label_density = self._calculate_label_density()
        
        # Starting position
        x_pos = self.canvas_width + (self.x_first - self.canvas_width) * self.zoom_settings['scale_factor'][0]
        drawn_positions = set()
        
        # Draw time labels
        for idx, (_, row) in enumerate(self.df.iloc[::-1].iterrows()):
            time_value = row["Time"]
            
            # Skip some labels based on density
            if idx % label_density != 0:
                x_pos -= self.candle_space_between * self.zoom_settings['scale_factor'][0]
                continue
            
            # Prevent label overlap
            rounded_pos = round(x_pos / 10) * 10
            if rounded_pos in drawn_positions and abs(x_pos - rounded_pos) < 30:
                x_pos -= self.candle_space_between * self.zoom_settings['scale_factor'][0]
                continue
            
            # Check if this time point should have a label
            if self._should_draw_time_label(time_value, units, interval):
                time_label = self._format_time_label(time_value, units)
                
                # Only draw if within canvas boundaries
                if 0 <= x_pos <= self.canvas_width:
                    self.canvas_date.create_text(
                        x_pos, 15, 
                        text=time_label, 
                        fill="black", 
                        anchor="n", 
                        font=("Arial", 10)
                    )
                    drawn_positions.add(rounded_pos)
            
            x_pos -= self.candle_space_between * self.zoom_settings['scale_factor'][0]
    
    def _calculate_label_density(self) -> int:
        """Calculate the density of time labels based on current zoom level."""
        zoom = self.zoom_settings['scale_factor'][0]
        if zoom < 0.5:
            return 5  # Show fewer labels when zoomed out
        elif zoom > 2.0:
            return 1  # Show more labels when zoomed in
        else:
            return 3  # Default density
    
    def _parse_time_frame(self, time_frame: str) -> Tuple[str, int]:
        """
        Parse a time frame string into units and interval.
        
        Args:
            time_frame: Time frame string (e.g., "m5", "h1", "1d")
            
        Returns:
            Tuple of (unit, interval)
        """
        for unit in ["m", "h", "d", "W", "M", "Y"]:
            if unit in time_frame:
                try:
                    interval = int(time_frame.replace(unit, ""))
                    return unit, interval
                except ValueError:
                    # Handle special cases like "1d", "1W"
                    if time_frame.startswith("1") and unit in ["d", "W", "M", "Y"]:
                        return unit, 1
                    elif time_frame.startswith("6M"):
                        return "M", 6
                    else:
                        return "m", 1  # Default to minutes
        return "m", 1  # Default
    
    def _should_draw_time_label(self, time_value: Union[datetime, time], units: str, interval: int) -> bool:
        """
        Determine if a time label should be drawn based on time frame and interval.
        
        Args:
            time_value: The time value to check
            units: Time unit (m, h, d, W, M, Y)
            interval: Interval value
            
        Returns:
            True if label should be drawn, False otherwise
        """
        if not isinstance(time_value, (datetime, time)):
            return False
            
        if isinstance(time_value, datetime):
            if units == "m":
                return time_value.minute % interval == 0
            elif units == "h":
                return time_value.hour % interval == 0 and time_value.minute == 0
            elif units == "d":
                return time_value.day % interval == 0
            elif units == "W":
                return time_value.weekday() == 0  # Monday
            elif units == "M":
                return time_value.day == 1  # First day of month
            elif units == "Y":
                return time_value.month == 1 and time_value.day == 1  # First day of year
        else:  # time object
            if units == "m":
                return time_value.minute % interval == 0
            elif units == "h":
                return time_value.hour % interval == 0 and time_value.minute == 0
        
        return False
    
    def _format_time_label(self, time_value: Union[datetime, time], units: str) -> str:
        """
        Format time value based on time frame.
        
        Args:
            time_value: The time value to format
            units: Time unit (m, h, d, W, M, Y)
            
        Returns:
            Formatted time string
        """
        if not isinstance(time_value, (datetime, time)):
            return ""
            
        if isinstance(time_value, datetime):
            if units in ["m", "h"]:
                return time_value.strftime("%H:%M")
            elif units == "d":
                return time_value.strftime("%d-%m")
            elif units == "W":
                return time_value.strftime("%d-%m")
            elif units == "M":
                return time_value.strftime("%b %Y")
            else:  # Year
                return time_value.strftime("%Y")
        else:  # time object
            return time_value.strftime("%H:%M")
    
    def draw_price_labels(self) -> None:
        """
        Draw price labels on the price canvas.
        Adjusts spacing and precision based on price range and zoom level.
        """
        self.canvas_price.delete("all")
        
        # Determine appropriate price increment based on data range
        price_increment = self._calculate_price_increment()
        
        # Calculate center price and adjust for zoom
        center_price = (self.price_min + self.price_range / 2)
        price_increment = price_increment / self.zoom_settings['scale_label'][1]
        
        # Number of price levels to display
        levels = 7
        
        # Draw price labels
        for i in range(-levels, levels + 1):
            price = center_price + i * price_increment
            if self.price_min <= price <= self.price_max:
                y_pos = self._calculate_y_position(price)
                
                # Format price with appropriate precision
                price_text = f"{price:.2f}" if price < 1000 else f"{price:.0f}"
                
                self.canvas_price.create_text(
                    15, y_pos, 
                    text=price_text, 
                    fill="black", 
                    anchor="w", 
                    font=("Arial", 10)
                )
    
    def _calculate_price_increment(self) -> float:
        """Calculate appropriate price increment based on data range."""
        # Get average price movement
        avg_movement = (self.df['High'] - self.df['Low']).mean()
        
        # Scale factor to normalize
        scale = 1
        while avg_movement < 10:
            scale *= 10
            avg_movement *= 10
        
        # Round to appropriate increment
        if avg_movement <= 50:
            increment = 50
        else:
            increment = 100
            
        return increment / scale
    
    def draw_grid(self) -> None:
        """Draw grid lines on the main canvas for better readability."""
        self.canvas.delete("grid")
        
        # Draw horizontal grid lines at price label positions
        price_increment = self._calculate_price_increment() / self.zoom_settings['scale_label'][1]
        center_price = (self.price_min + self.price_range / 2)
        levels = 7
        
        for i in range(-levels, levels + 1):
            price = center_price + i * price_increment
            if self.price_min <= price <= self.price_max:
                y_pos = self._calculate_y_position(price)
                
                self.canvas.create_line(
                    0, y_pos, self.canvas_width, y_pos,
                    fill="#EEEEEE", 
                    dash=(2, 4),
                    tags="grid"
                )
        
        # Draw vertical grid lines at significant time points
        x_pos = self.x_center
        current_tf = self.time_frames[self.label_tf_index]
        units, interval = self._parse_time_frame(current_tf)
        
        for _, row in self.df.iloc[::-1].iterrows():
            time_value = row["Time"]
            
            if self._should_draw_time_label(time_value, units, interval):
                self.canvas.create_line(
                    x_pos, 0, x_pos, self.canvas_height,
                    fill="#EEEEEE", 
                    dash=(2, 4),
                    tags="grid"
                )
                
            x_pos -= self.candle_space_between * self.zoom_settings['scale_factor'][0]
    
    def _calculate_y_position(self, price: float) -> float:
        """
        Convert a price value to y-coordinate on the canvas.
        
        Args:
            price: Price value to convert
            
        Returns:
            Y-coordinate position
        """
        # Extract parameters
        price_min = self.graph_params['price_min']
        price_height_ratio = self.graph_params['price_height_ratio']
        height_ratio = self.graph_params['height_ratio']
        canvas_height = self.graph_params['canvas_height']
        
        # Calculate rendering height
        rendering_height = height_ratio * canvas_height
        
        # Calculate base coordinate
        price_offset = (price - price_min)
        base_y = price_offset / price_height_ratio
        
        # Apply zoom transformation
        zoom_factor = self.zoom_settings['scale_factor'][1]
        midpoint = rendering_height / 2
        zoomed_y = midpoint - zoom_factor * (base_y - midpoint)
        
        # Final adjustment for display
        y_position = canvas_height - zoomed_y - (1 - height_ratio) * canvas_height / 2
        
        return y_position
    
    def start_drag(self, event: tk.Event, axis: str) -> None:
        """
        Start drag operation.
        
        Args:
            event: Tkinter event
            axis: Drag axis ('x', 'y', or 'canvas')
        """
        if axis in ["x", "canvas"]:
            self.drag_state['last_x'] = event.x
        
        if axis in ["y", "canvas"]:
            self.drag_state['last_y'] = event.y
    
    def drag_to_zoom(self, event: tk.Event, axis: str) -> None:
        """
        Handle drag events for zooming.
        
        Args:
            event: Tkinter event
            axis: Zoom axis ('x' or 'y')
        """
        # Determine which axis to use
        if axis == "x":
            last_pos = self.drag_state['last_x']
            current_pos = event.x
            axis_index = 0
        else:  # y-axis
            last_pos = self.drag_state['last_y']
            current_pos = event.y
            axis_index = 1
        
        if last_pos is not None:
            # Calculate drag delta
            delta = current_pos - last_pos
            
            if delta != 0:
                # Calculate new scale based on drag direction
                zoom_direction = 1.02 if delta > 0 else 0.98
                new_scale = self.zoom_settings['scale_factor'][axis_index] * zoom_direction
                
                # Apply limits
                min_scale = self.zoom_settings['min_scale'][axis_index]
                max_scale = self.zoom_settings['max_scale'][axis_index]
                new_scale = max(min_scale, min(new_scale, max_scale))
                
                # Prepare scale parameters
                width = self.canvas.winfo_width()
                height = self.canvas.winfo_height()
                scale_change = new_scale / self.zoom_settings['scale_factor'][axis_index]
                
                # Create scale parameters based on axis
                if axis == "y":
                    scale_params = (width, height/2, 1, scale_change)
                else:  # x-axis
                    scale_params = (width, height/2, scale_change, 1)
                
                # Check if we need to update label scale
                self._update_label_scale(axis_index, new_scale)
                
                # Apply the scaling
                self._apply_scaling(scale_params, axis_index)
                
                # Update scale factor
                self.zoom_settings['scale_factor'][axis_index] = new_scale
            
            # Update last position
            if axis == "x":
                self.drag_state['last_x'] = current_pos
            else:
                self.drag_state['last_y'] = current_pos
    
    def _update_label_scale(self, axis_index: int, new_scale: float) -> None:
        """
        Update label scale and adjust timeframe index if necessary.
        
        Args:
            axis_index: Axis index (0 for x, 1 for y)
            new_scale: New scale value
        """
        current_label_scale = self.zoom_settings['scale_label'][axis_index]
        
        # Check if scale changed significantly
        if axis_index == 1:  # Y-axis (price)
            if new_scale > 2 * current_label_scale:
                self.zoom_settings['scale_label'][axis_index] *= 2
                self.draw_price_labels()
            elif new_scale < current_label_scale / 2:
                self.zoom_settings['scale_label'][axis_index] /= 2
                self.draw_price_labels()
        elif axis_index == 0:  # X-axis (time)
            if new_scale > 2 * current_label_scale:
                self.zoom_settings['scale_label'][axis_index] *= 2
                self.label_tf_index = max(0, self.label_tf_index - 1)
                self.draw_time_labels()
            elif new_scale < current_label_scale / 2:
                self.zoom_settings['scale_label'][axis_index] /= 2
                self.label_tf_index = min(len(self.time_frames) - 1, self.label_tf_index + 1)
                self.draw_time_labels()
    
    def _apply_scaling(self, scale_params: Tuple[float, float, float, float], axis_index: int) -> None:
        """
        Apply scaling to canvas elements.
        
        Args:
            scale_params: (center_x, center_y, scale_x, scale_y)
            axis_index: Axis index (0 for x, 1 for y)
        """
        center_x, center_y, scale_x, scale_y = scale_params
        
        # Scale main canvas
        self.canvas.scale("all", center_x, center_y, scale_x, scale_y)
        
        # Scale auxiliary canvases
        if axis_index == 0:  # X-axis
            self.canvas_date.scale("all", center_x, center_y, scale_x, 1)
        else:  # Y-axis
            self.canvas_price.scale("all", center_x, center_y, 1, scale_y)
    
    def drag_to_pan(self, event: tk.Event, axis: str) -> None:
        """
        Handle drag events for panning.
        
        Args:
            event: Tkinter event
            axis: Pan axis ('canvas')
        """
        if self.drag_state['last_x'] is not None and self.drag_state['last_y'] is not None:
            # Calculate movement delta
            dx = event.x - self.drag_state['last_x']
            dy = event.y - self.drag_state['last_y']
            
            # Move content on all canvases
            self.canvas.move('all', dx, dy)
            self.canvas_date.move('all', dx, 0)
            self.canvas_price.move('all', 0, dy)
            
            # Update last position
            self.drag_state['last_x'] = event.x
            self.drag_state['last_y'] = event.y
    
    def stop_drag(self, event: tk.Event, axis: str) -> None:
        """
        Stop drag operation.
        
        Args:
            event: Tkinter event
            axis: Drag axis
        """
        self.drag_state['last_x'] = None
        self.drag_state['last_y'] = None
    
    def mouse_wheel_zoom(self, event: tk.Event) -> None:
        """
        Handle mouse wheel events for zooming.
        
        Args:
            event: Tkinter event
        """
        # Determine zoom direction
        zoom_in = event.delta > 0
        
        # Apply zoom to both axes
        for axis_index in range(2):
            new_scale = self.zoom_settings['scale_factor'][axis_index]
            
            if zoom_in:
                new_scale *= 1.1
            else:
                new_scale /= 1.1
            
            # Apply limits
            min_scale = self.zoom_settings['min_scale'][axis_index]
            max_scale = self.zoom_settings['max_scale'][axis_index]
            new_scale = max(min_scale, min(new_scale, max_scale))
            
            # Calculate scale change
            scale_change = new_scale / self.zoom_settings['scale_factor'][axis_index]
            
            # Update scale factor
            self.zoom_settings['scale_factor'][axis_index] = new_scale
            
            # Check if we need to update label scale
            self._update_label_scale(axis_index, new_scale)
        
        # Redraw chart
        self.draw_chart()


# Example usage
if __name__ == "__main__":
    df = pd.read_excel("./data/historique/donne.xlsx")
    
    # Create Tkinter app
    root = tk.Tk()
    root.title("Financial Chart")
    root.geometry("1200x800")
    
    app = DragZoomApp(root, df)
    root.mainloop()