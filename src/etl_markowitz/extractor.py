# ETL-markowitz/etl_markowitz/extractor.py

import yfinance as yf
import pandas as pd
from datetime import datetime
import os # Importamos a biblioteca 'os' para lidar com caminhos de arquivos

# --- Configurações Iniciais ---
TICKERS = [
    "AAPL", "MSFT", "JPM", "PG", "XOM", 
    "MGLU3.SA", "PETR4.SA"
]
START_DATE = "2020-01-01"
END_DATE = datetime.now().strftime('%Y-%m-%d')
OUTPUT_DIR = "data" # Nome da pasta onde salvaremos os dados
FILE_NAME = "raw_stock_prices.parquet" # Nome do nosso arquivo de saída

# --- Funções do ETL ---
def fetch_stock_data(tickers, start_date, end_date):
    """Busca os dados históricos de preços de fechamento ajustado."""
    print(f"Buscando dados para {len(tickers)} ativos...")
    data = yf.download(tickers, start=start_date, end=end_date)['Close']
    data.dropna(inplace=True)
    print("Dados extraídos com sucesso!")
    return data

def save_to_parquet(df, directory, file_name):
    """Salva o DataFrame em um arquivo Parquet em um diretório específico."""
    # Cria o diretório se ele não existir
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Diretório '{directory}' criado.")
        
    file_path = os.path.join(directory, file_name)
    print(f"Salvando dados em {file_path}...")
    df.to_parquet(file_path)
    print("Dados salvos com sucesso!")

# --- Execução Principal ---
if __name__ == "__main__":
    # 1. Extração
    price_data = fetch_stock_data(TICKERS, START_DATE, END_DATE)
    
    # 2. Salvamento (Carregamento para um arquivo local)
    save_to_parquet(price_data, OUTPUT_DIR, FILE_NAME)
    
    # Mostra uma amostra dos dados
    print("\n--- Amostra dos Dados Salvos ---")
    print(price_data.head())