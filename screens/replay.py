import customtkinter as ctk
import tkinter as tk
import pandas as pd
from functools import partial
from datetime import time
import threading 

class DragZoomApp:
    def __init__(self, root : tk.Tk,df : pd.DataFrame):
        self.time_frame = ["m1","m5","m15","m30","h1","h2","h4","1d","1W","1M","6M","1Y","4Y"]
        self.current_tf_index = 0
        self.label_tf_index = self.current_tf_index + 2
        self.df =df
        self.root = root
        self.root.columnconfigure(0, weight=1)  # Expandable column
        self.root.columnconfigure(1, weight=0, minsize=100)  # Fixed width
        self.root.rowconfigure(0, weight=1)  # Expandable row
        self.root.rowconfigure(1, weight=0, minsize=30)  # Fixed height
        self.create_canvas()

        self.root.after(1000,self.init_graph)
        
    def init_graph(self):
        self.create_values()
        self.draw()
        self.binding()

    def create_values(self):
        for i in range(1000):
            self.last_x = None
            self.last_y = None
            self.scale_factor = [1.0,1.0]
            self.scale_label = [1.0,1.0]
            self.min_scale = [0.2,0.5]
            self.max_scale = [4.0,4.0]
            self.price_min = self.df['Low'].min()
            self.price_max = self.df['High'].max()
            self.price_range = self.price_max - self.price_min
            self.canvas_height = self.canvas.winfo_height()
            self.canvas_width = self.canvas.winfo_width()
            height_ratio = 0.9
            self.height_price = self.canvas_height * height_ratio
            self.price_height_ratio = self.price_range / self.height_price
            self.margin = 50
            self.graph_param = (self.price_min, self.price_height_ratio, height_ratio, self.canvas_height)
            self.candle_width = 10
            self.candle_space_between = 15
            self.x_center = self.canvas_width - self.margin
            self.x_first = self.x_center  

    def create_canvas(self):
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas_price = tk.Canvas(self.root, bg="white", width=100)
        self.canvas_date = tk.Canvas(self.root, bg="white", height=30)
        self.Button = tk.Canvas(self.root, bg="white", width=100, height=30)

        # Place them in the grid
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas_price.grid(row=0, column=1, sticky="ns")
        self.canvas_date.grid(row=1, column=0, sticky="ew")
        self.Button.grid(row=1, column=1)

    def binding(self):
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
        visible = self.df.iloc[::1].reset_index(drop=True)  # Inverse l'ordre des bougies
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
        self.canvas_date.delete("all")
        label = self.time_frame[self.label_tf_index]
        units, how_many = self.get_time_units(label)

        x_center = self.canvas_width + (self.x_first - self.canvas_width) * self.scale_factor[0]
        for _, row in self.df.iloc[::-1].iterrows():
            time_obj = row["Time"]
  
            if isinstance(time_obj, time):
                if units == "m" and time_obj.minute % how_many == 0:
                    time_label = time_obj.strftime("%H:%M")
                    self.canvas_date.create_text(x_center, 15, text=time_label, fill="black", anchor="n", font=("Arial", 10))
                if units == "h" and time_obj.hour % how_many == 0 and time_obj.minute == 0:
                    time_label = time_obj.strftime("%H:%M")
                    self.canvas_date.create_text(x_center, 15, text=time_label, fill="black", anchor="n", font=("Arial", 10))

            x_center -= self.candle_space_between * self.scale_factor[0]

    def get_time_units(self, label):
        for i in ["m", "h", "d", "W"]:
            if i in label:
                units = i
                how_many = int(label.replace(i, ""))
                return units, how_many

    def draw_price_label(self):
        """Dessine l'étiquette de prix sur le canvas Tkinter."""
        self.canvas_price.delete("all")
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
        
        d = d/self.scale_label[1]

        pricecenter = (((self.df["Low"].min()+self.price_range/2)*echelle)//d)*d/echelle
        d = d/echelle
        n = 7
        for i in range(n*2):
            price = pricecenter - (i-n)*d
            self.canvas_price.create_text(15,self.get_y_value(price), text=f"{price:.2f}", fill="black", anchor="w", font=("Arial", 10))

    def get_y_value(self, price: float) -> float:
        """Convertit un prix en une position Y sur le canvas avec un zoom sur Y."""
        price_min, price_height_ratio, height_ratio, height_canvas= self.graph_param  # Ajout du zoom_y
        coord_price = (price - price_min)
        rendering_height = height_ratio*height_canvas

        # Appliquer le zoom sur l'échelle des prix
        y_SE = (coord_price / price_height_ratio)

        # on aplique une homotethie pour prendre en compte le changement de la position de l'axe par rapport au centre de scale
        y_SE = rendering_height/2 - self.scale_factor[1]*(y_SE - rendering_height/2)

        # Ajustement final pour l'affichage
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
                
                if index == 1 and new_scale > 2*self.scale_label[index]:
                    self.scale_label[index]*=2
                    self.draw_price_label()
                elif index == 1 and new_scale < self.scale_label[index]/2:
                    self.scale_label[index]/=2
                    self.draw_price_label()
                elif index == 0 and new_scale > 2 * self.scale_label[index]:  
                    self.scale_label[index] *= 2  
                    self.label_tf_index -=1
                    self.draw_time_labels()  # Redessiner les labels de dates

                elif index == 0 and new_scale < self.scale_label[index] / 2:  
                    self.scale_label[index] /= 2  
                    self.label_tf_index +=1
                    self.draw_time_labels()  # Redessiner les labels de dates

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
        

df = pd.read_excel("./data/historique/donne.xlsx")
df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.time

class ReplayScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.place_toolbar()
        self.place_work_frame()
        self.place_graphic()

    def place_toolbar(self):
        self.toolbar_frame = ctk.CTkFrame(self,height=50,fg_color="#ffffff",border_color="#000000",border_width=1,corner_radius=0)
        self.toolbar_frame.pack(fill="x")

        self.body_frame = ctk.CTkFrame(self,fg_color="#ffffff",border_color="#000000",border_width=1,corner_radius=0)
        self.body_frame.pack(fill="both",expand=True)

    def place_work_frame(self):
        self.object_left = ctk.CTkFrame(self.body_frame,width=50,fg_color="#ffffff",border_color="#000000",border_width=1,corner_radius=0)
        self.object_left.pack(side="left",fill="y")

        self.graphic_container = ctk.CTkFrame(self.body_frame,fg_color="#ffffff",border_color="#000000",border_width=1,corner_radius=0)
        self.graphic_container.pack(side="left",fill="both",expand=True)

        self.object_right = ctk.CTkFrame(self.body_frame,width=50,fg_color="#ffffff",border_color="#000000",border_width=1,corner_radius=0)
        self.object_right.pack(side="left",fill="y")

    def place_graphic(self):
        self.graphic_frame = ctk.CTkFrame(self.graphic_container,fg_color="#ffffff",border_color="#000000",border_width=1,corner_radius=0)
        self.graphic_frame.pack(side="top",fill="both",expand=True)

        self.view = DragZoomApp(self.graphic_frame,df=df)       

        self.graphic_frame_bar = ctk.CTkFrame(self.graphic_container,height=50,fg_color="#ffffff",border_color="#000000",border_width=1,corner_radius=0)
        self.graphic_frame_bar.pack(side="top",fill="x")


# window = ctk.CTk()
# window.geometry("800x600")
# app = DragZoomApp(window,df)
# app.pack(expand=True,fill="both")
# window.mainloop()