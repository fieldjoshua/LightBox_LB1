import tkinter as tk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LED Matrix Control")
        self.geometry("800x600")
        self.create_widgets()

    def create_widgets(self):
        # Placeholder for GUI widgets
        self.label = tk.Label(self, text="LED Matrix GUI")
        self.label.pack(pady=10)


if __name__ == "__main__":
    app = App()
    app.mainloop() 