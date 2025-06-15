import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, UnidentifiedImageError


class ImageResizerApp:
    def __init__(self, master):
        self.master = master
        master.title("Redimensionador de Imagens")
        master.geometry("600x500")  # Define um tamanho inicial para a janela

        self.source_folder = ""
        self.output_folder = ""
        self.resize_percentage = tk.StringVar(
            value="50%")  # Valor padrão para o combobox

        self._create_widgets()

    def _create_widgets(self):
        # --- Frame para seleção de pasta de origem ---
        source_frame = tk.LabelFrame(self.master, text="Pasta de Origem")
        source_frame.pack(pady=10, padx=10, fill="x")

        self.source_path_label = tk.Label(
            source_frame, text="Nenhuma pasta selecionada")
        self.source_path_label.pack(
            side="left", padx=5, pady=5, fill="x", expand=True)

        select_source_button = tk.Button(
            source_frame, text="Selecionar Pasta", command=self._select_source_folder)
        select_source_button.pack(side="right", padx=5, pady=5)

        # --- Frame para seleção da porcentagem de redimensionamento ---
        resize_options_frame = tk.LabelFrame(
            self.master, text="Porcentagem de Redimensionamento")
        resize_options_frame.pack(pady=10, padx=10, fill="x")

        percentage_options = ["25%", "50%", "75%"]
        self.percentage_combobox = ttk.Combobox(
            resize_options_frame, textvariable=self.resize_percentage, values=percentage_options, state="readonly")
        self.percentage_combobox.pack(pady=5)
        self.percentage_combobox.set("50%")  # Define o valor inicial exibido

        # --- Frame para seleção de pasta de saída ---
        output_frame = tk.LabelFrame(
            self.master, text="Pasta de Saída (Opcional)")
        output_frame.pack(pady=10, padx=10, fill="x")

        self.output_path_label = tk.Label(
            output_frame, text="Usará a pasta de origem se não selecionada")
        self.output_path_label.pack(
            side="left", padx=5, pady=5, fill="x", expand=True)

        select_output_button = tk.Button(
            output_frame, text="Selecionar Pasta", command=self._select_output_folder)
        select_output_button.pack(side="right", padx=5, pady=5)

        # --- Botão para aplicar redimensionamento ---
        apply_resize_button = tk.Button(
            self.master, text="Aplicar Redimensionamento", command=self._start_resize_thread)
        apply_resize_button.pack(pady=10)

        # --- Textarea para status ---
        status_frame = tk.LabelFrame(
            self.master, text="Status do Processamento")
        status_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.status_text = tk.Text(status_frame, height=10, state="disabled")
        self.status_text.pack(pady=5, padx=5, fill="both", expand=True)

        # **CORREÇÃO AQUI:** Use 'self.status_text' para referenciar o widget Text
        self.status_text_scrollbar = tk.Scrollbar(
            self.status_text, command=self.status_text.yview)
        self.status_text_scrollbar.pack(side="right", fill="y")
        self.status_text.config(yscrollcommand=self.status_text_scrollbar.set)

    def _select_source_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_folder = folder_selected
            self.source_path_label.config(text=self.source_folder)
            self._log_status(
                f"Pasta de origem selecionada: {self.source_folder}")

    def _select_output_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_folder = folder_selected
            self.output_path_label.config(text=self.output_folder)
            self._log_status(
                f"Pasta de saída selecionada: {self.output_folder}")
        else:
            self.output_folder = ""  # Limpa a pasta de saída se nada for selecionado
            self.output_path_label.config(
                text="Usará a pasta de origem se não selecionada")
            self._log_status(
                "Nenhuma pasta de saída selecionada. Será usada a pasta de origem.")

    def _log_status(self, message):
        self.status_text.config(state="normal")  # Habilita para escrita
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)  # Auto-scroll para o final
        self.status_text.config(state="disabled")  # Desabilita novamente
        # Força a atualização da UI para mostrar a mensagem imediatamente
        self.master.update_idletasks()

    def _start_resize_thread(self):
        if not self.source_folder:
            messagebox.showwarning(
                "Atenção", "Por favor, selecione uma pasta de origem primeiro.")
            return

        self._log_status("\nIniciando processamento de redimensionamento...")
        # Limpa o status anterior ao iniciar um novo processamento
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state="disabled")

        # Inicia o processamento em uma thread separada para não travar a UI
        threading.Thread(target=self._process_images).start()

    def _process_images(self):
        # Define a pasta de saída: usa a selecionada ou a de origem
        output_folder_to_use = self.output_folder if self.output_folder else self.source_folder
        if not os.path.exists(output_folder_to_use):
            os.makedirs(output_folder_to_use)
            self._log_status(f"Pasta de saída criada: {output_folder_to_use}")

        percentage_str = self.resize_percentage.get()
        # Converte a porcentagem de string ("50%") para float (0.50)
        percentage = int(percentage_str.replace("%", "")) / 100.0

        # Extensões de imagem suportadas (Pillow pode ter limitações com SVG vetorial)
        supported_extensions = ('.jpg', '.jpeg', '.png',
                                '.gif', '.webp', '.bmp', '.tiff')
        processed_count = 0
        skipped_count = 0
        error_count = 0

        # Percorre os arquivos na pasta de origem
        for filename in os.listdir(self.source_folder):
            file_path = os.path.join(self.source_folder, filename)
            # Verifica se é um arquivo e se tem uma extensão suportada
            if os.path.isfile(file_path) and filename.lower().endswith(supported_extensions):
                try:
                    self._log_status(f"Processando: {filename}...")
                    img = Image.open(file_path)

                    # Calcula as novas dimensões baseadas na porcentagem
                    original_width, original_height = img.size
                    new_width = int(original_width * percentage)
                    new_height = int(original_height * percentage)

                    # Redimensiona a imagem usando o algoritmo LANCZOS para melhor qualidade
                    resized_img = img.resize(
                        (new_width, new_height), Image.Resampling.LANCZOS)

                    # Define o caminho e nome do arquivo de saída
                    base_name, ext = os.path.splitext(filename)
                    # Adiciona a porcentagem no nome do arquivo de saída
                    output_filename = f"{base_name}_resized_{percentage_str}{ext}"
                    output_path = os.path.join(
                        output_folder_to_use, output_filename)

                    # Salva a imagem redimensionada, com ajuste de qualidade para JPG
                    if ext.lower() in ('.jpg', '.jpeg'):
                        # Qualidade e otimização para JPG
                        resized_img.save(
                            output_path, quality=90, optimize=True)
                    else:
                        resized_img.save(output_path)  # Outros formatos

                    self._log_status(
                        f"  --> Redimensionado e salvo como: {output_filename}")
                    processed_count += 1

                except UnidentifiedImageError:
                    self._log_status(
                        f"  Pulando {filename}: Não é um formato de imagem reconhecido ou está corrompido.")
                    skipped_count += 1
                except Exception as e:
                    self._log_status(f"  Erro ao processar {filename}: {e}")
                    error_count += 1
            else:
                self._log_status(
                    f"  Pulando: {filename} (não é um arquivo de imagem suportado ou é um diretório).")
                skipped_count += 1

        self._log_status(f"\n--- Processamento Concluído ---")
        self._log_status(f"Total de imagens processadas: {processed_count}")
        self._log_status(f"Total de arquivos pulados: {skipped_count}")
        self._log_status(f"Total de erros: {error_count}")
        messagebox.showinfo("Concluído", "Todas as imagens foram processadas.")


# --- Configuração e execução da aplicação ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageResizerApp(root)
    root.mainloop()
