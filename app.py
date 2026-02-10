import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# --- 1. CONFIGURAÇÕES TÉCNICAS DE ÍCONE E NOME ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Tenta carregar a imagem para o Favicon e para o Atalho
try:
    img_logo = Image.open("logo.png")
    logo_base64 = get_base64_of_bin_file("logo.png")
except:
    img_logo = "🗄️"
    logo_base64 = None

# Configuração da página (Primeiro comando Streamlit)
st.set_page_config(
    page_title="Inventory Pro", # Nome que aparecerá no ícone do smartphone
    page_icon=img_logo,
    layout="centered"
)

# --- 2. CSS PARA OCULTAR O STREAMLIT E FORÇAR IDENTIDADE ---
# Injeta o ícone diretamente no HTML para forçar o Android a reconhecer
if logo_base64:
    icon_tag = f'<link rel="shortcut icon" href="data:image/png;base64,{logo_base64}">'
    st.markdown(icon_tag, unsafe_allow_html=True)

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {padding-top: 1rem;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 3. LÓGICA DE DADOS (SESSION STATE) ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# Função que o Leitor Zebra aciona ao dar "Enter"
def registrar_item():
    codigo = st.session_state.campo_scanner
    if codigo:
        registro = {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Código": codigo,
            "Unidade": st.session_state.get('unidade_lote', 'Unidade 1'),
            "Descrição": st.session_state.get('desc_lote', ''),
            "Etiqueta": st.session_state.get('etiqueta_lote', 'Metal')
        }
        st.session_state['lista_patrimonio'].append(registro)
        st.session_state.campo_scanner = "" # Limpa o campo para o próximo bip
        st.toast(f"Código {codigo} salvo!", icon="✅")

# --- 4. INTERFACE DO USUÁRIO ---

# Exibição da Logo centralizada
if logo_base64:
    st.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="data:image/png;base64,{logo_base64}" width="120">'
        f'</div>', 
        unsafe_allow_html=True
    )
else:
    st.title("🗄️ Inventory Pro")

st.markdown("<h2 style='text-align: center;'>Controle de Patrimônio</h2>", unsafe_allow_html=True)

# Configurações do Lote (Fixas para vários bips)
with st.expander("⚙️ Configurações do Lote", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.radio("Unidade:", ["Unidade 1", "Unidade 2"], key="unidade_lote", horizontal=True)
        st.selectbox("Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"], key="etiqueta_lote")
    with col2:
        st.text_input("Descrição Padrão:", key="desc_lote", placeholder="Ex: Cadeira")

st.divider()

# Campo focado para o Leitor Zebra
st.subheader("🔍 Scanner")
st.text_input(
    "Mantenha o cursor aqui para bipar:", 
    key="campo_scanner", 
    on_change=registrar_item, # Dispara ao receber o Enter do Zebra
    placeholder="Aguardando bip..."
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
        label="📥 Baixar Excel",
        data=output.getvalue(),
        file_name=f"inventario_{datetime.now().strftime('%d%m_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Sidebar
if st.sidebar.button("🗑️ Reiniciar Lista"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
