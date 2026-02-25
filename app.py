import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from io import BytesIO
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inventory Pro Safe", page_icon="📦", layout="wide")

ARQUIVO_BACKUP = "inventario_backup.csv"

# Lista de unidades
NOME_DAS_UNIDADES = [
    " ", "CLI BELO HORIZONTE/DR/MG", "CLI TJ MG", "CLI SMS CONTAGEM", 
    "CLI CONTAGEM", "CDIP BELO HORIZONTE", "CLI INDAIA", "CLI UNIVERSITARIO", 
    "CLI MONTES CLAROS", "CLI UBERLANDIA", "CLI VARGINHA", 
    "CLI DEFENSORIA PUBLICA DE MG", "CLI EFULFILLMENT EXTREMA", "CLI TAPERA", 
    "GER REG LOGISTICA/COPER", "SUB GEST OPER LOGISTICA/GELOG", 
    "SUB PLAN DE LOGISTICA/GELOG", "SEC ADMINISTRATIVA/GELOG", "CLI ARMAZEM DE RECURSOS"
]

# --- FUNÇÃO PARA O SOM (BEEP) ---
def tocar_som(tipo="sucesso"):
    if tipo == "sucesso":
        audio_url = "https://catalog.botreetechnologies.com/sounds/success.mp3"
    else:
        audio_url = "https://catalog.botreetechnologies.com/sounds/error.mp3"
    
    audio_html = f"""
        <audio autoplay>
            <source src="{audio_url}" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(audio_html, height=0)

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_disco(df):
    df.to_csv(ARQUIVO_BACKUP, index=False, encoding='utf-8-sig')

def carregar_do_disco():
    if os.path.exists(ARQUIVO_BACKUP):
        try:
            return pd.read_csv(ARQUIVO_BACKUP, encoding='utf-8-sig')
        except:
            return pd.DataFrame()
    return pd.DataFrame()

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
    df_recuperado = carregar_do_disco()
    st.session_state['lista_inventario'] = df_recuperado.to_dict('records')

# --- 2. LÓGICA DO INVENTÁRIO COM TRAVA DE DUPLICIDADE ---
def registrar_item_zebra():
    pib_lido = str(st.session_state.campo_zebra).strip().upper()
    
    if pib_lido:
        # --- VERIFICAÇÃO DE DUPLICIDADE ---
        pibs_ja_lidos = [item['PIB'] for item in st.session_state['lista_inventario']]
        
        if pib_lido in pibs_ja_lidos:
            st.toast(f"⚠️ O item {pib_lido} já foi lido anteriormente!", icon="🚫")
            tocar_som("erro")
            st.session_state.campo_zebra = ""
            return # Interrompe a função aqui para não duplicar
        
        tipo_etiqueta_atual = st.session_state.tipo_etiqueta_sel
        fuso_br = pytz.timezone('America/Sao_Paulo')
        hora_atual = datetime.now(fuso_br).strftime("%H:%M:%S")
        
        info = {"Descrição": "NÃO LOCALIZADO", "Cód. Local": "---", "Unidade": "---", "Status": "---"}
        achou = False
        
        if df_referencia is not None:
            res = df_referencia[df_referencia['pib_ref'] == pib_lido]
            if not res.empty:
                info = {
                    "Descrição": res.iloc[0]['desc_ref'], 
                    "Cód. Local": res.iloc[0]['cod_local_ref'], 
                    "Unidade": res.iloc[0]['unidade_ref'],
                    "Status": res.iloc[0]['status_ref']
                }
                achou = True
        
        tocar_som("sucesso" if achou else "erro")
        
        st.session_state['lista_inventario'].insert(0, {
            "Item": 0,
            "Hora": hora_atual,
            "PIB": pib_lido,
            "Descrição": info["Descrição"],
            "Cód. Local": info["Cód. Local"],
            "Unidade Base": info["Unidade"],
            "Status": info["Status"],
            "Etiqueta": tipo_etiqueta_atual
        })
        
        df_para_salvar = pd.DataFrame(st.session_state['lista_inventario'])
        salvar_no_disco(df_para_salvar)
        st.session_state.campo_zebra = ""

# --- 3. INTERFACE ---
st.title("📊 Gestão de Patrimônio - Safe + 🔊")

tab1, tab2 = st.tabs(["🔍 Inventário Ativo (Zebra)", "🏢 Relatório por Unidade"])

with tab1:
    st.subheader("Leitura com Coletor")
    st.radio("Selecione o tipo de etiqueta:", ["Papel", "Metal"], key="tipo_etiqueta_sel", horizontal=True)
    st.text_input("Bipe o item aqui:", key="campo_zebra", on_change=registrar_item_zebra)
    
    if st.session_state['lista_inventario']:
        df_inv = pd.DataFrame(st.session_state['lista_inventario'])
        
        total_itens = len(df_inv)
        df_inv['Item'] = range(total_itens, 0, -1)
        
        cols = ['Item'] + [c for c in df_inv.columns if c != 'Item']
        df_inv = df_inv[cols]

        st.dataframe(df_inv, use_container_width=True, hide_index=True)
        
        output_inv = BytesIO()
        with pd.ExcelWriter(output_inv, engine='xlsxwriter') as writer:
            df_inv.to_excel(writer, index=False, sheet_name='Inventario')
            
        st.download_button(
            label="📥 Baixar Inventário", 
            data=output_inv.getvalue(), 
            file_name=f"inventario_{datetime.now().strftime('%d%m_%H%M')}.xlsx",
            use_container_width=True
        )

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
with st.sidebar:
    st.header("Configurações")
    if st.button("🗑️ Limpar Inventário"):
        if os.path.exists(ARQUIVO_BACKUP):
            os.remove(ARQUIVO_BACKUP)
        st.session_state['lista_inventario'] = []
        st.rerun()
