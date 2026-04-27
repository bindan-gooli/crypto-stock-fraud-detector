import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_crypto_data(n_points=1000, symbol="BTC/USD"):
    """
    Generates synthetic crypto price data with injected anomalies.
    """
    np.random.seed(42)
    
    # Base price using Geometric Brownian Motion
    start_price = 50000
    returns = np.random.normal(0.0001, 0.01, n_points)
    price = start_price * np.exp(np.cumsum(returns))
    
    # Generate timestamps
    base_time = datetime.now() - timedelta(hours=n_points)
    timestamps = [base_time + timedelta(hours=i) for i in range(n_points)]
    
    # Generate volume
    volume = np.random.gamma(shape=2, scale=100, size=n_points) * 10
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'symbol': symbol,
        'price': price,
        'volume': volume
    })
    
    # Inject Anomalies (Pump and Dump)
    # Scenario: Sudden volume spike followed by price surge and then crash
    anomaly_idx = np.random.choice(range(100, n_points-50), size=3, replace=False)
    df['is_fraud'] = 0
    
    for idx in anomaly_idx:
        # Pump phase (5 points)
        df.loc[idx:idx+5, 'volume'] *= 10
        df.loc[idx:idx+5, 'price'] *= (1 + np.linspace(0, 0.3, 6))
        # Crash phase (3 points)
        df.loc[idx+6:idx+8, 'price'] *= 0.6
        df.loc[idx:idx+8, 'is_fraud'] = 1
        
    return df

if __name__ == "__main__":
    df = generate_crypto_data()
    df.to_csv("data/synthetic_crypto_data.csv", index=False)
    print(f"Generated {len(df)} points of synthetic data with anomalies.")
