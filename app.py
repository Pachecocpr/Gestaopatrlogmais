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

# Lista de unidades
NOME_DAS_UNIDADES = [
    " ", "CLI BELO HORIZONTE/DR/MG", "CLI TJ MG", "CLI SMS CONTAGEM", 
    "CLI CONTAGEM", "CDIP BELO HORIZONTE", "CLI INDAIA", "CLI UNIVERSITARIO", 
    "CLI MONTES CLAROS", "CLI UBERLANDIA", "CLI VARGINHA", 
    "CLI DEFENSORIA PUBLICA DE MG", "CLI EFULFILLMENT EXTREMA", "CLI TAPERA", 
    "GER REG LOGISTICA/COPER", "SUB GEST OPER LOGISTICA/GELOG", 
    "SUB PLAN DE LOGISTICA/GELOG", "SEC ADMINISTRATIVA/GELOG", "CLI ARMAZEM DE RECURSOS"
]

# --- FUNÇÃO PARA OBTER HORA DE BRASÍLIA ---
def obter_agora_br():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- SIDEBAR: IDENTIFICAÇÃO ---
with st.sidebar:
    st.header("👤 Usuário")
    usuario_id = st.text_input("Identificador do Conferente:", value="Padrao").strip().lower()
    ARQUIVO_BACKUP = f"backup_{usuario_id}.csv"
    
    st.divider()
    st.header("⚙️ Ferramentas")
    if st.button("🗑️ Limpar MEU Backup"):
        if os.path.exists(ARQUIVO_BACKUP):
            os.remove(ARQUIVO_BACKUP)
        st.session_state['lista_inventario'] = []
        st.rerun()

# --- FUNÇÃO GERAL DE ENVIO DE E-MAIL ---
def enviar_relatorio_email(destinatario, df_dados, titulo_relatorio):
    try:
        agora_br = obter_agora_br()
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_dados.to_excel(writer, index=False, sheet_name='Relatorio')
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        # Data e Hora corretas no Assunto
        msg['Subject'] = f"{titulo_relatorio} - {agora_br.strftime('%d/%m/%Y %H:%M')}"
        
        corpo = f"Relatório enviado por: {usuario_id.upper()}\nData/Hora: {agora_br.strftime('%d/%m/%Y %H:%M:%S')}\nTotal de registros: {len(df_dados)}"
        msg.attach(MIMEText(corpo, 'plain'))
        
        # Data e Hora corretas no Nome do Arquivo Anexo
        nome_anexo = f"relatorio_{usuario_id}_{agora_br.strftime('%d%m_%H%M')}.xlsx"
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {nome_anexo}")
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

# --- CARREGAMENTO DA BASE MESTRE ---
@st.cache_data
def carregar_base_mestre():
    try:
        df = pd.read_excel("base_patrimonio.xlsx", engine='openpyxl', header=None)
        df_limpo = pd.DataFrame()
        df_limpo['pib_ref'] = df.iloc[:, 1].astype(str).str.strip().str.upper()   # B
        df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()             # C
        df_limpo['cod_local_ref'] = df.iloc[:, 4].astype(str).str.strip()        # E
        df_limpo['unidade_ref'] = df.iloc[:, 5].astype(str).str.strip()          # F (NOME UNIDADE)
        df_limpo['status_ref'] = df.iloc[:, 9].astype(str).str.strip()           # J
        return df_limpo
    except: return None

df_referencia = carregar_base_mestre()

if 'usuario_atual' not in st.session_state or st.session_state['usuario_atual'] != usuario_id:
    df_rec = carregar_do_disco()
    st.session_state['lista_inventario'] = df_rec.to_dict('records')
    st.session_state['usuario_atual'] = usuario_id

