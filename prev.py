import streamlit as st
import re
import pandas as pd
import joblib

def validar_numeros(valor, nome_campo):
    # Substituir vírgula por ponto em números float
    valor = valor.replace(",", ".")
    
    # Verificar se o valor é numérico
    if not re.match(r'^\d*\.?\d+$', valor):
        return f"O campo {nome_campo} só trabalha com números"
    return float(valor)

# Dicionário para mapear as opções de Pedra
mapa_pedra = {"Quartzo": 1, "Agata": 2, "Ametista": 3, "Topázio": 4}

modelo = joblib.load('Abeto.joblib')



st.title("Modelo de Previsão - TechChallenge FIAP & Passos Mágicos")

with st.expander("Leia me"):
    st.write(
        """Este é um modelo de previsão criado para o TechChallenge da instituição FIAP em parceria com a associação Passos Mágicos. 
        O intuito desse modelo é prever, baseado nos dados de estudantes de 2022, a capacidade de um ou mais estudantes de ser indicado a uma bolsa de estudos. 
        O modelo utiliza como base a classificação-pedra, as notas de desempenho INDE, IAN, IDA, IEG, IAA e IPS."""
    )

    # ATENÇÃO em vermelho e mensagem abaixo
    st.markdown(
        '<p style="color:red; font-weight:bold;">ATENÇÃO</p>'
        '<p>É de extrema importância para a predição do modelo que todos os campos sejam preenchidos.</p>',
        unsafe_allow_html=True
    )

# Opção de seleção entre Individual e Coletivo
modo = st.radio("Escolha o modo de análise:", ["Individual", "Coletivo"])

if modo == "Individual":
    st.subheader("Preencha os dados do estudante")
    
    # Campo de seleção para Pedra
    pedra = st.selectbox("Pedra", ["Quartzo", "Agata", "Ametista", "Topázio"])
    
    # Campos de inserção manual para os indicadores numéricos
    campos_numericos = ["INDE", "IAN", "IDA", "IEG", "IAA", "IPS"]
    valores = {}
    erros = []
    
    for campo in campos_numericos:
        valor = st.text_input(f"{campo}:")
        if valor:
            resultado = validar_numeros(valor, campo)
            if isinstance(resultado, str):  # Se houver erro
                erros.append(resultado)
            else:
                valores[campo] = resultado
    
    # Botão para indicar preenchimento completo
    if st.button("Confirmar preenchimento"):
        if erros:
            for erro in erros:
                st.error(erro)
        elif len(valores) < len(campos_numericos):  # Se algum campo estiver vazio
            st.error("Todos os campos precisam estar preenchidos!")
        else:
            # Criar o DataFrame com os dados inseridos
            dados = {
                "Pedra": mapa_pedra[pedra],
                "INDE": valores["INDE"],
                "IAN": valores["IAN"],
                "IDA": valores["IDA"],
                "IEG": valores["IEG"],
                "IAA": valores["IAA"],
                "IPS": valores["IPS"],
            }
        
            df_preenchido = pd.DataFrame([dados])

            # Realizar a predição com o modelo carregado
            resultado = modelo.predict(df_preenchido)

            # Exibir a mensagem baseada no resultado da predição
            if resultado == 1:
                st.success("O Aluno se enquadra nas qualificações para ser indicado a uma bolsa")
            else:
                st.error("Infelizmente o Aluno NÃO se enquadra nas qualificações para ser indicado a uma bolsa")

