import pandas as pd
import logging
import os
from dotenv import load_dotenv
from pypfopt import expected_returns, risk_models, EfficientFrontier
from . import settings 
from . import azure_connector 

load_dotenv()

# Configura o logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

def optimize_portfolio(price_data):
    """Calcula o portfólio ótimo (Máximo Sharpe Ratio)."""
    logging.info("Iniciando otimização do portfólio...") 
    mu = expected_returns.mean_historical_return(price_data)
    S = risk_models.sample_cov(price_data)
    ef = EfficientFrontier(mu, S)
    weights = ef.max_sharpe()
    cleaned_weights = ef.clean_weights()
    logging.info("Otimização concluída!") 
    
    expected_return, annual_volatility, sharpe_ratio = ef.portfolio_performance(verbose=False)
    
    weights_df = pd.DataFrame.from_records(
        list(cleaned_weights.items()), columns=['Ativo', 'Peso']
    ).set_index('Ativo')
    
    performance_df = pd.DataFrame({
        'Métrica': ['Retorno Anual Esperado', 'Volatilidade Anual', 'Índice de Sharpe'],
        'Valor': [expected_return, annual_volatility, sharpe_ratio]
    }).set_index('Métrica')
    
    return weights_df, performance_df

def run_transformation(): 
    """
    Executa o pipeline de transformação completo:
    1. Baixa os dados da Zona Bruta.
    2. Calcula o portfólio ótimo.
    3. Faz o upload dos resultados para a Zona Processada.
    """
    if not AZURE_CONNECTION_STRING:
        logging.error("A variável de ambiente AZURE_STORAGE_CONNECTION_STRING não foi encontrada.") 
        return

    # 1. Baixar os dados brutos do Data Lake
    price_data = azure_connector.download_blob_to_dataframe( 
        connection_string=AZURE_CONNECTION_STRING,
        container_name=settings.RAW_CONTAINER_NAME, 
        blob_name=settings.RAW_BLOB_NAME 
    )
    
    if price_data is not None:
        # 2. Transformação: Otimizar o portfólio
        optimal_weights, portfolio_performance = optimize_portfolio(price_data)
        
        logging.info("--- Pesos Ótimos do Portfólio ---") 
        logging.info(f"\n{optimal_weights}") 
        
        logging.info("--- Performance Esperada do Portfólio ---") 
        logging.info(f"\n{portfolio_performance}") 
        
        # 3. Fazer o upload dos resultados de volta para o Azure
        azure_connector.upload_dataframe_to_adls( 
            df=optimal_weights, 
            connection_string=AZURE_CONNECTION_STRING, 
            container_name=settings.PROCESSED_CONTAINER_NAME, 
            blob_name=settings.WEIGHTS_BLOB_NAME 
        )
        azure_connector.upload_dataframe_to_adls( 
            df=portfolio_performance, 
            connection_string=AZURE_CONNECTION_STRING, 
            container_name=settings.PROCESSED_CONTAINER_NAME,
            blob_name=settings.PERFORMANCE_BLOB_NAME 
        )

# A seção de execução principal agora só chama a função 'run'
if __name__ == "__main__":
    run_transformation()