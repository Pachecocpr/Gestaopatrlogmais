import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Património Logística", layout="centered")

# Inicialização de variáveis de estado
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# Função para processar o salvamento e limpar o campo
def salvar_e_limpar():
    codigo = st.session_state.campo_leitura
    if codigo:
        # Cria o registo com os dados atuais
        novo_registro = {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Código": codigo,
            "Descrição": st.session_state.get('desc_input', ''),
            "Unidade": st.session_state.get('unidade_input', 'Unidade 1'),
            "Etiqueta": st.session_state.get('etiqueta_input', 'Metal')
        }
        # Adiciona à lista
        st.session_state['lista_patrimonio'].append(novo_registro)
        # Limpa o campo de leitura para a próxima inserção
        st.session_state.campo_leitura = ""
        st.toast(f"Item {codigo} registado com sucesso!", icon="✅")

st.title("📦 Gestão de Património")
st.caption("Modo de Inserção Contínua (Auto-save & Clear)")

# --- CONFIGURAÇÕES PRÉVIAS (Ficam salvas para os próximos bips) ---
st.subheader("⚙️ Configurações do Lote")
col1, col2 = st.columns(2)

with col1:
    st.radio("Unidade Atual:", ["Unidade 1", "Unidade 2"], 
             key="unidade_input", horizontal=True)
    st.selectbox("Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"], 
                 key="etiqueta_input")

with col2:
    st.text_input("Descrição Padrão:", placeholder="Ex: Cadeira Escritório", 
                 key="desc_input")

st.divider()

# --- CAMPO DE LEITURA COM AUTO-LIMPEZA ---
st.subheader("🔍 Leitura de Código")
# O on_change chama a função assim que o Enter é pressionado
st.text_input(
    "Clique aqui e bibe o código:", 
    key="campo_leitura", 
    on_change=salvar_e_limpar,
    placeholder="Aguardando bip do leitor..."
)

# --- VISUALIZAÇÃO E EXPORTAÇÃO ---
if st.session_state['lista_patrimonio']:
    st.markdown("---")
    st.subheader("📋 Itens Registados")
    
    df = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df, use_container_width=True)
    
    # Gerar ficheiro Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Patrimonio')
    
    st.download_button(
        label="📥 Descarregar Relatório Excel",
        data=output.getvalue(),
        file_name=f"patrimonio_{datetime.now().strftime('%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Botão na barra lateral para reiniciar o trabalho
if st.sidebar.button("Reiniciar Lista"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
