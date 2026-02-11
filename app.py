import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

# --- 1. CONFIGURAÇÃO DE IDENTIDADE ---
try:
    img_logo = Image.open("logo.png")
    with open("logo.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
except:
    img_logo = "🗄️"
    logo_base64 = None

st.set_page_config(page_title="Inventory Pro", page_icon=img_logo, layout="centered")

# --- 2. CARREGAMENTO DA BASE (COM TRATAMENTO DE ERROS) ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Carrega o Excel
        df = pd.read_excel("base_patrimonio.xlsx")
        
        # Remove espaços em branco dos nomes das colunas e converte para minúsculas para comparar
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Procura as colunas corretas mesmo que o usuário erre maiúsculas/minúsculas
        # Vamos renomear para um padrão interno
        mapeamento = {
            'patrimonio': 'cod_ref',
            'patrimônio': 'cod_ref',
            'codigo': 'cod_ref',
            'descricao': 'desc_ref',
            'descrição': 'desc_ref',
            'bem': 'desc_ref'
        }
        df = df.rename(columns=mapeamento)
        
        # Limpa os dados: remove espaços e garante que tudo é String
        if 'cod_ref' in df.columns:
            df['cod_ref'] = df['cod_ref'].astype(str).str.strip()
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return None

df_referencia = carregar_base_mestre()

# --- 3. LÓGICA DE BUSCA E REGISTRO ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

def registrar_item():
    # Limpa o código vindo do Zebra (remove espaços e quebras de linha)
    codigo_lido = str(st.session_state.campo_zebra).strip()
    
    if codigo_lido:
        descricao_final = "NÃO LOCALIZADO"
        
        if df_referencia is not None and 'cod_ref' in df_referencia.columns:
            # Busca exata convertendo ambos para string
            resultado = df_referencia[df_referencia['cod_ref'] == codigo_lido]
            
            if not resultado.empty:
                # Pega a descrição da coluna que mapeamos como desc_ref
                descricao_final = str(resultado.iloc[0]['desc_ref'])
        
        # Salva o registro
        st.session_state['lista_patrimonio'].append({
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Patrimônio": codigo_lido,
            "Descrição": descricao_final,
            "Unidade": st.session_state.get('unidade_lote', 'Unidade 1')
        })
        
        # Feedback
        if descricao_final == "NÃO LOCALIZADO":
            st.toast(f"Código {codigo_lido} não encontrado!", icon="❌")
        else:
            st.toast(f"✅ {descricao_final}", icon="✔️")
        
        # Limpa o campo do scanner
        st.session_state.campo_zebra = ""

# --- 4. INTERFACE ---
if logo_base64:
    st.markdown(f'<center><img src="data:image/png;base64,{logo_base64}" width="120"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Inventário Pro</h2>", unsafe_allow_html=True)

# Área de Debug (Aparece apenas se houver erro para te ajudar)
if df_referencia is None:
    st.warning("⚠️ Verifique se o arquivo 'base_patrimonio.xlsx' está no GitHub com as colunas: Patrimonio e Descricao.")
elif 'cod_ref' not in df_referencia.columns:
    st.error(f"Coluna 'Patrimonio' não encontrada. Colunas lidas: {list(df_referencia.columns)}")

# Scanner
st.text_input("Aguardando Bip do Zebra:", key="campo_zebra", on_change=registrar_item)

# Tabela de Resultados
if st.session_state['lista_patrimonio']:
    df_result = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.table(df_result) # st.table é melhor para visualização rápida no celular
    
    # Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False)
    st.download_button("📥 Baixar Excel", output.getvalue(), "relatorio.xlsx")

if st.sidebar.button("🗑️ Resetar"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
