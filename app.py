import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import zipfile  # Para agrupar múltiplos relatórios

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inventory Pro", page_icon="📦", layout="centered")

@st.cache_data
def carregar_base_mestre():
    try:
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

# --- INTERFACE ---
st.title("📦 Inventário por Localidade")

st.text_input("Aguardando leitura...", key="campo_zebra", on_change=registrar_item)

if st.session_state['lista_patrimonio']:
    df_result = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df_result, use_container_width=True)

    col1, col2 = st.columns(2)

    # OPÇÃO 1: Relatório Geral
    with col1:
        output_geral = BytesIO()
        with pd.ExcelWriter(output_geral, engine='xlsxwriter') as writer:
            df_result.to_excel(writer, index=False)
        st.download_button("📥 Relatório Geral", output_geral.getvalue(), "geral.xlsx", use_container_width=True)

    # OPÇÃO 2: Relatórios Separados por Unidade (ZIP)
    with col2:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
            # Para cada unidade única na lista, cria um Excel separado
            unidades = df_result['Unidade'].unique()
            for uni in unidades:
                excel_uni = BytesIO()
                df_uni = df_result[df_result['Unidade'] == uni]
                with pd.ExcelWriter(excel_uni, engine='xlsxwriter') as writer:
                    df_uni.to_excel(writer, index=False)
                # Nomeia o arquivo com o código da unidade
                zf.writestr(f"Relatorio_Unidade_{uni}.xlsx", excel_uni.getvalue())
        
        st.download_button("🗂️ Relatórios por Unidade (ZIP)", buf.getvalue(), "relatorios_por_localidade.zip", use_container_width=True)

if st.sidebar.button("Limpar"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
