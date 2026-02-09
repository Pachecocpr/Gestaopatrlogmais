import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Patrimônio Logística", layout="centered", page_icon="📦")

# Inicialização da lista de patrimônio se não existir
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# Função de Callback: Salva o dado e limpa o campo imediatamente
def processar_leitura():
    codigo = st.session_state.campo_scan
    if codigo:
        # Registra os dados usando os estados atuais dos outros campos
        novo_item = {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Código": codigo,
            "Descrição": st.session_state.get('desc_padrao', ''),
            "Unidade": st.session_state.get('unidade_sel', 'Unidade 1'),
            "Etiqueta": st.session_state.get('etiqueta_sel', 'Metal')
        }
        # Adiciona à lista permanente da sessão
        st.session_state['lista_patrimonio'].append(novo_item)
        
        # Limpa o campo de texto para o próximo "bip"
        st.session_state.campo_scan = ""
        st.toast(f"Código {codigo} registrado!", icon="✅")

# --- INTERFACE ---
st.title("📦 Gestão de Patrimônio")
st.write("Otimizado para App **Barcodes (TeaCapps)**")

# --- CONFIGURAÇÕES DE LOTE ---
# Estas opções ficam salvas enquanto você bipa vários itens iguais
st.subheader("⚙️ Definições do Lote")
c1, c2 = st.columns(2)

with c1:
    st.radio("Unidade Atual:", ["Unidade 1", "Unidade 2"], 
             key="unidade_sel", horizontal=True)
    st.selectbox("Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"], 
                 key="etiqueta_sel")

with c2:
    st.text_input("Descrição Padrão:", placeholder="Ex: Paleteira Hidráulica", 
                 key="desc_padrao")

st.divider()

# --- CAMPO DE ENTRADA (ONDE O APP BARCODES VAI ATUAR) ---
st.subheader("🔍 Scanner")
st.text_input(
    "Clique aqui para iniciar a leitura:", 
    key="campo_scan", 
    on_change=processar_leitura, # Dispara a função ao receber o 'Enter' do App
    placeholder="Aguardando bip..."
)

# --- TABELA E EXPORTAÇÃO ---
if st.session_state['lista_patrimonio']:
    st.markdown("---")
    df = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df, use_container_width=True)
    
    # Gerar Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Patrimonio')
    
    st.download_button(
        label="📥 Baixar Relatório Excel",
        data=buffer.getvalue(),
        file_name=f"inventario_{datetime.now().strftime('%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Botão para reiniciar sessão
if st.sidebar.button("Reiniciar Inventário"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
