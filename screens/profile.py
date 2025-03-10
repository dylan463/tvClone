import customtkinter as ctk

class ProfileScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ctk.CTkLabel(self, text="Écran Profil", font=("Arial", 18))
        label.pack(pady=20)

        btn_home = ctk.CTkButton(self, text="Retour Accueil", command=lambda: controller.show_frame("HomeScreen"))
        btn_home.pack(pady=10)
