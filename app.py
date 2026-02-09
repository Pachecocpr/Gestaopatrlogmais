import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Patrimônio Logística", layout="centered")

# Inicializa a lista de patrimônio e uma variável de controle para o código
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

st.title("📦 Gestão de Patrimônio")
st.caption("Configurado para salvamento rápido com Leitor Zebra / Enter.")

# --- ENTRADA DE DADOS ---
st.subheader("🔍 Escanear Item")

# Campo de entrada de texto
codigo_lido = st.text_input("Aponte o leitor e bibe (Enter salva automaticamente):", key="input_scan")

# --- INTERFACE DE SELEÇÃO ---
# Unidade e Etiqueta ficam fora do formulário para estarem sempre prontas
col1, col2 = st.columns(2)
with col1:
    unidade = st.radio("Unidade:", ["Unidade 1", "Unidade 2"], horizontal=True)
with col2:
    etiqueta = st.selectbox("Etiqueta:", ["Metal", "Papel", "Poliéster"])

descricao = st.text_input("Descrição do Bem:")

# --- LÓGICA DE SALVAMENTO AUTOMÁTICO ---
# Se houver um código e o usuário apertar Enter no teclado ou o Zebra enviar o Enter
if codigo_lido:
    # Criamos um botão de confirmação que também serve como gatilho
    if st.button("Confirmar e Salvar Agora") or (codigo_lido and st.session_state.get('last_code') != codigo_lido):
        
        novo_registro = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Código": codigo_lido,
            "Descrição": descricao,
            "Unidade": unidade,
            "Etiqueta": etiqueta
        }
        
        # Adiciona à lista
        st.session_state['lista_patrimonio'].append(novo_registro)
        st.session_state['last_code'] = codigo_lido # Evita duplicar no mesmo ciclo
        
        st.success(f"✅ Item {codigo_lido} salvo automaticamente!")
        st.info("Pronto para o próximo código.")
        # O Streamlit reinicia o ciclo e limpa o foco para o próximo item

# --- VISUALIZAÇÃO E EXCEL ---
if st.session_state['lista_patrimonio']:
    st.divider()
    df = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df, use_container_width=True)
    
    # Gerar Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button("📥 Baixar Relatório Excel", output.getvalue(), "patrimonio.xlsx")

# Barra lateral para limpar
if st.sidebar.button("Limpar Tudo"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
