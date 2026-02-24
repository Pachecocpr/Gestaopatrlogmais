import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inventory Pro", page_icon="📦", layout="wide")

# Lista de unidades para a caixa de seleção
NOME_DAS_UNIDADES = [
    "CLI BELO HORIZONTE/DR/MG", 
"CLI TJ MG", 
"CLI SMS CONTAGEM", 
"CLI CONTAGEM", 
"CDIP BELO HORIZONTE", 
"CLI INDAIA", 
"CLI UNIVERSITARIO", 
"CLI MONTES CLAROS", 
"CLI UBERLANDIA", 
"CLI VARGINHA", 
"CLI DEFENSORIA PUBLICA DE MG", 
"CLI EFULFILLMENT EXTREMA", 
"CLI TAPERA", 
"GER REG LOGISTICA/COPER", 
"SUB GEST OPER LOGISTICA/GELOG", 
"SUB PLAN DE LOGISTICA/GELOG", 
"SEC ADMINISTRATIVA/GELOG", 
"CLI ARMAZEM DE RECURSOS"
]

# --- 1. CARREGAMENTO DA BASE MESTRE (COLUNAS B, C, E, F, J) ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Carrega as colunas necessárias: 
        # B=1 (PIB), C=2 (Desc), E=4 (Local), F=5 (Unidade), J=9 (Status)
        df = pd.read_excel("base_patrimonio.xlsx", engine='openpyxl', header=None)
        
        df_limpo = pd.DataFrame()
        df_limpo['pib_ref'] = df.iloc[:, 1].astype(str).str.strip().str.upper()
        df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()
        df_limpo['cod_local_ref'] = df.iloc[:, 4].astype(str).str.strip()
        df_limpo['unidade_ref'] = df.iloc[:, 5].astype(str).str.strip()
        # Adicionando a Coluna J (Índice 9) -> Status
        df_limpo['status_ref'] = df.iloc[:, 9].astype(str).str.strip()
        
        return df_limpo
    except Exception as e:
        st.error(f"Erro ao carregar base_patrimonio.xlsx: {e}")
        return None

df_referencia = carregar_base_mestre()

# Inicializa lista do inventário (Zebra)
if 'lista_inventario' not in st.session_state:
    st.session_state['lista_inventario'] = []

# --- 2. LÓGICA DO INVENTÁRIO (ZEBRA) ---
def registrar_item_zebra():
    pib_lido = str(st.session_state.campo_zebra).strip().upper()
    if pib_lido:
        info = {
            "Descrição": "NÃO LOCALIZADO", 
            "Cód. Local": "---", 
            "Unidade": "---",
            "Status": "---"
        }
        
        if df_referencia is not None:
            res = df_referencia[df_referencia['pib_ref'] == pib_lido]
            if not res.empty:
                info = {
                    "Descrição": res.iloc[0]['desc_ref'], 
                    "Cód. Local": res.iloc[0]['cod_local_ref'], 
                    "Unidade": res.iloc[0]['unidade_ref'],
                    "Status": res.iloc[0]['status_ref']
                }
        
        st.session_state['lista_inventario'].insert(0, {
            "Data/Hora": datetime.now().strftime("%H:%M:%S"),
            "PIB": pib_lido,
            "Descrição": info["Descrição"],
            "Cód. Local": info["Cód. Local"],
            "Unidade Base": info["Unidade"],
            "Status": info["Status"]
        })
        st.session_state.campo_zebra = ""

# --- 3. INTERFACE ---
st.title("📊 Gestão de Patrimônio & Status")

tab1, tab2 = st.tabs(["🔍 Inventário Ativo (Zebra)", "🏢 Relatório por Unidade"])

# --- TAB 1: INVENTÁRIO ATIVO (ZEBRA) ---
with tab1:
    st.subheader("Leitura com Coletor")
    st.text_input("Bipe o item aqui:", key="campo_zebra", on_change=registrar_item_zebra)
    
    if st.session_state['lista_inventario']:
        df_inv = pd.DataFrame(st.session_state['lista_inventario'])
        st.dataframe(df_inv, use_container_width=True)
        
        output_inv = BytesIO()
        with pd.ExcelWriter(output_inv, engine='xlsxwriter') as writer:
            df_inv.to_excel(writer, index=False)
        st.download_button(
            label="📥 Baixar Inventário (Com Status)", 
            data=output_inv.getvalue(), 
            file_name="inventario_zebra_status.xlsx",
            use_container_width=True
        )

# --- TAB 2: RELATÓRIO DA BASE POR UNIDADE (FILTRO DIRETO) ---
with tab2:
    st.subheader("Consulta da Base por Unidade")
    unidade_sel = st.selectbox("Selecione a Unidade:", NOME_DAS_UNIDADES)
    
    if df_referencia is not None:
        # Filtra a base pela unidade selecionada
        df_unidade = df_referencia[df_referencia['unidade_ref'] == unidade_sel]
        
        st.info(f"Encontrados **{len(df_unidade)}** itens em **{unidade_sel}**")
        
        # Ajustando nomes das colunas para exibição amigável
        df_display = df_unidade.copy()
        df_display.columns = ['PIB', 'Descrição', 'Cód. Local', 'Unidade', 'Status']
        
        st.dataframe(df_display, use_container_width=True)
        
        if not df_display.empty:
            output_uni = BytesIO()
            with pd.ExcelWriter(output_uni, engine='xlsxwriter') as writer:
                df_display.to_excel(writer, index=False)
            
            st.download_button(
                label=f"📥 Baixar Relatório Completo: {unidade_sel}",
                data=output_uni.getvalue(),
                file_name=f"base_{unidade_sel.replace(' ', '_')}_status.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# --- SIDEBAR: LIMPEZA ---
if st.sidebar.button("🗑️ Limpar Inventário (Zebra)"):
    st.session_state['lista_inventario'] = []
    st.rerun()
