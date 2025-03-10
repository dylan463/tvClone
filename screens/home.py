import customtkinter as ctk

class HomeScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ctk.CTkLabel(self, text="Écran d'Accueil", font=("Arial", 18))
        label.pack(pady=20)

        # Bouton pour accéder aux Paramètres
        btn_settings = ctk.CTkButton(self, text="Paramètres", command=lambda: controller.show_frame("SettingsScreen"))
        btn_settings.pack(pady=10)

        # Bouton pour accéder au Profil
        btn_profile = ctk.CTkButton(self, text="Profil", command=lambda: controller.show_frame("ProfileScreen"))
        btn_profile.pack(pady=10)

        # Bouton pour accéder au Replay
        btn_replay = ctk.CTkButton(self, text="Replay", command=lambda: controller.show_frame("ReplayScreen"))
        btn_replay.pack(pady=10)
