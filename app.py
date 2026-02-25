import streamlit as st
import pandas as pd
from datetime import datetime
import pytz  # Necessário para o fuso horário
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inventory Pro", page_icon="📦", layout="wide")

# Lista de unidades
NOME_DAS_UNIDADES = [
    " ", "CLI BELO HORIZONTE/DR/MG", "CLI TJ MG", "CLI SMS CONTAGEM", 
    "CLI CONTAGEM", "CDIP BELO HORIZONTE", "CLI INDAIA", "CLI UNIVERSITARIO", 
    "CLI MONTES CLAROS", "CLI UBERLANDIA", "CLI VARGINHA", 
    "CLI DEFENSORIA PUBLICA DE MG", "CLI EFULFILLMENT EXTREMA", "CLI TAPERA", 
    "GER REG LOGISTICA/COPER", "SUB GEST OPER LOGISTICA/GELOG", 
    "SUB PLAN DE LOGISTICA/GELOG", "SEC ADMINISTRATIVA/GELOG", "CLI ARMAZEM DE RECURSOS"
]

# --- 1. CARREGAMENTO DA BASE MESTRE ---
@st.cache_data
def carregar_base_mestre():
    try:
        df = pd.read_excel("base_patrimonio.xlsx", engine='openpyxl', header=None)
        df_limpo = pd.DataFrame()
        df_limpo['pib_ref'] = df.iloc[:, 1].astype(str).str.strip().str.upper()
        df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()
        df_limpo['cod_local_ref'] = df.iloc[:, 4].astype(str).str.strip()
        df_limpo['unidade_ref'] = df.iloc[:, 5].astype(str).str.strip()
        df_limpo['status_ref'] = df.iloc[:, 9].astype(str).str.strip()
        return df_limpo
    except Exception as e:
        st.error(f"Erro ao carregar base_patrimonio.xlsx: {e}")
        return None

df_referencia = carregar_base_mestre()

if 'lista_inventario' not in st.session_state:
    st.session_state['lista_inventario'] = []

# --- 2. LÓGICA DO INVENTÁRIO (ZEBRA) ---
def registrar_item_zebra():
    pib_lido = str(st.session_state.campo_zebra).strip().upper()
    if pib_lido:
        tipo_etiqueta_atual = st.session_state.tipo_etiqueta_sel
        
        # AJUSTE DE HORA: Define fuso horário de Brasília
        fuso_br = pytz.timezone('America/Sao_Paulo')
        hora_atual = datetime.now(fuso_br).strftime("%H:%M:%S")
        
        info = {"Descrição": "NÃO LOCALIZADO", "Cód. Local": "---", "Unidade": "---", "Status": "---"}
        
        if df_referencia is not None:
            res = df_referencia[df_referencia['pib_ref'] == pib_lido]
            if not res.empty:
                info = {
                    "Descrição": res.iloc[0]['desc_ref'], 
                    "Cód. Local": res.iloc[0]['cod_local_ref'], 
                    "Unidade": res.iloc[0]['unidade_ref'],
                    "Status": res.iloc[0]['status_ref']
                }
        
        # Adiciona à lista
        st.session_state['lista_inventario'].insert(0, {
            "Item": len(st.session_state['lista_inventario']) + 1, # Será corrigido na exibição para ser sequencial
            "Hora": hora_atual,
            "PIB": pib_lido,
            "Descrição": info["Descrição"],
            "Cód. Local": info["Cód. Local"],
            "Unidade Base": info["Unidade"],
            "Status": info["Status"],
            "Etiqueta": tipo_etiqueta_atual
        })
        st.session_state.campo_zebra = ""

# --- 3. INTERFACE ---
st.title("📊 Gestão de Patrimônio & Status")

tab1, tab2 = st.tabs(["🔍 Inventário Ativo (Zebra)", "🏢 Relatório por Unidade"])

with tab1:
    st.subheader("Leitura com Coletor")
    st.radio("Selecione o tipo de etiqueta:", ["Papel", "Metal"], key="tipo_etiqueta_sel", horizontal=True)
    st.text_input("Bipe o item aqui:", key="campo_zebra", on_change=registrar_item_zebra)
    
    if st.session_state['lista_inventario']:
        # Criamos o DataFrame para manipulação
        df_inv = pd.DataFrame(st.session_state['lista_inventario'])
        
        # AJUSTE DE NUMERAÇÃO: Recalcula a coluna 'Item' para começar de 1 até o total, de cima para baixo
        total_itens = len(df_inv)
        df_inv['Item'] = range(total_itens, 0, -1)
        
        # Reordenar colunas para 'Item' ser a primeira
        cols = ['Item'] + [c for c in df_inv.columns if c != 'Item']
        df_inv = df_inv[cols]

        st.dataframe(df_inv, use_container_width=True, hide_index=True) # hide_index remove a coluna 0 do Streamlit
        
        output_inv = BytesIO()
        with pd.ExcelWriter(output_inv, engine='xlsxwriter') as writer:
            # index=False remove a coluna 0 no Excel gerado
            df_inv.to_excel(writer, index=False, sheet_name='Inventario')
            
        st.download_button(
            label="📥 Baixar Inventário (Com Hora e Numeração Corretas)", 
            data=output_inv.getvalue(), 
            file_name="inventario_zebra_corrigido.xlsx",
            use_container_width=True
        )

# --- ABA 2 (MANTIDA) ---
with tab2:
    st.subheader("Consulta da Base por Unidade")
    unidade_sel = st.selectbox("Selecione a Unidade:", NOME_DAS_UNIDADES)
    if df_referencia is not None:
        df_unidade = df_referencia[df_referencia['unidade_ref'] == unidade_sel]
        st.info(f"Encontrados **{len(df_unidade)}** itens em **{unidade_sel}**")
        df_display = df_unidade.copy()
        df_display.columns = ['PIB', 'Descrição', 'Cód. Local', 'Unidade', 'Status']
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- SIDEBAR ---
if st.sidebar.button("🗑️ Limpar Inventário"):
    st.session_state['lista_inventario'] = []
    st.rerun()
