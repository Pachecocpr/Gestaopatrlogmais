import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de Patrimônio", page_icon="📦", layout="wide")

# Inicializa a lista de bens na memória do navegador, se ainda não existir
if 'lista_bens' not in st.session_state:
    st.session_state['lista_bens'] = []

st.title("📦 Gestão de Patrimônio Logístico")

# --- BARRA LATERAL (Ações) ---
st.sidebar.header("⚙️ Opções")
if st.sidebar.button("Limpar Lista Atual"):
    st.session_state['lista_bens'] = []
    st.rerun()

# --- INTERFACE DE ENTRADA ---
st.subheader("🔍 Identificação do Bem")
metodo = st.radio("Método de Leitura:", ["Leitor Zebra / Manual", "Câmera do Celular"], horizontal=True)

codigo_patrimonio = ""
if metodo == "Leitor Zebra / Manual":
    codigo_patrimonio = st.text_input("Aponte o leitor Zebra ou digite o código:", key="input_scan")
else:
    img_file = st.camera_input("Tire uma foto do código de barras")
    st.info("Nota: A leitura automática por foto requer processamento adicional.")

# --- FORMULÁRIO DE REGISTRO ---
if codigo_patrimonio:
    st.divider()
    with st.form("form_patrimonio", clear_on_submit=True):
        st.write(f"✍️ Cadastrando item: **{codigo_patrimonio}**")
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_etiqueta = st.selectbox("Tipo de Etiqueta:", ["Papel", "Metal", "Poliéster"])
        with col2:
            unidade = st.radio("Unidade:", ["Unidade 1", "Unidade 2"])
            
        descricao = st.text_input("Descrição resumida (Ex: Paleteira):")
        
        btn_salvar = st.form_submit_button("💾 Salvar na Lista")

        if btn_salvar:
            # Adiciona o bem à lista na memória
            novo_bem = {
                "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Código": codigo_patrimonio,
                "Descrição": descricao,
                "Etiqueta": tipo_etiqueta,
                "Unidade": unidade
            }
            st.session_state['lista_bens'].append(novo_bem)
            st.success(f"Item {codigo_patrimonio} adicionado!")

# --- VISUALIZAÇÃO E EXPORTAÇÃO ---
if st.session_state['lista_bens']:
    st.divider()
    st.subheader("📋 Itens Registrados nesta Sessão")
    
    # Converte a lista para um DataFrame para exibir e exportar
    df_bens = pd.DataFrame(st.session_state['lista_bens'])
    st.dataframe(df_bens, use_container_width=True)

    # Função para gerar o Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_bens.to_excel(writer, index=False, sheet_name='Patrimonio')
    
    # Botão de Download
    st.download_button(
        label="📥 Baixar Relatório em Excel",
        data=output.getvalue(),
        file_name=f"patrimonio_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Nenhum item registrado ainda.")
