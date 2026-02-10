import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image

# 1. CONFIGURAÇÃO DA PÁGINA (Ícone e Nome que aparecerão no Smartphone)
# Esta deve ser a PRIMEIRA linha de comando Streamlit
try:
    img_logo = Image.open("logo.png")
except:
    # Caso a imagem não seja encontrada no GitHub, usa um emoji como fallback
    img_logo = "🗄️"

st.set_page_config(
    page_title="Inventory Pro", # Nome que aparecerá no atalho do celular
    page_icon=img_logo,          # Ícone que aparecerá no atalho do celular
    layout="centered"
)

# 2. DESIGN PROFISSIONAL (Esconde menus padrão do Streamlit)
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Ajuste de margem superior para a logo */
    .block-container {padding-top: 1rem;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 3. LÓGICA DE DADOS (Session State)
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# 4. FUNÇÃO PARA SALVAR E LIMPAR (Otimizado para Leitor Zebra)
def registrar_e_limpar():
    codigo = st.session_state.campo_zebra
    if codigo:
        # Cria o dicionário com os dados
        novo_item = {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Código": codigo,
            "Unidade": st.session_state.get('unidade_lote', 'Unidade 1'),
            "Descrição": st.session_state.get('desc_lote', ''),
            "Etiqueta": st.session_state.get('etiqueta_lote', 'Metal')
        }
        # Salva na lista
        st.session_state['lista_patrimonio'].append(novo_item)
        # Limpa o campo de entrada para o próximo bip
        st.session_state.campo_zebra = ""
        st.toast(f"Código {codigo} registrado!", icon="✅")

# --- INTERFACE VISUAL ---

# Exibição da Logo no topo
st.image(img_logo, width=120)
st.title("Sistema de Inventário")

# Painel de Configurações (Lote)
with st.expander("⚙️ Configurações do Lote Atual", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.radio("Unidade:", ["Unidade 1", "Unidade 2"], key="unidade_lote", horizontal=True)
        st.selectbox("Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"], key="etiqueta_lote")
    with col2:
        st.text_input("Descrição Padrão:", key="desc_lote", placeholder="Ex: Armário de Aço")

st.divider()

# Campo de Leitura (Foco do Zebra)
st.subheader("🔍 Entrada do Leitor Zebra")
st.text_input(
    "Clique aqui antes de começar a bipar:", 
    key="campo_zebra", 
    on_change=registrar_e_limpar, # Ativa o salvamento automático ao receber o 'Enter' do leitor
    placeholder="Aguardando bip..."
)

# --- TABELA E DOWNLOAD ---
if st.session_state['lista_patrimonio']:
    st.markdown("### 📋 Itens Registrados")
    df = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df, use_container_width=True)
    
    # Exportação para Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Baixar Relatório Excel",
        data=output.getvalue(),
        file_name=f"inventario_zebra_{datetime.now().strftime('%d%m_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Opção para resetar a lista na barra lateral
if st.sidebar.button("🗑️ Reiniciar Lista"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
