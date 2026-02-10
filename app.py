import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA (Ícone de móvel e Nome Personalizado)
st.set_page_config(
    page_title="Gestão de Patrimônios", 
    page_icon="🗄️", 
    layout="centered"
)

# 2. CSS PARA ESCONDER MENUS E RODAPÉ (Aparência Profissional)
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# Inicializa a lista de registros
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# 3. FUNÇÃO DE SALVAMENTO AUTOMÁTICO (Gatilho pelo Enter do Zebra)
def registrar_e_limpar():
    codigo = st.session_state.campo_zebra
    if codigo:
        novo_item = {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Código": codigo,
            "Unidade": st.session_state.get('unidade_lote', 'Unidade 1'),
            "Descrição": st.session_state.get('desc_lote', ''),
            "Etiqueta": st.session_state.get('etiqueta_lote', 'Metal')
        }
        st.session_state['lista_patrimonio'].append(novo_item)
        # Limpa o campo instantaneamente para o próximo bip
        st.session_state.campo_zebra = ""
        st.toast(f"Item {codigo} registrado!", icon="✅")

# --- INTERFACE DO USUÁRIO ---
st.title("🗄️ Inventário de Patrimônio")

# Configurações de Lote (Defina uma vez e saia bipando)
with st.expander("⚙️ Configurações do Lote", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.radio("Unidade:", ["Unidade 1", "Unidade 2"], key="unidade_lote", horizontal=True)
        st.selectbox("Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"], key="etiqueta_lote")
    with c2:
        st.text_input("Descrição do Item:", key="desc_lote", placeholder="Ex: Armário de Aço")

st.divider()

# Campo de Entrada (Foco do Leitor Zebra)
st.subheader("🔍 Entrada do Leitor")
st.text_input(
    "Aguardando Bip do Zebra...", 
    key="campo_zebra", 
    on_change=registrar_e_limpar, 
    placeholder="O cursor deve estar aqui para bipar"
)

# --- TABELA E EXPORTAÇÃO ---
if st.session_state['lista_patrimonio']:
    st.markdown("### 📋 Itens Registrados")
    df = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df, use_container_width=True)
    
    # Botão de Download Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Baixar Relatório Excel",
        data=output.getvalue(),
        file_name=f"inventario_{datetime.now().strftime('%d_%m_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Sidebar para funções de limpeza
if st.sidebar.button("🗑️ Reiniciar Lista"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
