import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Gestão de Patrimônio - Leitor Zebra", layout="wide")

# --- INICIALIZAÇÃO DO ESTADO ---
if 'historico_leituras' not in st.session_state:
    st.session_state.historico_leituras = []

# --- INTERFACE ---
st.title("📦 Sistema de Inventário e Etiquetas")

# Seleção do tipo de etiqueta
tipo_etiqueta = st.radio(
    "Selecione o tipo de etiqueta para as próximas leituras:",
    ["Papel", "Metal"],
    horizontal=True
)

# Campo de entrada para o Leitor Zebra
codigo_lido = st.text_input(
    "Aguardando leitura do código de barras...", 
    key="input_zebra", 
    placeholder="Passe o leitor no patrimônio",
    help="O leitor Zebra enviará o código e o comando Enter automaticamente."
)

# --- PROCESSAMENTO DOS DADOS ---
arquivo_entrada = "base_patrimonio.xlsx"

if os.path.exists(arquivo_entrada):
    try:
        df_base = pd.read_excel(arquivo_entrada)
        
        if codigo_lido:
            # Busca o código na Coluna B (Índice 1)
            # Garantimos que a comparação seja feita como String para evitar erros
            busca = df_base[df_base.iloc[:, 1].astype(str) == str(codigo_lido)]

            if not busca.empty:
                # ITEM ENCONTRADO: Extrai B, C, E e F
                novo_item = {
                    "Patrimônio": busca.iloc[0, 1],
                    "Descrição do Bem": busca.iloc[0, 2],
                    "Código do Local": busca.iloc[0, 4],
                    "Nome da Unidade": busca.iloc[0, 5],
                    "Tipo Etiqueta": tipo_etiqueta,
                    "Status": "Encontrado"
                }
                st.toast(f"✅ Item {codigo_lido} adicionado!", icon='🎉')
            else:
                # ITEM NÃO ENCONTRADO: Adiciona ao relatório com aviso
                novo_item = {
                    "Patrimônio": codigo_lido,
                    "Descrição do Bem": "NÃO ENCONTRADO",
                    "Código do Local": "N/A",
                    "Nome da Unidade": "N/A",
                    "Tipo Etiqueta": tipo_etiqueta,
                    "Status": "Não Encontrado na Base"
                }
                st.error(f"⚠️ Código {codigo_lido} não localizado, mas adicionado ao relatório.")

            # Evita duplicar o mesmo patrimônio na lista da sessão atual
            patrimonios_existentes = [item["Patrimônio"] for item in st.session_state.historico_leituras]
            
            if str(novo_item["Patrimônio"]) not in [str(p) for p in patrimonios_existentes]:
                st.session_state.historico_leituras.insert(0, novo_item)
            else:
                st.warning(f"O item {codigo_lido} já consta na lista abaixo.")

        # --- EXIBIÇÃO DO RELATÓRIO ---
        if st.session_state.historico_leituras:
            st.write("### Relatório de Itens Lidos")
            df_relatorio = pd.DataFrame(st.session_state.historico_leituras)
            
            # Exibe a tabela com destaque visual
            st.dataframe(df_relatorio, use_container_width=True)

            col1, col2 = st.columns(2)
            
            with col1:
                # Exportação para Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_relatorio.to_excel(writer, index=False, sheet_name='Leituras')
                
                st.download_button(
                    label="📥 Baixar Relatório (XLSX)",
                    data=output.getvalue(),
                    file_name=f"relatorio_inventario.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col2:
                if st.button("🗑️ Limpar Lista"):
                    st.session_state.historico_leituras = []
                    st.rerun()

    except Exception as e:
        st.error(f"Erro ao processar o arquivo Excel: {e}")
else:
    st.error(f"Arquivo '{arquivo_entrada}' não encontrado.")
