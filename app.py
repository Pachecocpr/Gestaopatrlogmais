import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de Patrimônio", page_icon="📦", layout="centered")

st.title("📦 Gestão de Patrimônio Logístico")
st.write("Registre e controle os bens das unidades.")

# --- INTERFACE DE ENTRADA ---
st.subheader("🔍 Identificação do Bem")

# Opção para escolher o método de entrada
metodo = st.radio("Método de Leitura:", ["Leitor Zebra / Manual", "Câmera do Celular"], horizontal=True)

codigo_patrimonio = ""

if metodo == "Leitor Zebra / Manual":
    # O leitor Zebra funciona como um teclado. 
    codigo_patrimonio = st.text_input("Aponte o leitor Zebra ou digite o código:", key="zebra_input")
else:
    st.info("Use o botão abaixo para abrir a câmera e capturar o código.")
    img_file = st.camera_input("Tire uma foto do código de barras")
    if img_file:
        st.warning("Imagem capturada! (Para decodificar o código automaticamente via foto, é necessário integrar uma biblioteca de visão computacional).")

# --- FORMULÁRIO DE DETALHES ---
if codigo_patrimonio:
    st.divider()
    st.success(f"Código Identificado: **{codigo_patrimonio}**")
    
    with st.form("registro_patrimonio"):
        col1, col2 = st.columns(2)
        with col1:
            tipo_etiqueta = st.selectbox("Tipo de Etiqueta:", ["Papel (Comum)", "Metal (Patrimonial)", "Poliéster"])
        with col2:
            unidade = st.radio("Unidade de Alocação:", ["Unidade 1", "Unidade 2"], index=0)
        
        descricao_bem = st.text_area("Descrição do Bem:", placeholder="Ex: Empilhadeira, Notebook...")
        enviar = st.form_submit_button("💾 Salvar Registro")

        if enviar:
            st.balloons()
            st.success(f"Bem {codigo_patrimonio} registrado na {unidade}!")