if modo == 'Coletivo':
    with st.expander("Leia me"):
        st.write(
            """A edição atual do modelo só aceita arquivos do tipo CSV ou XLSX, mas fique atento:
            \n- Para arquivos CSV, garanta que o separador dos dados seja a vírgula ",".
            \n- Para arquivos XLSX, só será considerada a primeira planilha do arquivo.
            \n- É necessário que o arquivo contenha NO MÍNIMO as seguintes colunas: "RA", "Pedra", "INDE", "IAN", "IDA", "IEG", "IAA" e "IPS"
            \n- É necessário que o arquivo não contenha valores vazios ou NaN.
            """
        )
    st.subheader("Insira o arquivo")
    
    # Opção de upload de arquivo para dados coletivos (ex: CSV ou XLSX)
    uploaded_file = st.file_uploader(" ", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Carregar o arquivo conforme a extensão
        if uploaded_file.name.endswith('.csv'):
            df_coletivo = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df_coletivo = pd.read_excel(uploaded_file)

        # Exibir os dados carregados
        st.write("Dados carregados:")
        st.dataframe(df_coletivo)

        # Verificar se a coluna RA existe e isolá-la
        ra_coluna = [col for col in df_coletivo.columns if col.strip().upper() == 'RA']
        if ra_coluna:
            df_ra = df_coletivo[ra_coluna]
        else:
            st.error("Coluna RA não encontrada no arquivo.")
        
        # Isolar a coluna Pedra com maior número acompanhado
        pedra_colunas = [col for col in df_coletivo.columns if 'Pedra' in col]

        if pedra_colunas:
            # Tentar encontrar o número maior associado à palavra "Pedra"
            pedra_coluna = max(pedra_colunas, key=lambda x: int(re.search(r'(\d+)', x).group()) if re.search(r'(\d+)', x) else 0)
            df_pedra = df_coletivo[[pedra_coluna]]
        else:
            st.error("Coluna Pedra não encontrada no arquivo.")


        # Isolar a coluna INDE com maior número acompanhado
        inde_colunas = [col for col in df_coletivo.columns if 'INDE' in col.upper()]
        if inde_colunas:
            # Selecionar a coluna INDE com maior número acompanhado
            inde_coluna = max(inde_colunas, key=lambda x: int(re.search(r'(\d+)', x).group()) if re.search(r'(\d+)', x) else 0)
            df_inde = df_coletivo[[inde_coluna]]
        else:
            st.error("Coluna INDE não encontrada no arquivo.")

        # Isolar as colunas de indicadores numéricos
        indicadores = ["IAN", "IDA", "IEG", "IAA", "IPS"]
        df_indicadores = df_coletivo[indicadores]

        # Criar o novo DataFrame isolado com as transformações
        df_isolado = pd.concat([df_pedra, df_inde, df_indicadores], axis=1)

        # Renomear a coluna Pedra para "Pedra"
        coluna_pedra = [col for col in df_isolado.columns if "Pedra" in col]
        if coluna_pedra:
            df_isolado.rename(columns={coluna_pedra[0]: "Pedra"}, inplace=True)

        # Renomear a coluna INDE para "INDE"
        coluna_inde = [col for col in df_isolado.columns if "INDE" in col]
        if coluna_inde:
            df_isolado.rename(columns={coluna_inde[0]: "INDE"}, inplace=True)

        # Aplicar mapeamento para Pedra
        if "Pedra" in df_isolado.columns:
            df_isolado["Pedra"] = df_isolado["Pedra"].map(mapa_pedra)

        # Fazer a previsão com o modelo preditivo
        df_isolado["Indicação"] = modelo.predict(df_isolado)

        # Mapear os resultados da previsão para os rótulos desejados
        df_isolado["Indicação"] = df_isolado["Indicação"].map({1: "Qualificado", 0: "Não Qualificado"})

        # Criar dicionários inversos para converter de volta os números para os textos originais
        mapa_pedra_inv = {v: k for k, v in mapa_pedra.items()}

        # Aplicar os mapeamentos inversos
        df_isolado["Pedra"] = df_isolado["Pedra"].map(mapa_pedra_inv)

        # Garantir que df_ra seja a primeira coluna do DataFrame final
        df_final = pd.concat([df_ra, df_isolado], axis=1)

        # Exibir o DataFrame final
        st.write("DataFrame final com previsões:")
        st.dataframe(df_final)
    else:
        st.info("Por favor, faça o upload de um arquivo CSV ou XLSX para continuar.")
