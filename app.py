import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuração da página para modo largo (melhor visualização da tabela)
st.set_page_config(page_title="Gestão de Patrimônio - Leitor Zebra", layout="wide")

# --- INICIALIZAÇÃO DO ESTADO ---
# Criamos uma lista na memória do navegador para armazenar as leituras da sessão
if 'historico_leituras' not in st.session_state:
    st.session_state.historico_leituras = []

# --- INTERFACE ---
st.title("📦 Sistema de Inventário e Etiquetas")

# Seleção do tipo de etiqueta (Radio buttons para seleção rápida)
tipo_etiqueta = st.radio(
    "Selecione o tipo de etiqueta para as próximas leituras:",
    ["Papel", "Metal"],
    horizontal=True
)

# Campo de entrada para o Leitor Zebra
# O leitor simula um teclado e aperta 'Enter', o que aciona o processamento no Streamlit
codigo_lido = st.text_input(
    "Aguardando leitura do código de barras...", 
    key="input_zebra", 
    placeholder="Passe o leitor no patrimônio",
    help="Clique aqui antes de começar a bipar."
)

# --- PROCESSAMENTO DOS DADOS ---
arquivo_entrada = "base_patrimonio.xlsx"

if os.path.exists(arquivo_entrada):
    try:
        # Carregamos a base
        df_base = pd.read_excel(arquivo_entrada)

        # Mapeamento conforme as instruções:
        # Coluna B (Índice 1) = Patrimônio/Busca
        # Coluna C (Índice 2) = Descrição do Bem
        # Coluna E (Índice 4) = Código do Local
        # Coluna F (Índice 5) = Nome da Unidade
        
        if codigo_lido:
            # Busca o código na Coluna B (segunda coluna do Excel)
            # Convertemos ambos para string para evitar erro de comparação número/texto
            busca = df_base[df_base.iloc[:, 1].astype(str) == str(codigo_lido)]

            if not busca.empty:
                # Extrai as informações das colunas B, C, E e F
                novo_item = {
                    "Patrimônio": busca.iloc[0, 1],
                    "Descrição do Bem": busca.iloc[0, 2],
                    "Código do Local": busca.iloc[0, 4],
                    "Nome da Unidade": busca.iloc[0, 5],
                    "Tipo Etiqueta": tipo_etiqueta
                }

                # Evita duplicar o mesmo patrimônio na lista da sessão atual
                patrimonios_existentes = [item["Patrimônio"] for item in st.session_state.historico_leituras]
                
                if novo_item["Patrimônio"] not in patrimonios_existentes:
                    st.session_state.historico_leituras.insert(0, novo_item) # Adiciona no topo
                    st.toast(f"✅ Item {codigo_lido} adicionado!", icon='🎉')
                else:
                    st.warning(f"⚠️ O item {codigo_lido} já foi lido anteriormente.")
            else:
                st.error(f"❌ Código {codigo_lido} não encontrado na Coluna B da base.")

        # --- EXIBIÇÃO DO RELATÓRIO EM TEMPO REAL ---
        if st.session_state.historico_leituras:
            st.write("### Relatório de Itens Lidos")
            df_relatorio = pd.DataFrame(st.session_state.historico_leituras)
            
            # Mostra a tabela formatada
            st.dataframe(df_relatorio, use_container_width=True)

            # Botões de Ação
            col1, col2 = st.columns(2)
            
            with col1:
                # Gerar Excel para download
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_relatorio.to_excel(writer, index=False, sheet_name='Leituras')
                
                st.download_button(
                    label="📥 Baixar Relatório (XLSX)",
                    data=output.getvalue(),
                    file_name=f"relatorio_patrimonio_{tipo_etiqueta.lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col2:
                if st.button("🗑️ Limpar Lista Atual"):
                    st.session_state.historico_leituras = []
                    st.rerun()

    except Exception as e:
        st.error(f"Erro ao processar o arquivo Excel: {e}")
else:
    st.error(f"Arquivo '{arquivo_entrada}' não encontrado no repositório.")
    st.info("Suba o arquivo 'base_patrimonio.xlsx' para a mesma pasta deste app no GitHub.")

# Instruções de rodapé
st.markdown("---")
st.caption("Instruções: 1. Certifique-se de que o arquivo Excel está na raiz. 2. Clique no campo de texto para focar o leitor Zebra. 3. O relatório será montado conforme você bipa.")
