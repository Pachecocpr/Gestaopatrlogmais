import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from io import BytesIO
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inventory Pro Safe", page_icon="📦", layout="wide")

ARQUIVO_BACKUP = "inventario_backup.csv"

# Lista de unidades conforme sua necessidade
NOME_DAS_UNIDADES = [
    " ", "CLI BELO HORIZONTE/DR/MG", "CLI TJ MG", "CLI SMS CONTAGEM", 
    "CLI CONTAGEM", "CDIP BELO HORIZONTE", "CLI INDAIA", "CLI UNIVERSITARIO", 
    "CLI MONTES CLAROS", "CLI UBERLANDIA", "CLI VARGINHA", 
    "CLI DEFENSORIA PUBLICA DE MG", "CLI EFULFILLMENT EXTREMA", "CLI TAPERA", 
    "GER REG LOGISTICA/COPER", "SUB GEST OPER LOGISTICA/GELOG", 
    "SUB PLAN DE LOGISTICA/GELOG", "SEC ADMINISTRATIVA/GELOG", "CLI ARMAZEM DE RECURSOS"
]

# --- FUNÇÃO PARA O SOM (COM SCRIPT DE DESBLOQUEIO PARA SMARTPHONE) ---
def tocar_som(tipo="sucesso"):
    # Sons de bips curtos e padrão
    if tipo == "sucesso":
        src = "https://www.soundjay.com/buttons/sounds/button-37.mp3"
    else:
        src = "https://www.soundjay.com/buttons/sounds/button-10.mp3"
    
    # O JavaScript tenta forçar o play. Se o navegador bloquear, ele avisa no console.
    audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="{src}" type="audio/mp3">
        </audio>
        <script>
            var audio = document.querySelector('audio');
            audio.play().catch(function(error) {{
                console.log("Audio bloqueado pelo navegador. Interaja com a página primeiro.");
            }});
        </script>
    """
    st.components.v1.html(audio_html, height=0)

# --- FUNÇÕES DE PERSISTÊNCIA (ANTI-PERDA) ---
def salvar_no_disco(df):
    df.to_csv(ARQUIVO_BACKUP, index=False, encoding='utf-8-sig')

def carregar_do_disco():
    if os.path.exists(ARQUIVO_BACKUP):
        try:
            return pd.read_csv(ARQUIVO_BACKUP, encoding='utf-8-sig')
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- 1. CARREGAMENTO DA BASE MESTRE (COLUNAS B, C, E, F, J) ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Colunas: B=1, C=2, E=4, F=5, J=9
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

# Inicialização com recuperação de backup automático
if 'lista_inventario' not in st.session_state:
    df_recuperado = carregar_do_disco()
    st.session_state['lista_inventario'] = df_recuperado.to_dict('records')

# --- 2. LÓGICA DO INVENTÁRIO (COM TRAVA DE DUPLICIDADE) ---
def registrar_item_zebra():
    pib_lido = str(st.session_state.campo_zebra).strip().upper()
    
    if pib_lido:
        # VERIFICAÇÃO DE DUPLICIDADE
        pibs_ja_lidos = [str(item['PIB']).upper() for item in st.session_state['lista_inventario']]
        
        if pib_lido in pibs_ja_lidos:
            st.toast(f"🚫 Item {pib_lido} já foi bipado!", icon="❌")
            tocar_som("erro")
            st.session_state.campo_zebra = ""
            return

        # DADOS DA LEITURA
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
        
        # Feedback Sonoro
        tocar_som("sucesso" if achou else "erro")
        
        # Inserção na Lista
        st.session_state['lista_inventario'].insert(0, {
            "Item": 0, # Será recalculado na exibição
            "Hora": hora_atual,
            "PIB": pib_lido,
            "Descrição": info["Descrição"],
            "Cód. Local": info["Cód. Local"],
            "Unidade Base": info["Unidade"],
            "Status": info["Status"],
            "Etiqueta": tipo_etiqueta_atual
        })
        
        # Salvamento Físico (Anti-Perda)
        df_salvar = pd.DataFrame(st.session_state['lista_inventario'])
        salvar_no_disco(df_salvar)
        
        st.session_state.campo_zebra = ""

# --- 3. INTERFACE DO USUÁRIO ---
st.title("📊 Gestão de Patrimônio Profissional")

with st.sidebar:
    st.header("⚙️ Configurações")
    st.info("💡 No smartphone, toque na tela uma vez para ativar os bips sonoros.")
    if st.button("🗑️ Limpar Tudo (Apagar Backup)"):
        if os.path.exists(ARQUIVO_BACKUP):
            os.remove(ARQUIVO_BACKUP)
        st.session_state['lista_inventario'] = []
        st.rerun()

tab1, tab2 = st.tabs(["🔍 Inventário (Zebra)", "🏢 Relatório por Unidade"])

# --- ABA 1: COLETOR ---
with tab1:
    col_input, col_tipo = st.columns([2, 1])
    with col_tipo:
        st.radio("Etiqueta:", ["Papel", "Metal"], key="tipo_etiqueta_sel", horizontal=True)
    with col_input:
        st.text_input("Aguardando BIP:", key="campo_zebra", on_change=registrar_item_zebra, placeholder="Aponte o leitor aqui")

    if st.session_state['lista_inventario']:
        df_inv = pd.DataFrame(st.session_state['lista_inventario'])
        
        # Ajuste dinâmico da numeração "Item"
        total = len(df_inv)
        df_inv['Item'] = range(total, 0, -1)
        
        # Reorganizar colunas
        cols = ['Item', 'Hora', 'PIB', 'Descrição', 'Cód. Local', 'Unidade Base', 'Status', 'Etiqueta']
        df_inv = df_inv[cols]

        st.dataframe(df_inv, use_container_width=True, hide_index=True)
        
        # Exportação Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_inv.to_excel(writer, index=False, sheet_name='Inventario')
        
        st.download_button(
            label="📥 Baixar Relatório do Coletor",
            data=buffer.getvalue(),
            file_name=f"inventario_{datetime.now().strftime('%d%m_%H%M')}.xlsx",
            use_container_width=True
        )

# --- ABA 2: CONSULTA BASE ---
with tab2:
    st.subheader("Extrair Dados por Unidade")
    unidade_sel = st.selectbox("Selecione a Unidade para Relatório:", NOME_DAS_UNIDADES)
    
    if df_referencia is not None:
        df_unidade = df_referencia[df_referencia['unidade_ref'] == unidade_sel]
        
        st.write(f"Itens cadastrados na base: **{len(df_unidade)}**")
        
        df_display = df_unidade.copy()
        df_display.columns = ['PIB', 'Descrição', 'Cód. Local', 'Unidade', 'Status']
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        if not df_display.empty:
            buf_uni = BytesIO()
            with pd.ExcelWriter(buf_uni, engine='xlsxwriter') as writer:
                df_display.to_excel(writer, index=False)
            
            st.download_button(
                label=f"📥 Baixar Relatório: {unidade_sel}",
                data=buf_uni.getvalue(),
                file_name=f"base_{unidade_sel.replace(' ', '_')}.xlsx",
                use_container_width=True
            )
