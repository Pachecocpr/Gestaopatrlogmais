import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from pyzbar.pyzbar import decode # Biblioteca que lê o código
from PIL import Image

st.set_page_config(page_title="Patrimônio Logística", layout="centered")

if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

st.title("📦 Gestão de Patrimônio")

# --- OPÇÃO DE ENTRADA ---
metodo = st.radio("Escolha como ler o código:", ["Digitar/Zebra", "Usar Câmera do Celular"], horizontal=True)

codigo_final = ""

if metodo == "Digitar/Zebra":
    codigo_final = st.text_input("Aguardando código:", key="txt_input")
else:
    # Este botão abre a câmera direto no navegador
    foto = st.camera_input("Aponte para o código de barras")
    if foto:
        img = Image.open(foto)
        resultado = decode(img) # Tenta ler o código na foto
        if resultado:
            codigo_final = resultado[0].data.decode('utf-8')
            st.success(f"✅ Código Lido: {codigo_final}")
        else:
            st.error("❌ Não foi possível ler. Tente focar melhor ou limpar a lente.")

# --- FORMULÁRIO ---
if codigo_final:
    with st.form("cad_patrimonio", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            unidade = st.radio("Unidade:", ["Unidade 1", "Unidade 2"])
            etiqueta = st.selectbox("Etiqueta:", ["Metal", "Papel", "Poliéster"])
        with col2:
            desc = st.text_input("Descrição:")
            obs = st.text_input("Obs:")
        
        if st.form_submit_button("💾 Salvar"):
            st.session_state['lista_patrimonio'].append({
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Código": codigo_final,
                "Descrição": desc,
                "Unidade": unidade,
                "Etiqueta": etiqueta
            })
            st.toast("Registrado!")

# --- EXCEL ---
if st.session_state['lista_patrimonio']:
    df = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df, use_container_width=True)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 Baixar Excel", output.getvalue(), "patrimonio.xlsx")
