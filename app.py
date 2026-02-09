import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Patrimônio Logística", page_icon="📦", layout="centered")

# Inicializa a lista de patrimônio na memória da sessão (evita que apague ao interagir)
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# Título do App
st.title("📦 Gestão de Patrimônio")
st.caption("Versão Otimizada: Use com Binary Eye (Keyboard Wedge) ou Leitor Zebra.")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Painel de Controle")
if st.sidebar.button("🗑️ Limpar Lista Atual"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()

# --- CAMPO DE LEITURA (O "CORAÇÃO" DO APP) ---
st.subheader("🔍 Escanear Item")
# O cursor precisa estar focado aqui para o scanner "digitar" o código
codigo_lido = st.text_input("Clique abaixo antes de bipar:", key="input_principal", placeholder="Aguardando código...")

# --- FORMULÁRIO DE REGISTRO ---
if codigo_lido:
    st.success(f"✅ Item identificado: **{codigo_lido}**")
    
    # O formulário organiza os dados e limpa os campos após o envio
    with st.form("registro_bem", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            unidade = st.radio("📍 Unidade Alocada:", ["Unidade 1", "Unidade 2"], horizontal=True)
            etiqueta = st.selectbox("🏷️ Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"])
        
        with col2:
            descricao = st.text_input("📝 Descrição do Bem:", placeholder="Ex: Empilhadeira, Cadeira, PC")
            obs = st.text_input("⚠️ Observações:")

        # Botão para salvar na tabela
        btn_salvar = st.form_submit_button("💾 Salvar Registro")

        if btn_salvar:
            novo_registro = {
                "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Código Patrimônio": codigo_lido,
                "Descrição": descricao,
                "Unidade": unidade,
                "Tipo Etiqueta": etiqueta,
                "Observação": obs
            }
            # Adiciona à lista
            st.session_state['lista_patrimonio'].append(novo_registro)
            st.toast(f"Item {codigo_lido} salvo!", icon='✔️')
            st.info("💡 Clique no campo de busca para o próximo bip.")

# --- TABELA E EXPORTAÇÃO EXCEL ---
if st.session_state['lista_patrimonio']:
    st.divider()
    st.subheader("📋 Itens Registrados nesta Sessão")
    
    # Criar DataFrame para exibição
    df_lista = pd.DataFrame(st.session_state['lista_patrimonio'])
    
    # Exibe a tabela no app
    st.dataframe(df_lista, use_container_width=True)

    # Lógica para criar o arquivo Excel para download
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_lista.to_excel(writer, index=False, sheet_name='Patrimonio')
    
    # Botão de Download
    st.download_button(
        label="📥 Baixar Relatório Excel",
        data=buffer.getvalue(),
        file_name=f"patrimonio_{datetime.now().strftime('%d_%m_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Nenhum item na lista. Comece bipando um código de barras!")
