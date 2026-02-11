import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# =========================================================
# CONFIGURAÇÃO DE UNIDADES - SUBSTITUA PELOS NOMES REAIS
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

# --- 2. CARREGAMENTO DA BASE MESTRE (BUSCA B vs C) ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Lê o arquivo Excel
        df = pd.read_excel("base_patrimonio.xlsx")
        
        # Cria um DataFrame de busca limpo:
        # Coluna B (Índice 1) = Patrimônio/PIB
        # Coluna C (Índice 2) = Descrição do Bem
        df_limpo = pd.DataFrame()
        df_limpo['pib_ref'] = df.iloc[:, 1].astype(str).str.strip()
        df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()
        
        return df_limpo
    except Exception as e:
        st.error(f"Erro ao ler colunas B e C: {e}")
        return None

df_referencia = carregar_base_mestre()

# --- 3. LÓGICA DE REGISTRO ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

def registrar_item():
    pib_lido = str(st.session_state.campo_zebra).strip()
    
    if pib_lido:
        descricao_final = "ITEM NÃO ENCONTRADO NA BASE"
        
        if df_referencia is not None:
            # Busca o PIB lido na coluna de referência (Coluna B)
            resultado = df_referencia[df_referencia['pib_ref'] == pib_lido]
            
            if not resultado.empty:
                # Se achou, pega a descrição correspondente (Coluna C)
                descricao_final = resultado.iloc[0]['desc_ref']
        
        # Adiciona o registro à lista
        st.session_state['lista_patrimonio'].append({
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "PIB/Patrimônio": pib_lido,
            "Descrição": descricao_final,
            "Unidade": st.session_state.unidade_atual
        })
        
        # Alerta visual para o usuário
        if "NÃO ENCONTRADO" in descricao_final:
            st.toast(f"Código {pib_lido} não consta na base!", icon="⚠️")
        else:
            st.toast(f"✅ {descricao_final}", icon="✔️")
        
        # Limpa o campo para o próximo bip
        st.session_state.campo_zebra = ""

# --- 4. INTERFACE ---
if logo_base64:
    st.markdown(f'<center><img src="data:image/png;base64,{logo_base64}" width="120"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Inventário de Patrimônio</h2>", unsafe_allow_html=True)

# Esconde elementos do Streamlit para parecer App
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

# Seleção de Unidade
with st.expander("📍 Localização da Coleta", expanded=True):
    st.selectbox("Selecione a Unidade:", options=NOME_DAS_UNIDADES, key="unidade_atual")

st.divider()

# Scanner Input
st.subheader("🔍 Scanner Zebra")
st.text_input(
    "Clique aqui e comece a bipar:", 
    key="campo_zebra", 
    on_change=registrar_item, 
    placeholder="Aguardando PIB..."
)

# --- 5. TABELA E EXPORTAÇÃO ---
if st.session_state['lista_patrimonio']:
    st.markdown("### 📋 Resumo da Coleta")
    df_result = pd.DataFrame(st.session_state['lista_patrimonio'])
    
    # Exibe tabela formatada
    st.dataframe(df_result, use_container_width=True)
    
    # Botão de Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Baixar Relatório (Excel)", 
        data=output.getvalue(), 
        file_name=f"inventario_{st.session_state.unidade_atual}_{datetime.now().strftime('%d%m')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if st.sidebar.button("🗑️ Limpar Tudo"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
