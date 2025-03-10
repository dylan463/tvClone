import customtkinter as ctk
from screens.home import HomeScreen
from screens.settings import SettingsScreen
from screens.profile import ProfileScreen
from screens.replay import ReplayScreen

WIDTH = 800
HEIGHT = 600

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre principale
        self.title("Application Multi-écrans")
        self.geometry("800x600")
        self.minsize(WIDTH,HEIGHT)
        self.fullscreen : str = True  # État du plein écran

        # Liaisons clavier pour quitter ou basculer le plein écran
        self.bind("<Escape>", self.exit_fullscreen)  
        self.bind("<F11>", self.toggle_fullscreen)

        # Conteneur principal qui occupe toute la fenêtre
        self.container = ctk.CTkFrame(self)
        self.frame = ctk.CTkFrame(self.container)
        self.frame.pack()
        self.container.pack(expand=True, fill="both")


        # Dictionnaire pour stocker les écrans
        self.frames_class : dict[ctk.CTkFrame] = {}

        # Création et stockage des écrans
        for F in (HomeScreen, SettingsScreen, ProfileScreen, ReplayScreen):
            page_name = F.__name__
            self.frames_class[page_name] = F

        # Afficher l'écran d'accueil par défaut
        self.show_frame('HomeScreen')

    def show_frame(self, page_name : str):
        self.frame.pack_forget()
        self.frame = self.frames_class[page_name](self.container,controller = self)
        self.frame.pack(expand = True,fill = "both")

    def exit_fullscreen(self, event=None):
        """Quitte le mode plein écran."""
        self.attributes('-fullscreen', False)
        self.fullscreen = False

    def toggle_fullscreen(self, event=None):
        """Active/Désactive le mode plein écran."""
        self.fullscreen = not self.fullscreen
        self.attributes('-fullscreen', self.fullscreen)

def main():
    """Point d'entrée principal de l'application."""
    app = MainApp()
    app.mainloop()

if __name__ == "__main__":
    main()
