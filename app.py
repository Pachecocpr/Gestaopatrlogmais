import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Patrimônio Logística", layout="centered")

# Inicializa a lista na memória
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

st.title("📦 Gestão de Patrimônio")
st.info("Para usar no celular: Ative o 'Modo Teclado' no app Binary Eye.")

# --- ENTRADA DE DADOS ---
st.subheader("🔍 Escanear Item")
# O segredo é clicar neste campo antes de bipar
codigo_lido = st.text_input("Clique aqui e use o scanner:", key="input_scan")

if codigo_lido:
    st.success(f"✅ Identificado: **{codigo_lido}**")
    
    with st.form("cad_patrimonio", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            unidade = st.radio("Unidade:", ["Unidade 1", "Unidade 2"])
            etiqueta = st.selectbox("Etiqueta:", ["Metal", "Papel", "Poliéster"])
        with col2:
            desc = st.text_input("Descrição do Bem:")
            obs = st.text_input("Observações:")
        
        if st.form_submit_button("💾 Salvar Registro"):
            st.session_state['lista_patrimonio'].append({
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Código": codigo_lido,
                "Descrição": desc,
                "Unidade": unidade,
                "Etiqueta": etiqueta,
                "Obs": obs
            })
            st.toast("Salvo!")

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
