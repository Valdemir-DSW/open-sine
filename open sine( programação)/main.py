import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import StringVar, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser
import os
from PIL import Image  # Para trabalhar com imagens

# Configurações de áudio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512  # Tamanho do buffer

# Inicializando PyAudio
audio = pyaudio.PyAudio()

# Variáveis globais para armazenar dados de áudio e configurações de ganho
audio_data = np.zeros(CHUNK)
gain_base_map = {"1x": 1, "2x": 2, "3x": 3}  # Mapeamento de multiplicadores de ganho
gain_base = 1  # Ganho base
gain_fine = 0  # Ganho fino
calibrate_gain = 0  # Calibração do ganho base

# Função para capturar áudio em uma thread separada
def audio_capture():
    global audio_data
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    while True:
        audio_data = np.frombuffer(stream.read(CHUNK), dtype=np.int16) * gain_base_map[gain_option.get()] * (1 + gain_fine) * (10 ** calibrate_gain)

# Função de atualização para o gráfico
def update(frame):
    global audio_data
    line.set_ydata(audio_data)

    if extra_line_var.get():  # Verifica se a caixa de marcação está marcada
        # Aplica um fator de ajuste para gerar a linha extra com a mesma sincronia e ganho
        factor = 2  # Fator de ajuste para a linha extra (ajuste conforme necessário)
        extra_line.set_ydata(audio_data * factor)  # Gera a linha extra baseada na linha principal com o fator de ajuste
    else:
        extra_line.set_ydata(np.zeros(CHUNK))  # Define a linha extra como zeros se a caixa de marcação não estiver marcada

    # Atualiza o visor de amplitude
    amplitude = np.max(np.abs(audio_data))  # Calcula a amplitude como o valor absoluto máximo
    amplitude_var.set(amplitude)  # Atualiza o visor de amplitude

    # Atualiza o visor de tensão com base na relação configurada
    update_tensao()

    return line, extra_line


# Função para ajustar o ganho base
def set_gain_base(event):
    global gain_base
    gain_base = gain_base_map[gain_option.get()]

# Função para ajustar o ganho fino
def set_gain_fine(value):
    global gain_fine
    gain_fine = float(value)

# Função para calibrar o ganho base
def set_calibrate_gain(value):
    global calibrate_gain
    calibrate_gain = round(float(value))

    # Salvar a configuração ao fechar
    with open("config.txt", "w") as file:
        file.write(str(calibrate_gain))

varfree = 1  # Inicialmente, o gráfico não está congelado

def defreeze_graph():
    global varfree
    varfree = 1  # Marcar que o gráfico está descongelado
    ani.event_source.start()
    freeze_button.config(text="Congelar Gráfico", command=freeze_graph)

def freeze_graph():
    global varfree
    varfree = 0  # Marcar que o gráfico está congelado
    ani.event_source.stop()  # Pausar a animação
    freeze_button.config(text="Descongelar Gráfico", command=defreeze_graph)

    # Configurar o botão de congelar para descongelar quando pressionado
    freeze_button.config(command=defreeze_graph)

def export_png():
    filename = tk.filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if filename:
        fig.savefig(filename, format="png")
        messagebox.showinfo("Exportar PNG", "Gráfico exportado como PNG com sucesso!")

# Configuração da interface tk
root = tk.Tk()
root.title("open sine - By Valdemir")
root.iconbitmap(os.path.abspath("sine.ico"))
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

mainframe = ttk.Frame(notebook, padding="3 3 12 12")
mainframe.pack(fill=tk.BOTH, expand=True)
notebook.add(mainframe, text='Controle')

settingsframe = ttk.Frame(notebook, padding="3 3 12 12")
settingsframe.pack(fill=tk.BOTH, expand=True)
notebook.add(settingsframe, text='Configurações')

# Label e OptionMenu para o ganho base
ttk.Label(mainframe, text="Ganho Base:").grid(column=1, row=1, sticky=tk.W)
gain_option = tk.StringVar()
gain_menu = ttk.Combobox(mainframe, textvariable=gain_option, values=["1x", "2x", "3x"])
gain_menu.set("1x")
gain_menu.grid(column=2, row=1, sticky=(tk.W, tk.E))
gain_menu.bind("<<ComboboxSelected>>", set_gain_base)

