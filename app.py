import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# --- 1. CONFIGURAÇÃO DE IDENTIDADE E LOGO ---
try:
    img_logo = Image.open("logo.png")
    with open("logo.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
except:
    img_logo = "🗄️"
    logo_base64 = None

st.set_page_config(page_title="Inventory Pro", page_icon=img_logo, layout="centered")

# --- 2. CARREGAMENTO DA BASE MESTRE (BUSCA POR POSIÇÃO DE COLUNA) ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Carrega o Excel
        df = pd.read_excel("base_patrimonio.xlsx")
        
        # Limpeza básica: remove linhas totalmente vazias
        df = df.dropna(how='all')
        
        # FORÇAR TRATAMENTO:
        # Coluna 1 (Índice 0): Patrimônio
        # Coluna 3 (Índice 2): Descrição (Conforme você informou)
        
        # Criamos um novo DataFrame padronizado para o sistema não se perder
        df_limpo = pd.DataFrame()
        df_limpo['cod_ref'] = df.iloc[:, 0].astype(str).str.strip() # Primeira coluna
        df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip() # TERCEIRA COLUNA (Índice 2)
        
        return df_limpo
    except Exception as e:
        st.error(f"Erro ao carregar base_patrimonio.xlsx: {e}")
        return None

df_referencia = carregar_base_mestre()

# --- 3. LÓGICA DE REGISTRO ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

def registrar_item():
    # Pega o que foi bipado e limpa espaços
    codigo_lido = str(st.session_state.campo_zebra).strip()
    
    if codigo_lido:
        descricao_final = "NÃO LOCALIZADO"
        
        if df_referencia is not None:
            # Busca o código na coluna 'cod_ref' que criamos
            resultado = df_referencia[df_referencia['cod_ref'] == codigo_lido]
            
            if not resultado.empty:
                descricao_final = resultado.iloc[0]['desc_ref']
        
        # Adiciona à lista de conferência
        st.session_state['lista_patrimonio'].append({
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Patrimônio": codigo_lido,
            "Descrição": descricao_final,
            "Unidade": st.session_state.get('unidade_lote', 'Unidade 1')
        })
        
        # Alerta visual
        if descricao_final == "NÃO LOCALIZADO":
            st.toast(f"Código {codigo_lido} não encontrado!", icon="⚠️")
        else:
            st.toast(f"✅ {descricao_final}", icon="✔️")
        
        # Limpa o campo para o próximo bip
        st.session_state.campo_zebra = ""

# --- 4. INTERFACE ---
if logo_base64:
    st.markdown(f'<center><img src="data:image/png;base64,{logo_base64}" width="120"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Inventário Profissional</h2>", unsafe_allow_html=True)

# Esconde menus do Streamlit
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

# Scanner Input
st.subheader("🔍 Scanner")
st.text_input("Bipe o código aqui:", key="campo_zebra", on_change=registrar_item, placeholder="Aguardando...")

# Tabela e Exportação
if st.session_state['lista_patrimonio']:
    st.markdown("### Itens Lidos")
    df_result = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df_result, use_container_width=True)
    
    # Download Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False)
    st.download_button("📥 Baixar Relatório Excel", output.getvalue(), f"inventario_{datetime.now().strftime('%d%m_%H%M')}.xlsx")

if st.sidebar.button("🗑️ Limpar Tudo"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
