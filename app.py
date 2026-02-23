import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Gestão de Patrimônio - Leitor Zebra", layout="wide")

# --- INICIALIZAÇÃO DO ESTADO ---
if 'historico_leituras' not in st.session_state:
    st.session_state.historico_leituras = []

# Função para processar a leitura e limpar o campo
def processar_leitura():
    codigo = st.session_state.input_zebra.strip()
    if codigo:
        arquivo_entrada = "base_patrimonio.xlsx"
        
        if os.path.exists(arquivo_entrada):
            try:
                df_base = pd.read_excel(arquivo_entrada)
                # Busca na Coluna B (Índice 1)
                busca = df_base[df_base.iloc[:, 1].astype(str) == str(codigo)]

                if not busca.empty:
                    novo_item = {
                        "Patrimônio": busca.iloc[0, 1],
                        "Descrição do Bem": busca.iloc[0, 2],
                        "Código do Local": busca.iloc[0, 4],
                        "Nome da Unidade": busca.iloc[0, 5],
                        "Tipo Etiqueta": st.session_state.tipo_etiqueta,
                        "Status": "Encontrado"
                    }
                else:
                    novo_item = {
                        "Patrimônio": codigo,
                        "Descrição do Bem": "NÃO ENCONTRADO",
                        "Código do Local": "N/A",
                        "Nome da Unidade": "N/A",
                        "Tipo Etiqueta": st.session_state.tipo_etiqueta,
                        "Status": "Não Encontrado"
                    }

                # Evita duplicados na lista
                patrimonios_existentes = [str(item["Patrimônio"]) for item in st.session_state.historico_leituras]
                if str(novo_item["Patrimônio"]) not in patrimonios_existentes:
                    st.session_state.historico_leituras.insert(0, novo_item)
                
            except Exception as e:
                st.error(f"Erro ao ler banco de dados: {e}")
        else:
            st.error("Arquivo 'base_patrimonio.xlsx' não encontrado!")
        
        # LIMPA O CAMPO: Reseta o valor do input no session_state
        st.session_state.input_zebra = ""

# --- INTERFACE ---
st.title("📦 Sistema de Inventário e Etiquetas")

# Seleção do tipo de etiqueta
st.radio(
    "Selecione o tipo de etiqueta:",
    ["Papel", "Metal"],
    horizontal=True,
    key="tipo_etiqueta"
)

# Campo de entrada com o parâmetro 'on_change'
# Isso faz com que a função 'processar_leitura' rode toda vez que o leitor der "Enter"
st.text_input(
    "Aguardando leitura do leitor Zebra...", 
    key="input_zebra", 
    on_change=processar_leitura,
    placeholder="Bipe o código aqui..."
)

# --- EXIBIÇÃO DO RELATÓRIO ---
if st.session_state.historico_leituras:
    st.write("---")
    st.write("### Itens Lidos")
    df_relatorio = pd.DataFrame(st.session_state.historico_leituras)
    st.dataframe(df_relatorio, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_relatorio.to_excel(writer, index=False, sheet_name='Leituras')
        
        st.download_button(
            label="📥 Baixar Relatório (XLSX)",
            data=output.getvalue(),
            file_name="relatorio_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col2:
        if st.button("🗑️ Limpar Tudo"):
            st.session_state.historico_leituras = []
            st.rerun()

st.caption("Dica: O cursor deve estar no campo de texto para o leitor Zebra funcionar.")
