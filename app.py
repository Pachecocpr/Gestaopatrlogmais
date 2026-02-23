import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Inventory Pro | Gestão de Patrimônio", 
    page_icon="📦", 
    layout="centered"
)

# --- 1. CARREGAMENTO DA BASE MESTRE (COLUNAS B, C, E, F) ---
@st.cache_data
def carregar_base_mestre():
    try:
        # Carrega o Excel sem cabeçalho para mapear pelos índices exatos das colunas
        # Coluna B=1, C=2, E=4, F=5
        df = pd.read_excel("base_patrimonio.xlsx", engine='openpyxl', header=None)
        
        df_limpo = pd.DataFrame()
        
        # Mapeamento conforme solicitado:
        # Coluna B (Índice 1) -> PIB/Patrimônio
        df_limpo['pib_ref'] = df.iloc[:, 1].astype(str).str.strip().str.upper()
        
        # Coluna C (Índice 2) -> Descrição do Bem
        df_limpo['desc_ref'] = df.iloc[:, 2].astype(str).str.strip()
        
        # Coluna E (Índice 4) -> Código de Local
        df_limpo['cod_local_ref'] = df.iloc[:, 4].astype(str).str.strip()
        
        # Coluna F (Índice 5) -> Nome da Unidade
        df_limpo['unidade_ref'] = df.iloc[:, 5].astype(str).str.strip()
        
        return df_limpo
    except Exception as e:
        st.error(f"Erro ao acessar 'base_patrimonio.xlsx'. Verifique se o arquivo está na pasta do script. Erro: {e}")
        return None

# Inicializa a base de dados
df_referencia = carregar_base_mestre()

# --- 2. ESTADO DA SESSÃO (MEMÓRIA DO APP) ---
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# --- 3. LÓGICA DE REGISTRO (DISPARADA PELO SCANNER/ENTER) ---
def registrar_item():
    pib_lido = str(st.session_state.campo_zebra).strip().upper()
    
    if pib_lido:
        # Valores padrão para itens não encontrados
        detalhes = {
            "Descrição": "NÃO LOCALIZADO",
            "Cód. Local": "---",
            "Unidade": "---"
        }
        
        # Busca na base carregada
        if df_referencia is not None:
            resultado = df_referencia[df_referencia['pib_ref'] == pib_lido]
            if not resultado.empty:
                detalhes["Descrição"] = resultado.iloc[0]['desc_ref']
                detalhes["Cód. Local"] = resultado.iloc[0]['cod_local_ref']
                detalhes["Unidade"] = resultado.iloc[0]['unidade_ref']
        
        # Adiciona o registro à lista global (insere no início para aparecer primeiro na tabela)
        st.session_state['lista_patrimonio'].insert(0, {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "PIB/Patrimônio": pib_lido,
            "Descrição": detalhes["Descrição"],
            "Cód. Local": detalhes["Cód. Local"],
            "Unidade": detalhes["Unidade"]
        })
        
        # Feedback visual rápido
        if detalhes["Descrição"] == "NÃO LOCALIZADO":
            st.toast(f"Código {pib_lido} não encontrado!", icon="⚠️")
        else:
            st.toast(f"Item registrado com sucesso!", icon="✅")
        
        # Limpa o campo de entrada para o próximo BIP
        st.session_state.campo_zebra = ""

# --- 4. INTERFACE DO USUÁRIO ---
st.markdown("<h2 style='text-align: center;'>📦 Inventário de Patrimônio</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Aponte o leitor Zebra para o código de barras</p>", unsafe_allow_html=True)

st.divider()

# Campo de entrada principal
st.text_input(
    "Aguardando leitura...", 
    key="campo_zebra", 
    on_change=registrar_item,
    placeholder="Clique aqui e use o leitor ou digite o código"
)

# Exibição dos resultados
if st.session_state['lista_patrimonio']:
    df_result = pd.DataFrame(st.session_state['lista_patrimonio'])
    
    st.subheader(f"📋 Itens Coletados ({len(df_result)})")
    st.dataframe(df_result, use_container_width=True)
    
    # --- 5. EXPORTAÇÃO EXCEL ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False, sheet_name='Inventário_Realizado')
    
    st.download_button(
        label="📥 Baixar Relatório Excel", 
        data=output.getvalue(), 
        file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# Barra Lateral para utilitários
with st.sidebar:
    st.title("Opções")
    if st.button("🗑️ Limpar Lista Atual"):
        st.session_state['lista_patrimonio'] = []
        st.rerun()
    
    st.divider()
    st.info("""
    **Instruções:**
    1. O arquivo `base_patrimonio.xlsx` deve estar na mesma pasta.
    2. A busca é feita na Coluna B.
    3. O relatório exportado contém as informações das Colunas B, C, E e F.
    """)