# --- LÓGICA DE REGISTRO ---
def registrar_item_zebra():
    pib = str(st.session_state.campo_zebra).strip().upper()
    if pib:
        pibs_lidos = [str(item['PIB']).upper() for item in st.session_state['lista_inventario']]
        if pib in pibs_lidos:
            st.toast(f"🚫 Duplicado: {pib}", icon="❌")
            tocar_som("erro")
        else:
            agora_br = obter_agora_br()
            info = {"Descrição": "NÃO LOCALIZADO", "Cód. Local": "---", "Unidade": "---", "Status": "---"}
            achou = False
            if df_referencia is not None:
                res = df_referencia[df_referencia['pib_ref'] == pib]
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
                "Item": 0, "Hora": agora_br.strftime("%H:%M:%S"), "PIB": pib, 
                "Descrição": info["Descrição"], "Cód. Local": info["Cód. Local"], 
                "Unidade Base": info["Unidade"], "Status": info["Status"], 
                "Etiqueta": st.session_state.tipo_etiqueta_sel
            })
            salvar_no_disco(pd.DataFrame(st.session_state['lista_inventario']))
    st.session_state.campo_zebra = ""

# --- INTERFACE ---
st.title(f"📊 Gestão de Patrimônio - Usuário: {usuario_id.upper()}")

tab1, tab2 = st.tabs(["🔍 Coletor Zebra", "🏢 Relatório por Unidade"])

# ABA 1: COLETOR
with tab1:
    col_r, col_i = st.columns([1, 2])
    col_r.radio("Tipo de Etiqueta:", ["Papel", "Metal"], key="tipo_etiqueta_sel", horizontal=True)
    col_i.text_input("Bipe aqui:", key="campo_zebra", on_change=registrar_item_zebra)
    
    if st.session_state['lista_inventario']:
        df_v = pd.DataFrame(st.session_state['lista_inventario'])
        df_v['Item'] = range(len(df_v), 0, -1)
        cols_ordem = ['Item', 'Hora', 'PIB', 'Descrição', 'Cód. Local', 'Unidade Base', 'Status', 'Etiqueta']
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            agora_br = obter_agora_br()
            buffer_dl = BytesIO()
            with pd.ExcelWriter(buffer_dl, engine='xlsxwriter') as writer:
                df_v[cols_ordem].to_excel(writer, index=False)
            st.download_button(
                "📥 Baixar Inventário", 
                buffer_dl.getvalue(), 
                f"inventario_{usuario_id}_{agora_br.strftime('%d%m_%H%M')}.xlsx", 
                use_container_width=True
            )
        with c2:
            col_m_t, col_m_b = st.columns([2, 1])
            email_inv = col_m_t.text_input("E-mail:", key="email_inv", placeholder="dest@email.com", label_visibility="collapsed")
            if col_m_b.button("📧 Enviar", use_container_width=True):
                if email_inv and enviar_relatorio_email(email_inv, df_v[cols_ordem], f"Inventário de {usuario_id.upper()}"):
                    st.success("Enviado!")
        st.markdown("---")

        st.dataframe(df_v[cols_ordem], use_container_width=True, hide_index=True)

# ABA 2: RELATÓRIO POR UNIDADE
with tab2:
    st.subheader("Consulta da Base Mestre")
    unidade_sel = st.selectbox("Selecione a Unidade:", NOME_DAS_UNIDADES)
    
    if df_referencia is not None:
        df_u = df_referencia[df_referencia['unidade_ref'] == unidade_sel]
        if not df_u.empty:
            df_u_show = df_u.copy()
            df_u_show.columns = ['PIB', 'Descrição', 'Cód. Local', 'Unidade Base', 'Status']
            
            st.markdown("---")
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                agora_br = obter_agora_br()
                buf_u = BytesIO()
                with pd.ExcelWriter(buf_u, engine='xlsxwriter') as writer:
                    df_u_show.to_excel(writer, index=False)
                st.download_button(f"📥 Baixar {unidade_sel}", buf_u.getvalue(), f"base_{unidade_sel}_{agora_br.strftime('%d%m')}.xlsx", use_container_width=True)
            with col_u2:
                col_u_t, col_u_b = st.columns([2, 1])
                email_u = col_u_t.text_input("E-mail destino:", key="email_uni", label_visibility="collapsed")
                if col_u_b.button("📧 Enviar Base", use_container_width=True):
                    if email_u and enviar_relatorio_email(email_u, df_u_show, f"Base - {unidade_sel}"):
                        st.success("Enviado!")
            st.markdown("---")
            st.write(f"Itens encontrados: **{len(df_u)}**")
            st.dataframe(df_u_show, use_container_width=True, hide_index=True)
