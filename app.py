import pandas as pd
import tkinter as tk
from tkinter import messagebox, ttk
import os

def gerar_relatorio():
    # Nome do arquivo que você corrigiu
    arquivo_entrada = "base_patrimonio.xlsx"
    
    # Verifica se o arquivo realmente existe na pasta
    if not os.path.exists(arquivo_entrada):
        messagebox.showerror("Erro", f"O arquivo '{arquivo_entrada}' não foi encontrado na mesma pasta do script!")
        return

    try:
        # 1. Carrega o arquivo Excel
        df = pd.read_excel(arquivo_entrada)
        
        # 2. Captura a escolha da etiqueta
        tipo_etiqueta = combo_etiqueta.get()
        
        # 3. Seleção das Colunas conforme a instrução (B, C, E, F)
        # No pandas/Python, os índices começam em 0:
        # Coluna B = índice 1 | Coluna C = índice 2 | Coluna E = índice 4 | Coluna F = índice 5
        colunas_selecionadas = df.iloc[:, [1, 2, 4, 5]]
        
        # 4. Nome do arquivo de saída baseado na escolha
        arquivo_saida = f"relatorio_final_{tipo_etiqueta.lower()}.xlsx"
        
        # 5. Exportação
        colunas_selecionadas.to_excel(arquivo_saida, index=False)
        
        messagebox.showinfo("Sucesso", f"Relatório de {tipo_etiqueta} gerado: {arquivo_saida}")
        
    except Exception as e:
        messagebox.showerror("Erro Processamento", f"Ocorreu um erro ao ler o Excel: {e}")

# --- Configuração da Interface Gráfica (Tkinter) ---
root = tk.Tk()
root.title("Gerenciador de Patrimônio")
root.geometry("350x250")

# Centralizar os elementos
frame = tk.Frame(root)
frame.pack(expand=True)

tk.Label(frame, text="Sistema de Etiquetas", font=("Arial", 12, "bold")).pack(pady=10)

# Instrução
tk.Label(frame, text="Selecione o tipo de etiqueta:").pack()

# Menu de Seleção (Combobox)
combo_etiqueta = ttk.Combobox(frame, values=["Papel", "Metal"], state="readonly")
combo_etiqueta.set("Papel") # Valor padrão
combo_etiqueta.pack(pady=10)

# Botão de Ação
btn_gerar = tk.Button(
    frame, 
    text="Gerar Relatório Excel", 
    command=gerar_relatorio,
    bg="#2ecc71", 
    fg="white", 
    font=("Arial", 10, "bold"),
    padx=10,
    pady=5
)
btn_gerar.pack(pady=20)

# Rodapé informativo
tk.Label(root, text="O arquivo 'base_patrimonio.xlsx' deve estar nesta pasta.", font=("Arial", 7)).pack(side="bottom")

root.mainloop()
