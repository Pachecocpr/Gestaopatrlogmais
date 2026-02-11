import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# =========================================================
# CONFIGURAÇÃO DE UNIDADES - EDITE AQUI
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

# --- 1. CONFIGURAÇÃO DE IDENTIDADE ---
try:
    img_logo = Image.open("logo.png")
    with open("logo.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
except:
    img_logo = "🗄️"
    logo_base64 = None

st.set_page_config(page_title="Inventory Pro", page_icon=img_logo, layout="centered")

# --- 2. CARREGAMENTO DA BASE MESTRE (BUSCA INTELIGENTE) ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Carrega o Excel ignorando linhas vazias
        df = pd.read_excel("base_patrimonio.xlsx")
        
        # Limpa nomes das colunas (remove espaços e converte para minúsculas)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        df_limpo = pd.DataFrame()

        # Tenta achar por NOME primeiro, se falhar, usa a POSIÇÃO (B e C)
        # Coluna B é o índice 1 | Coluna C é o índice 2
        try:
            # Tenta encontrar colunas que contenham 'patrimonio', 'pib' ou 'codigo'
            col_pib = [c for c in df.columns if 'patrimonio' in c or 'pib' in c or 'codigo' in c][0]
            df_limpo['pib_ref'] = df[col_pib].astype(str).str.strip()
        except:
            # Se não achar pelo nome, pega a COLUNA B (índice 1)
            df_limpo['pib_ref'] = df.iloc[:, 1].astype(str).str.strip()

        try:
            # Tenta encontrar colunas que contenham 'descricao' ou 'bem'
            col_desc = [c for c in df.columns if 'descricao' in c or 'bem' in c][0]
            df_limpo['desc_ref'] = df[col_desc].astype(str).str.strip()
        except:
            # Se não achar pelo nome, pega a COLUNA C (índice 2)
            df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()
            
        return df_limpo
    except Exception as e:
        # Exibe o erro real na tela para sabermos o que é
        st.error(f"Erro técnico ao ler a planilha: {e}")
        return None

df_referencia = carregar_base_mestre()

# --- 3. LÓGICA DE REGISTRO ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

def registrar_item():
    pib_lido = str(st.session_state.campo_zebra).strip()
    
    if pib_lido:
        descricao_final = "NÃO LOCALIZADO"
        
        if df_referencia is not None:
            # Busca o código lido na coluna de referência
            resultado = df_referencia[df_referencia['pib_ref'] == pib_lido]
            
            if not resultado.empty:
                descricao_final = resultado.iloc[0]['desc_ref']
        
        st.session_state['lista_patrimonio'].append({
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "PIB/Patrimônio": pib_lido,
            "Descrição": descricao_final,
            "Unidade": st.session_state.unidade_atual
        })
        
        if descricao_final == "NÃO LOCALIZADO":
            st.toast(f"Código {pib_lido} não encontrado!", icon="⚠️")
        else:
            st.toast(f"✅ {descricao_final}", icon="✔️")
        
        st.session_state.campo_zebra = ""

# --- 4. INTERFACE ---
if logo_base64:
    st.markdown(f'<center><img src="data:image/png;base64,{logo_base64}" width="120"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Inventário de Patrimônio</h2>", unsafe_allow_html=True)

# Esconde menus do Streamlit
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

# Painel de Seleção
with st.expander("📍 Unidade de Coleta", expanded=True):
    st.selectbox("Selecione o Local:", options=NOME_DAS_UNIDADES, key="unidade_atual")

st.divider()

# Scanner
st.subheader("🔍 Scanner Zebra")
st.text_input("Bipe o código:", key="campo_zebra", on_change=registrar_item)

# Tabela e Exportação
if st.session_state['lista_patrimonio']:
    df_result = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df_result, use_container_width=True)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False)
    st.download_button("📥 Baixar Excel", output.getvalue(), f"inventario_{datetime.now().strftime('%d%m')}.xlsx")

if st.sidebar.button("🗑️ Limpar Lista"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
