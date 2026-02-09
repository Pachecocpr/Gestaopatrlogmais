import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Inventário Zebra", layout="centered", page_icon="🦓")

# Inicializa a lista de registros na memória da sessão
if 'lista_patrimonio' not in st.session_state:
    st.session_state['lista_patrimonio'] = []

# Função disparada pelo "Enter" do Zebra
def registrar_e_limpar():
    codigo = st.session_state.campo_zebra
    if codigo:
        # Cria o registro com os dados atuais das configurações
        novo_item = {
            "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Código": codigo,
            "Unidade": st.session_state.get('unidade_lote', 'Unidade 1'),
            "Descrição": st.session_state.get('desc_lote', ''),
            "Etiqueta": st.session_state.get('etiqueta_lote', 'Metal')
        }
        # Adiciona à lista
        st.session_state['lista_patrimonio'].append(novo_item)
        # Limpa o campo de texto para o próximo bip
        st.session_state.campo_zebra = ""
        st.toast(f"Item {codigo} registrado!", icon="✅")

st.title("🦓 Sistema de Inventário (Leitor Zebra)")

# --- CONFIGURAÇÕES DE LOTE ---
# Defina isso uma vez e saia bipando os itens iguais
st.subheader("⚙️ Configurações do Lote")
c1, c2 = st.columns(2)
with c1:
    st.radio("Unidade:", ["Unidade 1", "Unidade 2"], key="unidade_lote", horizontal=True)
    st.selectbox("Tipo de Etiqueta:", ["Metal", "Papel", "Poliéster"], key="etiqueta_lote")
with c2:
    st.text_input("Descrição padrão para este lote:", key="desc_lote", placeholder="Ex: Cadeira de Escritório")

st.divider()

# --- CAMPO DE ENTRADA DO ZEBRA ---
st.subheader("🔍 Entrada do Leitor")
st.info("Mantenha o cursor piscando no campo abaixo para bipar.")

st.text_input(
    "Aguardando Bip...", 
    key="campo_zebra", 
    on_change=registrar_e_limpar, # O Enter do Zebra aciona isso automaticamente
    placeholder="Bipe o código aqui"
)

# --- TABELA E EXCEL ---
if st.session_state['lista_patrimonio']:
    st.divider()
    df = pd.DataFrame(st.session_state['lista_patrimonio'])
    st.dataframe(df, use_container_width=True)
    
    # Gerar Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Baixar Relatório Atualizado (Excel)",
        data=output.getvalue(),
        file_name=f"inventario_zebra_{datetime.now().strftime('%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Barra lateral para controle
if st.sidebar.button("🗑️ Limpar Lista e Recomeçar"):
    st.session_state['lista_patrimonio'] = []
    st.rerun()
