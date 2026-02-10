import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image

# 1. CONFIGURAÇÃO DA PÁGINA E IDENTIDADE VISUAL
try:
    img_logo = Image.open("logo.png")
except:
    # Caso a imagem ainda não tenha sido enviada ao GitHub, usa um ícone reserva
    img_logo = "🗄️"

st.set_page_config(
    page_title="Inventory Pro",
    page_icon=img_logo,
    layout="centered"
)

# 2. CSS PARA OCULTAR ELEMENTOS PADRÃO DO STREAMLIT
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Ajuste para remover espaços em branco no topo */
    .block-container {padding-top: 2rem;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# 3. INICIALIZAÇÃO DO ESTADO DA SESSÃO
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# 4. FUNÇÃO DE REGISTRO AUTOMÁTICO (Gatilho pelo Enter do Zebra)
def registrar_item():
    codigo = st.session_state.campo_zebra
    if codigo:
        # Captura os dados atuais dos seletores
        novo_registro = {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Código": codigo,
            "Unidade": st.session_state.get('unidade_lote', 'Unidade 1'),
            "Descrição": st.session_state.get('desc_lote', ''),
            "Tipo Etiqueta": st.session_state.get('etiqueta_lote', 'Metal')
        }
        # Adiciona à lista
        st.session_state['lista_patrimonio'].append(novo_registro)
        # Limpa o campo de texto para a próxima leitura
        st.session_state.campo_zebra = ""
        st.toast(f"Item {codigo} registrado!", icon="✅")

# --- INTERFACE ---

# Exibição da Logo
st.image(img_logo, width=150)
st.title("Sistema de Inventário")

# Configurações do Lote Atual
with st.expander("⚙️ Configurações do Lote (Fixas por Bip)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.radio("Unidade:", ["Unidade 1", "Unidade 2"], key="unidade_lote", horizontal=True)
        st.selectbox("Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"], key="etiqueta_lote")
    with col2:
        st.text_input("Descrição Padrão:", key="desc_lote", placeholder="Ex: Armário de Aço")

st.divider()

# Campo de entrada focado para o Leitor Zebra
st.subheader("🔍 Scanner")
st.info("Mantenha o cursor piscando abaixo e use o leitor.")

st.text_input(
    "Aguardando leitura...", 
    key="campo_zebra", 
    on_change=registrar_item, # O 'Enter' do Zebra dispara esta função
    placeholder="Bipe o código de barras aqui"
)

# --- VISUALIZAÇÃO E EXPORTAÇÃO ---

if st.session_state['lista_patrimonio']:
    st.markdown("---")
    st.subheader("📋 Itens Escaneados")
    
    # Exibe a tabela atualizada
    df = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df, use_container_width=True)
    
    # Preparação do arquivo Excel para Download
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    
    st.download_button(
        label="📥 Baixar Relatório (Excel)",
        data=buffer.getvalue(),
        file_name=f"inventario_{datetime.now().strftime('%d%m_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Botão de Reset na Barra Lateral
if st.sidebar.button("🗑️ Limpar Lista Completa"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
