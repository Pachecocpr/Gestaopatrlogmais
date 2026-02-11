import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# =========================================================
# CONFIGURAÇÃO DE UNIDADES - ATUALIZADO
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

OPCOES_ETIQUETA = ["Metal", "Papel"]

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
        # Carrega o Excel garantindo o uso do openpyxl
        df = pd.read_excel("base_patrimonio.xlsx", engine='openpyxl')
        
        # Limpa nomes das colunas
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        df_limpo = pd.DataFrame()

        # Tenta achar o PIB/Patrimônio por NOME ou pela COLUNA B (índice 1)
        try:
            col_pib = [c for c in df.columns if 'patrimonio' in c or 'pib' in c or 'codigo' in c][0]
            df_limpo['pib_ref'] = df[col_pib].astype(str).str.strip()
        except:
            df_limpo['pib_ref'] = df.iloc[:, 1].astype(str).str.strip()

        # Tenta achar a Descrição por NOME ou pela COLUNA C (índice 2)
        try:
            col_desc = [c for c in df.columns if 'descricao' in c or 'bem' in c][0]
            df_limpo['desc_ref'] = df[col_desc].astype(str).str.strip()
        except:
            df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()
            
        return df_limpo
    except Exception as e:
        st.error(f"Erro técnico ao ler a planilha: {e}")
        return None

df_referencia = carregar_base_mestre()

# --- 3. LÓGICA DE REGISTRO (DISPARADA PELO ENTER) ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

def registrar_item():
    # Captura o valor digitado no campo e limpa espaços
    pib_lido = str(st.session_state.campo_zebra).strip()
    
    if pib_lido:
        descricao_final = "NÃO LOCALIZADO"
        
        if df_referencia is not None:
            # Busca exata na base de dados
            resultado = df_referencia[df_referencia['pib_ref'] == pib_lido]
            if not resultado.empty:
                descricao_final = resultado.iloc[0]['desc_ref']
        
        # Salva o registro incluindo Unidade e Etiqueta selecionadas
        st.session_state['lista_patrimonio'].append({
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "PIB/Patrimônio": pib_lido,
            "Descrição": descricao_final,
            "Unidade": st.session_state.unidade_atual,
            "Etiqueta": st.session_state.etiqueta_atual
        })
        
        # Feedback visual
        if descricao_final == "NÃO LOCALIZADO":
            st.toast(f"Código {pib_lido} não encontrado!", icon="⚠️")
        else:
            st.toast(f"✅ {descricao_final}", icon="✔️")
        
        # LIMPA O CAMPO AUTOMATICAMENTE PARA O PRÓXIMO
        st.session_state.campo_zebra = ""

# --- 4. INTERFACE ---
if logo_base64:
    st.markdown(f'<center><img src="data:image/png;base64,{logo_base64}" width="120"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Inventário de Patrimônio</h2>", unsafe_allow_html=True)

# Esconde menus do Streamlit para foco total
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

# Painel de Seleção (Configurações do Lote)
with st.expander("⚙️ Configurações da Unidade e Etiqueta", expanded=True):
    col_unidade, col_etiq = st.columns([2, 1])
    with col_unidade:
        st.selectbox("Unidade Alocada:", options=NOME_DAS_UNIDADES, key="unidade_atual")
    with col_etiq:
        st.radio("Etiqueta:", options=OPCOES_ETIQUETA, key="etiqueta_atual", horizontal=True)

st.divider()

# Scanner
st.subheader("🔍 Scanner / Entrada Manual")
# O parâmetro on_change garante que ao clicar Enter no smartphone o registro seja feito
st.text_input(
    "Aguardando leitura ou digitação (Enter para salvar):", 
    key="campo_zebra", 
    on_change=registrar_item,
    placeholder="Digite o código ou bipe aqui..."
)

# Tabela e Exportação
if st.session_state['lista_patrimonio']:
    st.markdown("### 📋 Itens Coletados")
    df_result = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df_result, use_container_width=True)
    
    # Gerar Excel para download
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Baixar Relatório Excel", 
        data=output.getvalue(), 
        file_name=f"inventario_{datetime.now().strftime('%d%m_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Barra lateral
if st.sidebar.button("🗑️ Limpar Lista Atual"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
