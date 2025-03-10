import customtkinter as ctk
import tkinter as tk
import pandas as pd
from functools import partial
from datetime import time

class DragZoomApp:
    def __init__(self, root : tk.Tk,df : pd.DataFrame):
        self.df =df
        self.root = root
        self.create_canvas()
        self.create_values()
        self.binding()
        self.root.update_idletasks()
        self.root.after(100, self.draw)  # Attendre un peu avant de dessiner les éléments

    def create_values(self):
        self.last_x = None
        self.last_y = None
        self.scale_factor = [1.0,1.0]
        self.min_scale = [0.5,0.5]
        self.max_scale = [2.0,2.0]
        self.price_min = self.df['Low'].min()
        self.price_max = self.df['High'].max()
        self.price_range = self.price_max - self.price_min
        self.canvas_height = int(self.canvas.cget("height"))
        self.canvas_width = int(self.canvas.cget("width"))
        height_ratio = 0.9
        self.height_price = self.canvas_height * height_ratio
        self.price_height_ratio = self.price_range / self.height_price
        self.margin = 50
        self.graph_param = (self.price_min, self.price_height_ratio, height_ratio, self.canvas_height)
        self.candle_width = 10
        self.candle_space_between = 15
        self.x_center = self.canvas_width - self.margin  

    def create_canvas(self):
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(expand=True, fill="both")

        # Canvas vert (barre latérale droite)
        self.canvas_price = tk.Canvas(self.root, bg="white", width=100)
        self.canvas_price.place(x=self.canvas.winfo_width() - 100, y=0)

        # Canvas bleu (barre inférieure horizontale)
        self.canvas_date = tk.Canvas(self.root, bg="white", height=30)
        self.canvas_date.place(y=self.canvas.winfo_height() - 30, x=0)

        # Canvas jaune (coin inférieur droit)
        self.Button = tk.Button(self.root, bg="white", height=30, width=100)
        self.Button.place(x=self.canvas.winfo_width() - 100, y=self.canvas.winfo_height() - 30)

    def binding(self):
        self.root.bind("<Configure>", self.on_change_size)

        self.canvas_date.bind("<ButtonPress-1>", partial(self.start_drag, ax="x"))
        self.canvas_date.bind("<B1-Motion>", partial(self.zoom_on_drag, ax="x"))
        self.canvas_date.bind("<ButtonRelease-1>", partial(self.stop_drag, ax="x"))

        self.canvas_price.bind("<ButtonPress-1>", partial(self.start_drag, ax="y"))
        self.canvas_price.bind("<B1-Motion>", partial(self.zoom_on_drag, ax="y"))
        self.canvas_price.bind("<ButtonRelease-1>", partial(self.stop_drag, ax="y"))

        self.canvas.bind("<ButtonPress-1>", partial(self.start_drag, ax="canvas"))
        self.canvas.bind("<B1-Motion>", partial(self.zoom_on_drag, ax="canvas"))
        self.canvas.bind("<ButtonRelease-1>", partial(self.stop_drag, ax="canvas"))

    def draw(self):
        self.draw_candlesticks()
        self.draw_time_labels()
        self.draw_price_label()

    def draw_candlesticks(self):
        """Affiche les chandeliers dans le canvas Tkinter."""
        visible = self.df.iloc[::-1].reset_index(drop=True)  # Inverse l'ordre des bougies
        self.canvas.delete("all")

        for _, row in visible.iterrows():
            color = "green" if row["Close"] >= row["Open"] else "red"

            high_y = self.get_y_value(row["High"])
            low_y = self.get_y_value(row["Low"])
            open_y = self.get_y_value(row["Open"])
            close_y = self.get_y_value(row["Close"])

            self.canvas.create_line(self.x_center, high_y, self.x_center, low_y, fill=color)
            self.canvas.create_rectangle(self.x_center - self.candle_width / 2, open_y, 
                                self.x_center + self.candle_width / 2, close_y, fill=color, outline=color)

            self.x_center -= self.candle_space_between

    def draw_time_labels(self):
        """Ajoute des graduations de temps toutes les 15 minutes."""
        canvas_width = int(self.canvas_date.cget("width"))
        x_center = canvas_width - self.margin 
        candle_space_between = 15  

        for _, row in self.df.iloc[::-1].iterrows():
            time_obj = row["Time"]

            if isinstance(time_obj, time) and time_obj.minute % 15 == 0:  # Vérifie si c'est bien un objet time
                time_label = time_obj.strftime("%H:%M")  # Formate hh:mm
                self.canvas_date.create_text(x_center, 15, text=time_label,  # Ajuste la position y
                                fill="black", anchor="n", font=("Arial", 10))
        
            x_center -= candle_space_between  

    def draw_price_label(self):
        """Dessine l'étiquette de prix sur le canvas Tkinter."""
        moyenne =  (self.df['High'] - self.df['Low']).mean()

        echelle = 1
        while not moyenne>10:
            echelle*=10
            moyenne*=10
    
        d = 0
        if moyenne <= 50 :
            d = 50
        else:
            d = 100

        pricecenter = (((self.df["Low"].min()+self.price_range/2)*echelle)//d)*d/echelle
        d = d/echelle
        for i in range(8):
            price = pricecenter - (i-4)*d
            self.canvas_price.create_text(15,self.get_y_value(price), text=f"{price:.2f}", fill="black", anchor="w", font=("Arial", 10))

    def get_y_value(self, price: float) -> float:
        """Convertit un prix en une position Y sur le canvas."""
        price_min, price_height_ratio, height_ratio, height_canvas = self.graph_param
        coord_price = price - price_min
        y_SE = coord_price / price_height_ratio
        y_value = height_canvas - y_SE - (1 - height_ratio) * height_canvas / 2
        return y_value

    def start_drag(self, event: tk.Event, ax: str):
        """Démarre le glissement."""
        if ax == "x":
            self.last_x = event.x
        elif ax == "canvas":
            self.last_x = event.x
            self.last_y = event.y
        else:
            self.last_y = event.y

    def zoom_on_drag(self, event: tk.Event, ax: str):
        """Zoom lors du glissement."""
        if ax == "x":
            last_ax = self.last_x
            event_ax = event.x
        elif ax == "canvas":
            if self.last_x is not None and self.last_y is not None:
                dx = (event.x - self.last_x)
                dy = (event.y - self.last_y)
                self.canvas.move('all', dx, dy)
                self.canvas_date.move('all', dx, 0)  # Move all elements on canvas_date in the x-axis
                self.canvas_price.move('all', 0, dy)  # Move all elements on canvas_price in the y-axis
                self.last_x = event.x
                self.last_y = event.y
                return
        else:
            last_ax = self.last_y
            event_ax = event.y

        if last_ax is not None:
            dax = event_ax - last_ax

            if dax != 0:
                index = 0 if ax == "x" else 1
                new_scale = self.scale_factor[index] * (1.02 if dax > 0 else 0.98)
                new_scale = max(self.min_scale[index], min(new_scale, self.max_scale[index]))

                width = self.canvas.winfo_width()
                height = self.canvas.winfo_height()
                scale = (width, height/2, 1, new_scale / self.scale_factor[index]) if ax == "y" else (
                    width, height/2, new_scale / self.scale_factor[index], 1)

                self.canvas.scale("all", scale[0], scale[1], scale[2], scale[3])
                self.canvas_date.scale("all", scale[0], scale[1], scale[2], 1)  # Scale all elements on canvas_date in the x-axis
                self.canvas_price.scale("all", scale[0], scale[1], 1, scale[3])  # Scale all elements on canvas_price in the y-axis
                self.scale_factor[index] = new_scale

        if ax == "x":
            self.last_x = event_ax
        else:
            self.last_y = event_ax

    def stop_drag(self, event, ax):
        """Fin du glissement."""
        self.last_x = None
        self.last_y = None
        
    def on_change_size(self, event):
        """ Ajuste la position et la taille des éléments lors du redimensionnement de la fenêtre """
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Ajuster la taille et la position
        self.canvas_price.config(height=height)
        self.canvas_price.place(x=width - 100, y=0)

        self.canvas_date.config(width=width)  # Ajuste la largeur du canvas bleu
        self.canvas_date.place(y=height - 30, x=0)

        self.Button.place(x=width - 100, y=height - 30)




