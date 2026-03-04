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
# Removidos os espaços da senha para evitar erro de autenticação
SENHA_DE_APP = "fnnyszccqjlpcsiv" 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Inventory Pro Safe", page_icon="📦", layout="wide")

NOME_DAS_UNIDADES = [
    " ", "CLI BELO HORIZONTE/DR/MG", "CLI TJ MG", "CLI SMS CONTAGEM", 
    "CLI CONTAGEM", "CDIP BELO HORIZONTE", "CLI INDAIA", "CLI UNIVERSITARIO", 
    "CLI MONTES CLAROS", "CLI UBERLANDIA", "CLI VARGINHA", 
    "CLI DEFENSORIA PUBLICA DE MG", "CLI EFULFILLMENT EXTREMA", "CLI TAPERA", 
    "GER REG LOGISTICA/COPER", "SUB GEST OPER LOGISTICA/GELOG", 
    "SUB PLAN DE LOGISTICA/GELOG", "SEC ADMINISTRATIVA/GELOG", "CLI ARMAZEM DE RECURSOS"
]

def obter_agora_br():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

# --- SIDEBAR ---
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

def enviar_relatorio_email(destinatario, df_dados, titulo_relatorio):
    try:
        agora_br = obter_agora_br()
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_dados.to_excel(writer, index=False, sheet_name='Relatorio')
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        msg['Subject'] = f"{titulo_relatorio} - {agora_br.strftime('%d/%m/%Y %H:%M')}"
        
        corpo = f"Relatório enviado por: {usuario_id.upper()}\nData/Hora: {agora_br.strftime('%d/%m/%Y %H:%M:%S')}"
        msg.attach(MIMEText(corpo, 'plain'))
        
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
        st.error(f"Erro ao enviar: {e}")
        return False

def tocar_som(tipo="sucesso"):
    src = "https://www.soundjay.com/buttons/sounds/button-37.mp3" if tipo == "sucesso" else "https://www.soundjay.com/buttons/sounds/button-10.mp3"
    audio_html = f'<audio autoplay style="display:none;"><source src="{src}" type="audio/mp3"></audio>'
    st.components.v1.html(audio_html, height=0)

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

if 'usuario_atual' not in st.session_state or st.session_state['usuario_atual'] != usuario_id:
    if os.path.exists(ARQUIVO_BACKUP):
        st.session_state['lista_inventario'] = pd.read_csv(ARQUIVO_BACKUP, encoding='utf-8-sig').to_dict('records')
    else:
        st.session_state['lista_inventario'] = []
    st.session_state['usuario_atual'] = usuario_id

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
                    info = {"Descrição": res.iloc[0]['desc_ref'], "Cód. Local": res.iloc[0]['cod_local_ref'], 
                            "Unidade": res.iloc[0]['unidade_ref'], "Status": res.iloc[0]['status_ref']}
                    achou = True
            tocar_som("sucesso" if achou else "erro")
            st.session_state['lista_inventario'].insert(0, {
                "Item": 0, "Hora": agora_br.strftime("%H:%M:%S"), "PIB": pib, 
                "Descrição": info["Descrição"], "Cód. Local": info["Cód. Local"], 
                "Unidade Base": info["Unidade"], "Status": info["Status"], 
                "Etiqueta": st.session_state.tipo_etiqueta_sel
            })
            pd.DataFrame(st.session_state['lista_inventario']).to_csv(ARQUIVO_BACKUP, index=False, encoding='utf-8-sig')
    st.session_state.campo_zebra = ""

# --- INTERFACE ---
st.title(f"📊 Gestão de Patrimônio - Usuário: {usuario_id.upper()}")

tab1, tab2 = st.tabs(["🔍 Coletor Zebra", "🏢 Relatório por Unidade"])

with tab1:
    c_opt, c_in = st.columns([1, 2])
    c_opt.radio("Tipo de Etiqueta:", ["Papel", "Metal"], key="tipo_etiqueta_sel", horizontal=True)
    c_in.text_input("Bipe aqui:", key="campo_zebra", on_change=registrar_item_zebra, placeholder="Aguardando scanner...")
    
    if st.session_state['lista_inventario']:
        df_v = pd.DataFrame(st.session_state['lista_inventario'])
        df_v['Item'] = range(len(df_v), 0, -1)
        cols_ordem = ['Item', 'Hora', 'PIB', 'Descrição', 'Cód. Local', 'Unidade Base', 'Status', 'Etiqueta']
        
        st.markdown("---")
        st.subheader("📤 Exportar Resultados")
        
        # CAMPO DE EMAIL MUITO MAIS INTUITIVO
        email_inv = st.text_input(
            label="📧 Para quem devemos enviar o relatório?", 
            key="email_inv", 
            placeholder="Digite o e-mail do destinatário (ex: supervisor@empresa.com.br)",
            help="Insira um e-mail válido para habilitar o envio."
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            buffer_dl = BytesIO()
            with pd.ExcelWriter(buffer_dl, engine='xlsxwriter') as writer:
                df_v[cols_ordem].to_excel(writer, index=False)
            st.download_button("📥 Baixar em Excel", buffer_dl.getvalue(), f"inv_{usuario_id}.xlsx", use_container_width=True)
        
        with col_btn2:
            # Botão só ativa se o e-mail parecer válido (contém @ e .)
            email_valido = "@" in email_inv and "." in email_inv
            if st.button("📧 Enviar por E-mail Agora", use_container_width=True, disabled=not email_valido):
                with st.spinner("Enviando e-mail..."):
                    if enviar_relatorio_email(email_inv, df_v[cols_ordem], f"Inventário - {usuario_id.upper()}"):
                        st.success(f"Relatório enviado com sucesso para {email_inv}!")

        st.markdown("---")
        st.dataframe(df_v[cols_ordem], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🏢 Consulta por Unidade")
    unidade_sel = st.selectbox("Selecione a Unidade para filtrar:", NOME_DAS_UNIDADES)
    
    if df_referencia is not None:
        df_u = df_referencia[df_referencia['unidade_ref'] == unidade_sel]
        if not df_u.empty:
            df_u_show = df_u.copy()
            df_u_show.columns = ['PIB', 'Descrição', 'Cód. Local', 'Unidade Base', 'Status']
            
            # EMAIL INTUITIVO TAMBÉM NA ABA 2
            email_u = st.text_input("📧 Enviar base desta unidade para:", key="email_uni_aba2", placeholder="diretoria@empresa.com")
            
            c_u1, c_u2 = st.columns(2)
            with c_u1:
                buf_u = BytesIO()
                with pd.ExcelWriter(buf_u, engine='xlsxwriter') as writer:
                    df_u_show.to_excel(writer, index=False)
                st.download_button(f"📥 Baixar Base {unidade_sel}", buf_u.getvalue(), f"base_{unidade_sel}.xlsx", use_container_width=True)
            with c_u2:
                if st.button("📧 Enviar Base Unidade", use_container_width=True, disabled="@" not in email_u):
                    if enviar_relatorio_email(email_u, df_u_show, f"Base - {unidade_sel}"):
                        st.success("Base enviada!")

            st.write(f"Itens encontrados nesta unidade: **{len(df_u)}**")
            st.dataframe(df_u_show, use_container_width=True, hide_index=True)
