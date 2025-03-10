import tkinter as tk

class TimeScale(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, height=50, bg="white")
        self.scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.canvas.pack(fill="both", expand=True, side="top")
        self.scrollbar.pack(fill="x", side="bottom")

        self.start_time = 9  # Start at 09:00
        self.end_time = 9 + 24  # Show 24 hours
        self.scale_factor = 100  # Pixels per hour
        self.zoom_level = 1.0

        self.draw_scale()
        self.bind_events()

    def draw_scale(self):
        self.canvas.delete("all")
        width = (self.end_time - self.start_time) * self.scale_factor
        self.canvas.config(scrollregion=(0, 0, width, 50))

        for hour in range(self.start_time, self.end_time + 1):
            x = (hour - self.start_time) * self.scale_factor
            time_label = f"{hour:02d}:00"
            self.canvas.create_text(x, 25, text=time_label, anchor="w", font=("Arial", 10))

    def zoom(self, event):
        """Zoom in/out on mouse wheel scroll"""
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale_factor = max(20, min(self.scale_factor * factor, 200))  # Limit zoom level
        self.draw_scale()

    def bind_events(self):
        self.canvas.bind("<MouseWheel>", self.zoom)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("TradingView Time Scale")
    scale = TimeScale(root)
    scale.pack(fill="both", expand=True)
    root.mainloop()
