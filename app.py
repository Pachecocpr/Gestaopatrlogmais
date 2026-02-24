import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inventory Pro", page_icon="📦", layout="wide")

# Lista de unidades para a caixa de seleção (conforme seu primeiro código)
NOME_DAS_UNIDADES = [
    " ", "CLI EFULFILLMENT EXTREMA", 
"CLI CONTAGEM", "CLI BELO HORIZONTE/DR/MG", 
"CLI TAPERA", "CLI ARMAZEM RECURSO",
    "CLI UNIVERSITARIO", "CLI DEFENSORIA PUBLICA DE MG", 
"CLI TJ MG", "GELOG MG",
    "CLI INDAIA", "CEDIP", "GELOG MG", 
"CLI CAIXA ECONOMICA FEDERAL"
]

# --- 1. CARREGAMENTO DA BASE MESTRE ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Carrega colunas B(1), C(2), E(4) e F(5)
        df = pd.read_excel("base_patrimonio.xlsx", engine='openpyxl', header=None)
        df_limpo = pd.DataFrame()
        df_limpo['pib_ref'] = df.iloc[:, 1].astype(str).str.strip().str.upper()
        df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()
        df_limpo['cod_local_ref'] = df.iloc[:, 4].astype(str).str.strip()
        df_limpo['unidade_ref'] = df.iloc[:, 5].astype(str).str.strip()
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
        info = {"Descrição": "NÃO LOCALIZADO", "Cód. Local": "---", "Unidade": "---"}
        if df_referencia is not None:
            res = df_referencia[df_referencia['pib_ref'] == pib_lido]
            if not res.empty:
                info = {"Descrição": res.iloc[0]['desc_ref'], 
                        "Cód. Local": res.iloc[0]['cod_local_ref'], 
                        "Unidade": res.iloc[0]['unidade_ref']}
        
        st.session_state['lista_inventario'].insert(0, {
            "Data/Hora": datetime.now().strftime("%H:%M:%S"),
            "PIB": pib_lido,
            "Descrição": info["Descrição"],
            "Cód. Local": info["Cód. Local"],
            "Unidade Base": info["Unidade"]
        })
        st.session_state.campo_zebra = ""

# --- 3. INTERFACE ---
st.title("📊 Sistema de Gestão de Patrimônio")

tab1, tab2 = st.tabs(["🔍 Inventário (Leitor Zebra)", "🏢 Relatório por Unidade"])

# --- TAB 1: INVENTÁRIO ATIVO ---
with tab1:
    st.subheader("Leitura em Tempo Real")
    st.text_input("Bipe o item:", key="campo_zebra", on_change=registrar_item_zebra)
    
    if st.session_state['lista_inventario']:
        df_inv = pd.DataFrame(st.session_state['lista_inventario'])
        st.dataframe(df_inv, use_container_width=True)
        
        output_inv = BytesIO()
        with pd.ExcelWriter(output_inv, engine='xlsxwriter') as writer:
            df_inv.to_excel(writer, index=False)
        st.download_button("📥 Baixar Inventário Atual", output_inv.getvalue(), "inventario_zebra.xlsx")

# --- TAB 2: RELATÓRIO DA BASE POR UNIDADE ---
with tab2:
    st.subheader("Gerar Relatório Completo da Unidade")
    unidade_sel = st.selectbox("Selecione a Unidade desejada:", NOME_DAS_UNIDADES)
    
    if df_referencia is not None:
        # Filtra a base original pela unidade selecionada (Coluna F)
        df_unidade = df_referencia[df_referencia['unidade_ref'] == unidade_sel]
        
        st.write(f"Itens encontrados para **{unidade_sel}**: {len(df_unidade)}")
        st.dataframe(df_unidade, use_container_width=True)
        
        if not df_unidade.empty:
            output_uni = BytesIO()
            with pd.ExcelWriter(output_uni, engine='xlsxwriter') as writer:
                df_unidade.to_excel(writer, index=False, header=['PIB', 'Descrição', 'Cód. Local', 'Unidade'])
            
            st.download_button(
                label=f"📥 Baixar Relatório Completo: {unidade_sel}",
                data=output_uni.getvalue(),
                file_name=f"base_{unidade_sel.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Nenhum item encontrado para esta unidade na base de dados.")

# Sidebar
if st.sidebar.button("🗑️ Limpar Inventário (Zebra)"):
    st.session_state['lista_inventario'] = []
    st.rerun()