amplitude_var = tk.DoubleVar()
amplitude_label = ttk.Label(mainframe, text="Amplitude:")
amplitude_label.grid(column=1, row=5, sticky=tk.W)
amplitude_display = ttk.Label(mainframe, textvariable=amplitude_var)
amplitude_display.grid(column=2, row=5, sticky=tk.W)
tensao_var = tk.DoubleVar()
tensao_label = ttk.Label(mainframe, text="Tensão:")
tensao_label.grid(column=1, row=6, sticky=tk.W)
tensao_display = ttk.Label(mainframe, textvariable=tensao_var)
tensao_display.grid(column=2, row=6, sticky=tk.W)


def update_tensao():
    amplitude = amplitude_var.get()  
    relacao_str = relacao_var.get() 

    # Verifica se a relação é um número válido antes de tentar a conversão
    if relacao_str.replace(".", "", 1).isdigit() or relacao_str.replace("-", "", 1).isdigit():
        relacao = float(relacao_str)  # Converte a relação para float
        tensao = amplitude * relacao  # Calcula a tensão com base na relação

        if amplitude < 0:
            tensao *= -1

        tensao_var.set(tensao)  
    else:
        tensao_var.set("N/A") 



relacao_label = ttk.Label(mainframe, text="Relação Amplitude-Tensão:")
relacao_label.grid(column=1, row=7, sticky=tk.W)
relacao_var = tk.StringVar(value="1")  # Valor padrão da relação
relacao_entry = ttk.Entry(mainframe, textvariable=relacao_var)
relacao_entry.grid(column=2, row=7, sticky=tk.W)
relacao_entry.bind("<Return>", lambda event: update_tensao())  # Atualiza a tensão ao pressionar Enter
# Label e Scale para o ganho fino
ttk.Label(mainframe, text="Ganho Fino:").grid(column=1, row=2, sticky=tk.W)
gain_scale_var = StringVar()
gain_scale_var.set("0.0")
gain_scale_label = ttk.Label(mainframe, textvariable=gain_scale_var)
gain_scale_label.grid(column=3, row=2, sticky=(tk.W, tk.E))
gain_scale = ttk.Scale(mainframe, orient=tk.HORIZONTAL, length=200, from_=0, to_=1, command=set_gain_fine, variable=gain_scale_var)
gain_scale.grid(column=2, row=2, sticky=(tk.W, tk.E))

def update_calibrate_gain_value(value):
    try:
        float_value = float(value)
        print(float_value)
        calibrate_gain_value_label.config(text=f"Valor do Slide de Calibração: {float_value:.2f}")
    except ValueError:
        pass
    print("erro")
    save_config()
    
    
    

def save_config():
    global gain_base, gain_fine, calibrate_gain
    with open("config.txt", "w") as file:
        file.write(f"Ganho Base: {gain_base}\n")
        file.write(f"Ganho Fino: {gain_fine}\n")
        file.write(f"Calibração do Ganho: {calibrate_gain}\n")
# Opção para escolher a entrada de áudio
audio_input_label = ttk.Label(settingsframe, text="Escolher Entrada de Áudio:")
audio_input_label.pack()

audio_input_options = ["Microfone", "Entrada de Linha", "Outro"]
audio_input_var = tk.StringVar()
audio_input_var.set(audio_input_options[0])  # Definindo a opção padrão

audio_input_menu = ttk.OptionMenu(settingsframe, audio_input_var, *audio_input_options)
audio_input_menu.pack()

# Opção para trocar o tema da interface
theme_label = ttk.Label(settingsframe, text="Trocar Tema da Interface:")
theme_label.pack()

def change_theme():
    current_theme = root.tk.call("ttk::style", "theme", "use")
    new_theme = "clam" if current_theme == "default" else "default"
    root.tk.call("ttk::style", "theme", "use", new_theme)

def site():
    webbrowser.open("https://valdemir-rs.rf.gd/")

theme_button = ttk.Button(settingsframe, text="Alternar Tema", command=change_theme)
theme_button.pack()
theme_button2 = ttk.Button(settingsframe, text="Visite meu site!", command=site)
theme_button2.pack()

# Configuração do ganho de calibração
calibrate_gain_label = ttk.Label(settingsframe, text="Calibração do Ganho:")
calibrate_gain_label.pack()
calibrate_gain_label_desc = ttk.Label(settingsframe, text='''
    Com ela você vai poder definir o ponto base do início de 
    medição porque cada placa de áudio tem uma estrutura de ganho
    diferente. Aqui você pode fazer a calibragem do ponto zero.
''')
def load_config():
    try:
        with open("config.txt", "r") as file:
            return int(file.read())
    except FileNotFoundError:
        return 0
