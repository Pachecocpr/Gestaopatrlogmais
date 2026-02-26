import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from io import BytesIO
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# --- CONFIGURAÇÕES DE E-MAIL ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = "inventarioautomatico@gmail.com"
SENHA_DE_APP = "fnny szcc qjlp csiv" 

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

# --- FUNÇÃO DE ENVIO DE E-MAIL ---
def enviar_relatorio(destinatario, df_dados):
    try:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_dados.to_excel(writer, index=False, sheet_name='Inventario')
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        msg['Subject'] = f"Relatório Inventário - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        corpo = f"Segue em anexo o relatório de inventário.\nTotal de itens: {len(df_dados)}"
        msg.attach(MIMEText(corpo, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= inventario_{datetime.now().strftime('%d%m_%H%M')}.xlsx")
        msg.attach(part)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_DE_APP)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

# --- FUNÇÃO PARA O SOM (BEEP) ---
def tocar_som(tipo="sucesso"):
    src = "https://www.soundjay.com/buttons/sounds/button-37.mp3" if tipo == "sucesso" else "https://www.soundjay.com/buttons/sounds/button-10.mp3"
    audio_html = f"""
        <audio autoplay style="display:none;"><source src="{src}" type="audio/mp3"></audio>
        <script>document.querySelector('audio').play();</script>
    """
    st.components.v1.html(audio_html, height=0)

# --- PERSISTÊNCIA ---
def salvar_no_disco(df):
    df.to_csv(ARQUIVO_BACKUP, index=False, encoding='utf-8-sig')

def carregar_do_disco():
    if os.path.exists(ARQUIVO_BACKUP):
        try: return pd.read_csv(ARQUIVO_BACKUP, encoding='utf-8-sig')
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- CARREGAMENTO BASE ---
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
    except: return None

df_referencia = carregar_base_mestre()

if 'lista_inventario' not in st.session_state:
    df_rec = carregar_do_disco()
    st.session_state['lista_inventario'] = df_rec.to_dict('records')

# --- LÓGICA DE REGISTRO ---
def registrar_item_zebra():
    pib = str(st.session_state.campo_zebra).strip().upper()
    if pib:
        pibs_lidos = [str(item['PIB']).upper() for item in st.session_state['lista_inventario']]
        if pib in pibs_lidos:
            st.toast(f"🚫 Duplicado: {pib}", icon="❌")
            tocar_som("erro")
        else:
            fuso = pytz.timezone('America/Sao_Paulo')
            info = {"Descrição": "NÃO LOCALIZADO", "Cód. Local": "---", "Unidade": "---", "Status": "---"}
            achou = False
            if df_referencia is not None:
                res = df_referencia[df_referencia['pib_ref'] == pib]
                if not res.empty:
                    info = {"Descrição": res.iloc[0]['desc_ref'], "Cód. Local": res.iloc[0]['cod_local_ref'], "Unidade": res.iloc[0]['unidade_ref'], "Status": res.iloc[0]['status_ref']}
                    achou = True
            tocar_som("sucesso" if achou else "erro")
            st.session_state['lista_inventario'].insert(0, {"Item": 0, "Hora": datetime.now(fuso).strftime("%H:%M:%S"), "PIB": pib, "Descrição": info["Descrição"], "Cód. Local": info["Cód. Local"], "Unidade Base": info["Unidade"], "Status": info["Status"], "Etiqueta": st.session_state.tipo_etiqueta_sel})
            salvar_no_disco(pd.DataFrame(st.session_state['lista_inventario']))
    st.session_state.campo_zebra = ""

# --- INTERFACE ---
st.title("📊 Gestão de Patrimônio Safe")

with st.sidebar:
    st.header("📧 Enviar por E-mail")
    email_dest = st.text_input("Destinatário:", placeholder="exemplo@email.com")
    if st.button("Enviar Agora"):
        if st.session_state['lista_inventario'] and email_dest:
            with st.spinner("Enviando..."):
                if enviar_relatorio(email_dest, pd.DataFrame(st.session_state['lista_inventario'])):
                    st.success("Enviado!")
        else: st.warning("Verifique o e-mail ou se há dados.")
    
    st.divider()
    if st.button("🗑️ Limpar Tudo"):
        if os.path.exists(ARQUIVO_BACKUP): os.remove(ARQUIVO_BACKUP)
        st.session_state['lista_inventario'] = []
        st.rerun()

tab1, tab2 = st.tabs(["🔍 Coletor Zebra", "🏢 Por Unidade"])

with tab1:
    col_r, col_i = st.columns([1, 2])
    col_r.radio("Etiqueta:", ["Papel", "Metal"], key="tipo_etiqueta_sel", horizontal=True)
    col_i.text_input("Bipe aqui:", key="campo_zebra", on_change=registrar_item_zebra)
    
    if st.session_state['lista_inventario']:
        df_v = pd.DataFrame(st.session_state['lista_inventario'])
        df_v['Item'] = range(len(df_v), 0, -1)
        cols = ['Item', 'Hora', 'PIB', 'Descrição', 'Cód. Local', 'Status', 'Etiqueta']
        
        st.dataframe(df_v[cols], use_container_width=True, hide_index=True)

        # --- NOVA OPÇÃO: DOWNLOAD MANUAL ---
        buffer_dl = BytesIO()
        with pd.ExcelWriter(buffer_dl, engine='xlsxwriter') as writer:
            df_v[cols].to_excel(writer, index=False, sheet_name='Inventario')
        
        st.download_button(
            label="📥 Baixar Arquivo Excel (Download Direto)",
            data=buffer_dl.getvalue(),
            file_name=f"inventario_{datetime.now().strftime('%d%m_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with tab2:
    unidade = st.selectbox("Unidade:", NOME_DAS_UNIDADES)
    if df_referencia is not None:
        df_u = df_referencia[df_referencia['unidade_ref'] == unidade]
        st.write(f"Itens na base: **{len(df_u)}**")
        st.dataframe(df_u, use_container_width=True, hide_index=True)
