import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA (NOME E ÍCONE) ---
def get_image_as_base64(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# Tenta carregar a logo para o ícone da aba e do atalho
try:
    img_logo = Image.open("logo.png")
    # Técnica para forçar o navegador a reconhecer o ícone novo
    logo_base64 = get_image_as_base64("logo.png")
except:
    img_logo = "🗄️"
    logo_base64 = None

st.set_page_config(
    page_title="Inventory Pro",  # Nome que aparecerá no ícone do smartphone
    page_icon=img_logo,
    layout="centered"
)

# --- 2. CSS PARA APARÊNCIA PROFISSIONAL E REMOVER STREAMLIT ---
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Remove espaço em branco excessivo no topo */
    .block-container {padding-top: 1rem;}
    /* Força o nome no topo da página caso queira reforçar a marca */
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- 3. LÓGICA DO INVENTÁRIO (SESSÃO) ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

def registrar_item():
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
        st.session_state.campo_zebra = "" # Limpa para o próximo bip
        st.toast(f"Código {codigo} salvo!", icon="✅")

# --- 4. INTERFACE ---

# Exibe a logo no topo do app
if logo_base64:
    st.markdown(
        f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="120"></div>',
        unsafe_allow_html=True
    )
else:
    st.title("🗄️ Inventory Pro")

st.markdown("<h1 style='text-align: center;'>Gestão de Patrimônio</h1>", unsafe_allow_html=True)

# Configurações fixas para agilizar o trabalho com o Zebra
with st.expander("⚙️ Configurações do Lote Atual", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.radio("Unidade:", ["Unidade 1", "Unidade 2"], key="unidade_lote", horizontal=True)
        st.selectbox("Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"], key="etiqueta_lote")
    with c2:
        st.text_input("Descrição Padrão:", key="desc_lote", placeholder="Ex: Cadeira Giratória")

st.divider()

# Campo principal para o Leitor Zebra (Simula teclado + Enter)
st.subheader("🔍 Scanner")
st.text_input(
    "Mantenha o cursor aqui para bipar:", 
    key="campo_zebra", 
    on_change=registrar_item, 
    placeholder="Aguardando bip do Zebra..."
)

# --- 5. TABELA E EXPORTAÇÃO ---
if st.session_state['lista_patrimonio']:
    st.write("### 📋 Itens Coletados")
    df = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df, use_container_width=True)
    
    # Gerador de Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Baixar Relatório (Excel)",
        data=output.getvalue(),
        file_name=f"inventario_{datetime.now().strftime('%d%m_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Sidebar
if st.sidebar.button("🗑️ Limpar Tudo"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