calibrate_gain_label_desc.pack()
calibrate_gain_var = tk.DoubleVar()
calibrate_gain_var.set(load_config())
calibrate_gain_scale = ttk.Scale(settingsframe, orient=tk.HORIZONTAL, length=400, from_=-1, to_=4, command=set_calibrate_gain, variable=calibrate_gain_var)
calibrate_gain_scale.pack()
calibrate_gain_scale.config(command=lambda value: (set_calibrate_gain(value), update_calibrate_gain_value(value)))
# Função para ajustar o número de canais (CHANNELS)
def set_channels(value):
    global CHANNELS
    CHANNELS = int(value)
    print(f"Número de Canais: {CHANNELS}")

# Função para ajustar a taxa de amostragem (RATE)
def set_rate(value):
    global RATE
    RATE = int(value)
    print(f"Taxa de Amostragem (RATE): {RATE}")

# Função para ajustar o tamanho do buffer (CHUNK)
def set_chunk(value):
    global CHUNK
    CHUNK = int(value)
    print(f"Tamanho do Buffer (CHUNK): {CHUNK}")

# Label para mostrar o valor do slide de calibração na Label
calibrate_gain_value_label = ttk.Label(settingsframe, text="Valor do Slide de Calibração:")
calibrate_gain_value_label.pack()
# Slider para ajustar o número de canais (CHANNELS)
channels_label = ttk.Label(settingsframe, text="Número de Canais:")
channels_label.pack()
channels_slider = tk.Scale(settingsframe, orient=tk.HORIZONTAL, length=200, from_=1, to=2, command=set_channels)
channels_slider.pack()

# Slider para ajustar a taxa de amostragem (RATE)
rate_label = ttk.Label(settingsframe, text="Taxa de Amostragem (RATE):")
rate_label.pack()
rate_slider = ttk.Scale(settingsframe, orient=tk.HORIZONTAL, length=200, from_=22050, to=44100, command=set_rate)
rate_slider.pack()

# Slider para ajustar o tamanho do buffer (CHUNK)
chunk_label = ttk.Label(settingsframe, text="Tamanho do Buffer (CHUNK):")
chunk_label.pack()
chunk_slider = ttk.Scale(settingsframe, orient=tk.HORIZONTAL, length=200, from_=256, to=1024, command=set_chunk)
chunk_slider.pack()

# Botão para congelar o gráfico
freeze_button = ttk.Button(mainframe, text="Congelar Gráfico",command=freeze_graph)
freeze_button.grid(column=1, row=4, sticky=tk.W)

# Botão para exportar o gráfico como PNG
export_button = ttk.Button(mainframe, text="Exportar PNG")
export_button.grid(column=2, row=4, sticky=tk.W)
export_button.config(command=export_png)

# Configuração do gráfico
fig, ax = plt.subplots()
x = np.arange(0, 2 * CHUNK, 2)
line, = ax.plot(x, np.random.rand(CHUNK))
extra_line, = ax.plot(x, np.zeros(CHUNK))  # Adiciona uma linha extra
extra_line_var = tk.IntVar(value=0)  # Variável para controlar se a linha extra será mostrada ou não

# Função de atualização para o gráfico

ax.set_ylim(-2**15, 2**15)
ax.set_xlim(0, CHUNK)

canvas = FigureCanvasTkAgg(fig, master=mainframe)
canvas.get_tk_widget()
canvas.draw()
canvas.get_tk_widget().grid(column=1, row=3, columnspan=3)

ani = animation.FuncAnimation(fig, update, blit=True)

# Adicionando a caixa de marcação para a linha extra
extra_line_var = tk.IntVar(value=0)  # Variável para controlar se a linha extra será mostrada ou não
extra_line_check = ttk.Checkbutton(mainframe, text="Separar os lados em 2 linhas", variable=extra_line_var)
extra_line_check.grid(column=4, row=4, sticky=tk.W)

# Iniciar a captura de áudio em uma thread separada
audio_thread = threading.Thread(target=audio_capture)
audio_thread.daemon = True  # A thread será encerrada quando o programa principal encerrar
audio_thread.start()

# Fechando o stream e PyAudio ao encerrar o gráfico
def close(event):
    audio.terminate()

    # Salvar a configuração ao fechar
    with open("config.txt", "w") as file:
        file.write(str(calibrate_gain))

fig.canvas.mpl_connect('close_event', close)

# Rodando a interface tk
root.mainloop()
