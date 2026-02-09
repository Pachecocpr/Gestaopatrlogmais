import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Patrimônio Logística", page_icon="📦", layout="centered")

# Inicializa a memória do app (Session State)
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

st.title("📦 Gestão de Patrimônio")
st.write("Versão otimizada para Leitores Zebra e Apps de Scanner (Keyboard Wedge).")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Painel de Controle")
if st.sidebar.button("🗑️ Limpar Lista Atual"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()

# --- ENTRADA DE DADOS ---
st.subheader("🔍 Escanear Item")
# O cursor deve estar focado aqui para o scanner funcionar
codigo_final = st.text_input("Clique aqui e bibe o código:", key="entrada_scanner", placeholder="Aguardando bip...")

if codigo_final:
    st.success(f"✅ Item identificado: **{codigo_final}**")
    
    # Formulário de detalhes (limpa após salvar)
    with st.form("registro_patrimonio", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            unidade = st.radio("Unidade:", ["Unidade 1", "Unidade 2"])
            etiqueta = st.selectbox("Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"])
        
        with col2:
            descricao = st.text_input("Descrição (Ex: Notebook, Cadeira):")
            obs = st.text_input("Observações:")

        if st.form_submit_button("💾 Salvar Registro"):
            novo_item = {
                "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Patrimônio": codigo_final,
                "Descrição": descricao,
                "Unidade": unidade,
                "Etiqueta": etiqueta,
                "Observação": obs
            }
            st.session_state['lista_patrimonio'].append(novo_item)
            st.toast("Salvo com sucesso!", icon="✔️")
            # Força o foco de volta para o campo de scan (limpando o código anterior)
            st.info("Pronto para o próximo bip!")

# --- VISUALIZAÇÃO E DOWNLOAD ---
if st.session_state['lista_patrimonio']:
    st.divider()
    st.subheader("📋 Itens na Lista")
    
    df_resultado = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df_resultado, use_container_width=True)

    # Geração do arquivo Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_resultado.to_excel(writer, index=False, sheet_name='Patrimonio')
    
    st.download_button(
        label="📥 Baixar Relatório (Excel)",
        data=buffer.getvalue(),
        file_name=f"patrimonio_{datetime.now().strftime('%d_%m_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
