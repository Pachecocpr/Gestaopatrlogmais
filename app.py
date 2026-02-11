import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# =========================================================
# CONFIGURAÇÃO DE UNIDADES - EDITE OS NOMES ABAIXO
# =========================================================
NOME_DAS_UNIDADES = [
    "CLI-CONTAGEM BH",
    "CLI-CONTAGEM CTG",
    "CLI-TAPERA",
    "CLI-ARO",
    "CLI-UNIVERSITÁRIO",
    "CLI-DEFENSORIA PÚBLICA",
    "CLI-TJ",
    "CLI-INDAIA",
    "CEDIP",
    "GELOG-MG",
    "CLI-CAIXA"
]
# =========================================================

# --- 1. CONFIGURAÇÃO DE IDENTIDADE E LOGO ---
try:
    img_logo = Image.open("logo.png")
    with open("logo.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
except:
    img_logo = "🗄️"
    logo_base64 = None

st.set_page_config(page_title="Inventory Pro", page_icon=img_logo, layout="centered")

# --- 2. CARREGAMENTO DA BASE MESTRE ---
@st.cache_data
def carregar_base_mestre():
    try:
        df = pd.read_excel("base_patrimonio.xlsx")
        df_limpo = pd.DataFrame()
        # Coluna 1: Código | Coluna 3: Descrição
        df_limpo['cod_ref'] = df.iloc[:, 0].astype(str).str.strip()
        df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()
        return df_limpo
    except:
        return None

df_referencia = carregar_base_mestre()

# --- 3. LÓGICA DE REGISTRO ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

def registrar_item():
    codigo_lido = str(st.session_state.campo_zebra).strip()
    
    if codigo_lido:
        descricao_final = "NÃO LOCALIZADO"
        if df_referencia is not None:
            resultado = df_referencia[df_referencia['cod_ref'] == codigo_lido]
            if not resultado.empty:
                descricao_final = resultado.iloc[0]['desc_ref']
        
        st.session_state['lista_patrimonio'].append({
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Patrimônio": codigo_lido,
            "Descrição": descricao_final,
            "Unidade": st.session_state.unidade_atual # Salva o nome real da unidade
        })
        
        if descricao_final == "NÃO LOCALIZADO":
            st.toast(f"Código {codigo_lido} não encontrado!", icon="⚠️")
        else:
            st.toast(f"✅ {descricao_final}", icon="✔️")
        
        st.session_state.campo_zebra = ""

# --- 4. INTERFACE ---
if logo_base64:
    st.markdown(f'<center><img src="data:image/png;base64,{logo_base64}" width="120"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Inventário por Gerência</h2>", unsafe_allow_html=True)

# Esconde menus do Streamlit
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

# Painel de Seleção de Unidades Reais
with st.expander("📍 Selecione o Local da Coleta", expanded=True):
    st.selectbox(
        "Unidade Responsável:",
        options=NOME_DAS_UNIDADES,
        key="unidade_atual"
    )

st.divider()

# Scanner Input
st.subheader("🔍 Scanner Zebra")
st.text_input("Bipe o código aqui:", key="campo_zebra", on_change=registrar_item, placeholder="Aguardando bip...")

# Tabela e Exportação
if st.session_state['lista_patrimonio']:
    st.markdown("### Itens Lidos")
    df_result = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df_result, use_container_width=True)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False)
    st.download_button("📥 Baixar Relatório das Unidades", output.getvalue(), f"inventario_unidades_{datetime.now().strftime('%d%m')}.xlsx")

if st.sidebar.button("🗑️ Limpar Lista"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
