import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pyaudio
import threading
import time
import json
import os
from sinal import GeradorFrequencias
import webbrowser
from PIL import Image, ImageTk
class MicrophoneGraphApp:
    def __init__(self, root):
        def show_splash(root, image_path, duration):
            if not os.path.exists(image_path):
                print(f"Erro: O arquivo '{image_path}' não foi encontrado.")
                root.destroy()
                return

            # Create splash window
            splash = tk.Toplevel(root)
            splash.overrideredirect(True)  # Remove window decorations

            # Load and display image
            image = Image.open(image_path)
            photo = ImageTk.PhotoImage(image)
            label = tk.Label(splash, image=photo)
            label.image = photo  # Keep a reference to avoid garbage collection
            label.pack()

            # Center the splash window
            width, height = image.size
            screen_width = splash.winfo_screenwidth()
            screen_height = splash.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            splash.geometry(f'{width}x{height}+{x}+{y}')

            # Destroy splash window after the specified duration
            root.after(duration, splash.destroy)
        
        image_path = os.path.abspath("sine.png")

    # Show the splash screen
        show_splash(root, image_path, 2444) 
        
        self.root = root
        self.root.title("OPEN sine")
        self.root.iconbitmap(os.path.abspath("sine.ico"))
        

        # Configuração inicial do matplotlib
        self.fig, self.ax = plt.subplots()
        self.x = np.arange(0, 2000)
        self.y_left = np.zeros(2000)
        self.y_right = np.zeros(2000)
        self.line_left, = self.ax.plot(self.x, self.y_left, label="Canal Esquerdo")
        self.line_right, = self.ax.plot(self.x, self.y_right, label="Canal Direito", alpha=0.7)
        self.ax.legend()
        

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        

        # Frame para os controles
        control_frame = ttk.Frame(root)
        self.wave_zoom_slider = tk.Scale(control_frame, from_=1, to=10, orient=tk.HORIZONTAL)
        self.wave_zoom_slider.pack()
        control_frame.pack(side=tk.TOP, fill=tk.X)
        def helaa():
            webbrowser.open(os.path.abspath("help.pdf"))
            
        
        help = tk.Button(control_frame,text="Ajuda como calibrar - About",command=helaa)
        help.pack()
        

        # Adicionar label e slider de ganho
        self.gain = tk.DoubleVar(value=1.0)
        self.gain_label = ttk.Label(control_frame, text="Zoom")
        self.gain_label.pack(side=tk.LEFT, padx=5)
        self.gain_slider = ttk.Scale(control_frame, from_=0.1, to=10.0, orient=tk.HORIZONTAL, variable=self.gain)
        self.gain_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Adicionar slider de calibrar
        self.calibration = tk.DoubleVar(value=1.0)
        self.calibration_label = ttk.Label(control_frame, text="Calibragem")
        self.calibration_label.pack(side=tk.LEFT, padx=5)
        self.calibration_slider = ttk.Scale(control_frame, from_=-44, to=144, orient=tk.HORIZONTAL, variable=self.calibration)
        self.calibration_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Dentro do método __init__ da classe MicrophoneGraphApp
        



        # Adicionar checkbutton para dividir canais
        self.split_channels = tk.BooleanVar(value=False)
        self.split_checkbutton = ttk.Checkbutton(control_frame, text="Dividir Canais (E/D)", variable=self.split_channels)
        self.split_checkbutton.pack(side=tk.LEFT, padx=5)

        # Adicionar slider para separar as linhas
        self.offset = tk.DoubleVar(value=0.0)
        self.offset_label = ttk.Label(control_frame, text="Separação das Linhas")
        self.offset_label.pack(side=tk.LEFT, padx=5)
        self.offset_slider = ttk.Scale(control_frame, from_=0, to=32767, orient=tk.HORIZONTAL, variable=self.offset)
        self.offset_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Adicionar slider para taxa de atualização
        self.update_interval = tk.DoubleVar(value=0.1)
        self.update_label = ttk.Label(control_frame, text="Tempo de Atualização (s)")
        self.update_label.pack(side=tk.LEFT, padx=5)
        self.update_slider = ttk.Scale(control_frame, from_=0.01, to=1.0, orient=tk.HORIZONTAL, variable=self.update_interval)
        self.update_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Adicionar botão de pausa/despausa
        self.paused = tk.BooleanVar(value=False)
        self.pause_button = ttk.Button(control_frame, text="Pausar", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        # Adicionar Checkbutton para exibir/ocultar grade
        self.show_grid = tk.BooleanVar(value=False)
        self.grid_checkbutton = ttk.Checkbutton(control_frame, text="Mostrar Grade", variable=self.show_grid, command=self.toggle_grid)
        self.grid_checkbutton.pack(side=tk.LEFT, padx=5)
        self.helpgg = ttk.Button(control_frame,text="Gerador de frequência",command=self.abrir_gerador)
        self.helpgg.pack()

        # Adicionar Listbox para mostrar posições dos sliders e informações de frequência e nível
        self.update_listbox = tk.Listbox(root, height=10, width=50)
        self.update_listbox.pack(side=tk.RIGHT, padx=5, fill=tk.Y)
        # Dentro do método __init__ da classe MicrophoneGraphApp
        self.wave_zoom_slider.bind("<ButtonRelease-1>", lambda event: self.update_wave_zoom())


        # Iniciar thread de áudio
        self.stream = None
        self.audio_thread = threading.Thread(target=self.update_graph)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        self.load_slider_positions()
    # Dentro da classe MicrophoneGraphApp
    def update_wave_zoom(self):
        zoom_factor = self.wave_zoom_slider.get()  # Obter o fator de zoom selecionado pelo usuário
        self.ax.set_ylim([-32768 / zoom_factor, 32767 / zoom_factor])  # Aplicar o zoom na onda
        self.canvas.draw()  # Redesenhar o gráfico
        
    def start_stream(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=2,
                                  rate=60000,
                                  input=True,
                                  frames_per_buffer=1024)
    
    
    
    
    
    def save_slider_positions(self):
        positions = {
            "gain": self.gain.get(),
            "calibration": self.calibration.get(),
            "offset": self.offset.get(),
            "update_interval": self.update_interval.get(),
            "split_channels": self.split_channels.get(),
            "show_grid": self.show_grid.get(),
        }
        with open("slider_positions.json", "w") as file:
            json.dump(positions, file)

    def load_slider_positions(self):
        try:
            with open("slider_positions.json", "r") as file:
                positions = json.load(file)
                self.gain.set(positions["gain"])
                self.calibration.set(positions["calibration"])
                self.offset.set(positions["offset"])
                self.update_interval.set(positions["update_interval"])
                self.split_channels.set(positions["split_channels"])
                self.show_grid.set(positions["show_grid"])
        except FileNotFoundError:
            pass
    
    
    def update_graph(self):
        self.start_stream()
        while True:
            if not self.paused.get():
                data = np.frombuffer(self.stream.read(1024), dtype=np.int16).reshape(-1, 2)
                
                if self.calibration.get() < 0:

                    p_left_channel = data[:, 0]   /  self.calibration.get()
                    p_right_channel = data[:, 1] /  self.calibration.get()
                    left_channel = data[:, 0]   /  self.calibration.get()
                    right_channel = data[:, 1] /  self.calibration.get()
                else:
                    p_left_channel = data[:, 0]   *  self.calibration.get()
                    p_right_channel = data[:, 1] *  self.calibration.get()
                    left_channel = data[:, 0]   *  self.calibration.get()
                    right_channel = data[:, 1] *  self.calibration.get()


                # Aplicar ganho
                gain = self.gain.get()
                left_channel = left_channel * gain
                right_channel = right_channel * gain
                left_channel = np.clip(left_channel, -32768, 32767)
                right_channel = np.clip(right_channel, -32768, 32767)

                # Atualizar dados dos gráficos
                if self.split_channels.get():
                    self.y_left = np.roll(self.y_left, -1024)
                    self.y_right = np.roll(self.y_right, -1024)
                    self.y_left[-1024:] = left_channel
                    self.y_right[-1024:] = right_channel
                else:
                    mixed_channel = (left_channel + right_channel) / 2
                    self.y_left = np.roll(self.y_left, -1024)
                    self.y_right = np.roll(self.y_right, -1024)
                    self.y_left[-1024:] = mixed_channel
                    self.y_right[-1024:] = mixed_channel

                # Aplicar offset de separação
                offset = self.offset.get()
                self.line_left.set_ydata(self.y_left + offset)
                self.line_right.set_ydata(self.y_right - offset)
                self.ax.set_ylim([-32768 - offset, 32767 + offset])
                self.canvas.draw()

                # Calcular frequência dominante
                fft_result = np.fft.fft(left_channel)
                fft_freq = np.fft.fftfreq(len(left_channel), 1/44100)
                idx = np.argmax(np.abs(fft_result))
                freq = abs(fft_freq[idx]) * 1.44
                level = np.abs(fft_result[idx]) / len(p_left_channel)
                fft_result_original = np.fft.fft(p_left_channel)
                idx_original = np.argmax(np.abs(fft_result_original))
                level_original = np.abs(fft_result_original[idx_original]) / len(p_left_channel)

                # Mostrar posições dos sliders e informações de frequência e nível
                update_interval = self.update_interval.get()
                self.update_listbox.delete(0, tk.END)
                self.update_listbox.insert(tk.END, f"zoom: {gain:.2f} X")
                self.update_listbox.insert(tk.END, f"Separação das Linhas: {offset:.2f}")
                self.update_listbox.insert(tk.END, f"Tempo de Atualização: {update_interval:.2f} s")
                self.update_listbox.insert(tk.END, f"Frequência: {freq:.2f} Hz")
                self.update_listbox.insert(tk.END, f"Nível: {level_original/1000:.2f} V")
                self.update_listbox.insert(tk.END, f"escala em milissegundos 1000 = 1 segundo")
                self.update_listbox.insert(tk.END, f"Ponto de calibragem {self.calibration.get()}")


            time.sleep(self.update_interval.get())

    def toggle_pause(self):
        if self.paused.get():
            self.paused.set(False)
            self.pause_button.config(text="Pausar")
        else:
            self.paused.set(True)
            self.pause_button.config(text="Despausar")

    def abrir_gerador(self):
            print("oiss")
            self.janela_gerador = tk.Toplevel(self.root)
            self.janela_gerador.title("Gerador de Frequências")

            # Iniciar a classe GeradorFrequencias na nova janela
            self.gerador = GeradorFrequencias(self.janela_gerador)
    def toggle_grid(self):
        self.ax.grid(self.show_grid.get())
        self.canvas.draw()
        

    def on_closing(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()
            self.save_slider_positions()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MicrophoneGraphApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
