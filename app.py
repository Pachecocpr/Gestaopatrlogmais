import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from pyzbar.pyzbar import decode
from PIL import Image
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Patrimônio Logística", page_icon="📦", layout="wide")

# Inicializa a memória do app (Session State)
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

st.title("📦 Gestão de Patrimônio Unificado")
st.markdown("---")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Painel de Controle")
if st.sidebar.button("🗑️ Limpar Lista Atual"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()

# --- MÉTODO DE LEITURA ---
st.subheader("🔍 Identificação do Item")
metodo = st.radio("Selecione o dispositivo de entrada:", 
                  ["Leitor Zebra (Teclado)", "Câmera do Smartphone (Scan)"], 
                  horizontal=True)

codigo_final = ""

if metodo == "Leitor Zebra (Teclado)":
    # O Zebra digita automaticamente aqui ao bipar
    codigo_final = st.text_input("Aguardando bip do leitor...", key="zebra_in", placeholder="Clique aqui antes de bipar")
else:
    foto = st.camera_input("Tire uma foto nítida do código de barras")
    if foto:
        with st.spinner('Escaneando imagem...'):
            img_pil = Image.open(foto)
            # Decodifica o código de barras da foto
            scan_resultado = decode(img_pil)
            
            if scan_resultado:
                codigo_final = scan_resultado[0].data.decode('utf-8')
                st.success(f"✅ Código detectado via Câmera: {codigo_final}")
            else:
                st.error("❌ Não foi possível ler o código na foto. Tente focar melhor ou limpar a lente.")

# --- FORMULÁRIO DE REGISTRO ---
if codigo_final:
    st.markdown(f"### 📋 Detalhes do Bem: `{codigo_final}`")
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            unidade = st.selectbox("Localização:", ["Unidade 1", "Unidade 2"])
            etiqueta = st.selectbox("Tipo de Etiqueta:", ["Metal (Patrimonial)", "Papel (Comum)", "Poliéster"])
        
        with col2:
            descricao = st.text_input("Descrição do Bem:", placeholder="Ex: Paleteira Elétrica")
            obs = st.text_input("Observações:")

        salvar = st.form_submit_button("💾 Salvar Registro")

        if salvar:
            # Adiciona os dados na memória
            novo_item = {
                "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Patrimônio": codigo_final,
                "Descrição": descricao,
                "Unidade": unidade,
                "Tipo Etiqueta": etiqueta,
                "Observação": obs
            }
            st.session_state['lista_patrimonio'].append(novo_item)
            st.toast(f"Item {codigo_final} salvo!", icon='✅')

# --- EXIBIÇÃO E DOWNLOAD ---
if st.session_state['lista_patrimonio']:
    st.markdown("---")
    st.subheader("📋 Itens Registrados (Sessão Atual)")
    
    df_resultado = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df_resultado, use_container_width=True)

    # Geração do arquivo Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_resultado.to_excel(writer, index=False, sheet_name='Patrimonio')
    
    st.download_button(
        label="📥 Baixar Relatório em Excel",
        data=buffer.getvalue(),
        file_name=f"patrimonio_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Nenhum item registrado até o momento. Utilize o leitor ou a câmera acima.")
