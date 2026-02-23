import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURAÇÃO E LISTA DE UNIDADES ---
st.set_page_config(page_title="Inventory Pro", page_icon="📦", layout="centered")

NOME_DAS_UNIDADES = [
    "CLI-CONTAGEM BH", "CLI-CONTAGEM CTG", "CLI-TAPERA", "CLI-ARO",
    "CLI-UNIVERSITÁRIO", "CLI-DEFENSORIA PÚBLICA", "CLI-TJ",
    "CLI-INDAIA", "CEDIP", "GELOG-MG", "CLI-CAIXA"
]

# --- 1. CARREGAMENTO DA BASE MESTRE (COLUNAS B, C, E, F) ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Coluna B=1, C=2, E=4, F=5
        df = pd.read_excel("base_patrimonio.xlsx", engine='openpyxl', header=None)
        df_limpo = pd.DataFrame()
        df_limpo['pib_ref'] = df.iloc[:, 1].astype(str).str.strip().str.upper()
        df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()
        df_limpo['cod_local_ref'] = df.iloc[:, 4].astype(str).str.strip()
        df_limpo['unidade_ref'] = df.iloc[:, 5].astype(str).str.strip()
        return df_limpo
    except Exception as e:
        st.error(f"Erro ao acessar base_patrimonio.xlsx: {e}")
        return None

df_referencia = carregar_base_mestre()

if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# --- 2. LÓGICA DE REGISTRO ---
def registrar_item():
    pib_lido = str(st.session_state.campo_zebra).strip().upper()
    if pib_lido:
        detalhes = {"Descrição": "NÃO LOCALIZADO", "Cód. Local": "---", "Unidade": "---"}
        if df_referencia is not None:
            resultado = df_referencia[df_referencia['pib_ref'] == pib_lido]
            if not resultado.empty:
                detalhes["Descrição"] = resultado.iloc[0]['desc_ref']
                detalhes["Cód. Local"] = resultado.iloc[0]['cod_local_ref']
                detalhes["Unidade"] = resultado.iloc[0]['unidade_ref']
        
        st.session_state['lista_patrimonio'].insert(0, {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "PIB/Patrimônio": pib_lido,
            "Descrição": detalhes["Descrição"],
            "Cód. Local": detalhes["Cód. Local"],
            "Unidade": detalhes["Unidade"]
        })
        st.session_state.campo_zebra = ""

# --- 3. INTERFACE ---
st.title("📦 Inventário de Patrimônio")

st.text_input("Aguardando leitura (Scanner Zebra):", key="campo_zebra", on_change=registrar_item)

if st.session_state['lista_patrimonio']:
    df_result = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.subheader(f"📋 Itens Coletados ({len(df_result)})")
    st.dataframe(df_result, use_container_width=True)

    st.divider()
    
    # --- 4. ÁREA DE DOWNLOAD E FILTRO ---
    st.subheader("📥 Exportar Relatórios")
    
    col_geral, col_filtro = st.columns(2)

    with col_geral:
        st.markdown("**Opção 1: Tudo**")
        output_geral = BytesIO()
        with pd.ExcelWriter(output_geral, engine='xlsxwriter') as writer:
            df_result.to_excel(writer, index=False)
        st.download_button(
            label="Baixar Relatório Geral",
            data=output_geral.getvalue(),
            file_name="inventario_completo.xlsx",
            use_container_width=True
        )

    with col_filtro:
        st.markdown("**Opção 2: Por Unidade**")
        unidade_selecionada = st.selectbox("Selecione a Unidade para filtrar:", NOME_DAS_UNIDADES)
        
        # Filtra os dados com base na seleção
        df_filtrado = df_result[df_result['Unidade'] == unidade_selecionada]
        
        output_filtrado = BytesIO()
        with pd.ExcelWriter(output_filtrado, engine='xlsxwriter') as writer:
            df_filtrado.to_excel(writer, index=False)
        
        # Só habilita o download se houver itens para aquela unidade
        if not df_filtrado.empty:
            st.download_button(
                label=f"Baixar Relatório: {unidade_selecionada}",
                data=output_filtrado.getvalue(),
                file_name=f"inventario_{unidade_selecionada.replace(' ', '_')}.xlsx",
                use_container_width=True
            )
        else:
            st.warning("Nenhum item desta unidade na lista atual.")

# Sidebar
if st.sidebar.button("🗑️ Limpar Lista"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
