import tkinter as tk
import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
class GeradorFrequencias:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Frequências")
        self.root.iconbitmap(os.path.abspath("sine.ico"))
        self.label_frequencia = tk.Label(root, text="Digite a frequência (rl-Hz):")
        self.label_frequencia.pack()

        self.entry_frequencia = tk.Entry(root)
        self.entry_frequencia.pack()

        self.label_tipo_onda = tk.Label(root, text="Selecione o tipo de onda:")
        self.label_tipo_onda.pack()

        self.tipo_onda = tk.StringVar(root)
        self.tipo_onda.set("Senoidal")  # Valor padrão

        self.opcoes_tipo_onda = tk.OptionMenu(root, self.tipo_onda, "Senoidal", "Quadrada", "Triangular")
        self.opcoes_tipo_onda.pack()

        self.label_formula = tk.Label(root, text="Digite a fórmula da onda (usar 't' como tempo):")
        self.label_formula.pack()

        self.entry_formula = tk.Entry(root)
        self.entry_formula.insert(tk.END, "np.sin(2 * np.pi * frequencia * t)")
        self.entry_formula.pack()

        self.button = tk.Button(root, text="Gerar e Reproduzir-parar", command=self.toggle_reproducao)
        self.button.pack()

        self.label_info_frequencia = tk.Label(root, text="Frequência atual: ")
        self.label_info_frequencia.pack()

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        self.stream = None
        self.reproduzindo = False
        self.frequencia_atual = 0
        self.numero_amostras = 0  # Número de amostras para representar 1 segundo

    def toggle_reproducao(self):
        if self.reproduzindo:
            self.stop_reproducao()
        else:
            self.start_reproducao()

    def start_reproducao(self):
        try:
            frequencia = float(self.entry_frequencia.get())
            tipo_onda = self.tipo_onda.get()
            formula = self.entry_formula.get()

            self.frequencia_atual = frequencia
            self.reproduzindo = True

            duracao_ciclo = 1 / frequencia  # Calcular duração de um ciclo da frequência em segundos
            self.numero_amostras = int(44100 * duracao_ciclo)  # Calcular número de amostras para representar 1 ciclo da frequência

            duracao_total = self.numero_amostras / 44100  # Calcular duração total do sinal em segundos
            tempo = np.linspace(0, duracao_total, self.numero_amostras, False)
            sinal = self.gerar_sinal(formula, frequencia, tipo_onda, tempo)

            self.stream = sd.OutputStream(callback=self.callback_audio, channels=1, samplerate=44100)
            self.stream.start()

            self.label_info_frequencia.config(text=f"Frequência atual: {self.frequencia_atual:.2f} rl-Hz")
            self.plotar_grafico(tempo, sinal)

        except ValueError:
            tk.messagebox.showerror("Erro", "Digite um número válido para a frequência.")

    def stop_reproducao(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.reproduzindo = False

    def gerar_sinal(self, formula, frequencia, tipo_onda, tempo):
        t = tempo
        try:
            sinal = eval(formula)
        except Exception as e:
            tk.messagebox.showerror("Erro na Fórmula", f"Erro na fórmula:\n{str(e)}")
            return np.zeros_like(tempo)
        
        if tipo_onda == "Senoidal":
            return sinal
        elif tipo_onda == "Quadrada":
            return np.where(sinal > 0, 1, -1)
        elif tipo_onda == "Triangular":
            return np.arcsin(sinal)

    def callback_audio(self, outdata, frames, time, status):
        if not self.reproduzindo:
            return
        formula = self.entry_formula.get()
        sinal = self.gerar_sinal(formula, self.frequencia_atual, self.tipo_onda.get(), np.linspace(0, 1, frames, False))
        outdata[:] = sinal[:, np.newaxis]

    def plotar_grafico(self, tempo, sinal):
        self.ax.clear()
        self.ax.plot(tempo, sinal)
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Amplitude")
        self.ax.set_title("Sinal de Áudio")

        self.canvas.draw()
if __name__ == "__main__":
    root = tk.Tk()
    app = GeradorFrequencias(root)
    root.mainloop()
