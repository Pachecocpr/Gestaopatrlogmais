import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA E IDENTIDADE ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    img_logo = Image.open("logo.png")
    logo_base64 = get_base64_of_bin_file("logo.png")
except:
    img_logo = "🗄️"
    logo_base64 = None

st.set_page_config(
    page_title="Inventory Pro",
    page_icon=img_logo,
    layout="centered"
)

# --- 2. CSS PARA APARÊNCIA DE APP NATIVO ---
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- 3. CARREGAMENTO DA BASE MESTRE (PROCV) ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Tenta ler o arquivo que você subiu no GitHub
        df = pd.read_excel("base_patrimonio.xlsx")
        # Padroniza as colunas para evitar erro de espaço ou maiúsculas
        df.columns = [str(c).strip().title() for c in df.columns]
        # Converte a coluna Patrimonio para string para busca exata
        if 'Patrimonio' in df.columns:
            df['Patrimonio'] = df['Patrimonio'].astype(str).str.strip()
        return df
    except Exception as e:
        return None

df_referencia = carregar_base_mestre()

# --- 4. LÓGICA DE REGISTRO E BUSCA ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

def registrar_e_buscar():
    codigo_lido = st.session_state.campo_zebra.strip()
    
    if codigo_lido:
        descricao_encontrada = "NÃO LOCALIZADO NA BASE"
        
        # Realiza a busca na base mestre (VLOOKUP / PROCV)
        if df_referencia is not None and 'Patrimonio' in df_referencia.columns:
            # Busca o código na coluna 'Patrimonio'
            match = df_referencia[df_referencia['Patrimonio'] == codigo_lido]
            if not match.empty:
                # Pega a descrição da coluna 'Descricao' (ou a segunda coluna disponível)
                col_desc = 'Descricao' if 'Descricao' in df_referencia.columns else df_referencia.columns[1]
                descricao_encontrada = match.iloc[0][col_desc]

        # Cria o registro para o relatório final
        novo_item = {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Patrimônio": codigo_lido,
            "Descrição Original": descricao_encontrada,
            "Unidade": st.session_state.get('unidade_lote', 'Unidade 1'),
            "Observação": st.session_state.get('obs_lote', '')
        }
        
        st.session_state['lista_patrimonio'].append(novo_item)
        
        # Feedback visual
        if "NÃO LOCALIZADO" in descricao_encontrada:
            st.toast(f"Código {codigo_lido} não cadastrado!", icon="⚠️")
        else:
            st.toast(f"✅ {descricao_encontrada}", icon="✔")
            
        # Limpa o campo para o próximo bip do Zebra
        st.session_state.campo_zebra = ""

# --- 5. INTERFACE DO USUÁRIO ---

# Exibição da Logo
if logo_base64:
    st.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="data:image/png;base64,{logo_base64}" width="130">'
        f'</div>', 
        unsafe_allow_html=True
    )
else:
    st.title("🗄️ Inventory Pro")

st.markdown("<h2 style='text-align: center;'>Inventário Inteligente</h2>", unsafe_allow_html=True)

# Status da Base de Dados
if df_referencia is not None:
    st.caption(f"🟢 Base mestre conectada: {len(df_referencia)} itens carregados.")
else:
    st.error("🔴 Arquivo 'base_patrimonio.xlsx' não encontrado no GitHub.")

# Configurações do Lote
with st.expander("⚙️ Configurações do Lote", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.radio("Unidade Atual:", ["Unidade 1", "Unidade 2"], key="unidade_lote", horizontal=True)
    with c2:
        st.text_input("Nota/Observação:", key="obs_lote", placeholder="Ex: Sala 202")

st.divider()

# Campo de Entrada focado para o Zebra
st.subheader("🔍 Scanner")
st.text_input(
    "Aguardando leitura do patrimônio...", 
    key="campo_zebra", 
    on_change=registrar_e_buscar, 
    placeholder="Bipe com o Zebra aqui"
)

# --- 6. TABELA E EXPORTAÇÃO ---
if st.session_state['lista_patrimonio']:
    st.markdown("### 📋 Itens Coletados")
    df_final = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df_final, use_container_width=True)
    
    # Preparar Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Inventario')
    
    st.download_button(
        label="📥 Baixar Relatório Conferido (Excel)",
        data=output.getvalue(),
        file_name=f"conferencia_{datetime.now().strftime('%d%m_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Sidebar
if st.sidebar.button("🗑️ Limpar Lista Atual"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
