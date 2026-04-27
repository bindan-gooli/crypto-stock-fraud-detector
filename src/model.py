import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import os

class FraudDetector:
    def __init__(self):
        self.iso_forest = IsolationForest(contamination=0.05, random_state=42)
        self.classifier = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        
    def prepare_features(self, df):
        # Feature Engineering
        df = df.copy()
        df['price_change'] = df['price'].pct_change()
        df['vol_change'] = df['volume'].pct_change()
        df['volatility'] = df['price'].rolling(window=10).std()
        
        # Simple technical indicators
        df['sma_20'] = df['price'].rolling(window=20).mean()
        df['dist_from_sma'] = (df['price'] - df['sma_20']) / df['sma_20']
        
        # RSI (Relative Strength Index)
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['std_20'] = df['price'].rolling(window=20).std()
        df['bb_upper'] = df['sma_20'] + (df['std_20'] * 2)
        df['bb_lower'] = df['sma_20'] - (df['std_20'] * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['sma_20']
        
        return df.dropna()

    def train(self, df):
        features = ['price', 'volume', 'price_change', 'vol_change', 'volatility', 'dist_from_sma', 'rsi', 'bb_width']
        X = df[features]
        
        # Unsupervised part: Isolation Forest (Always train)
        self.iso_forest.fit(X)
        iso_preds = self.iso_forest.predict(X)
        df['iso_score'] = np.where(iso_preds == -1, 1, 0)
        
        # Supervised part: XGBoost (If labels exist, use them. Otherwise use self-supervised pseudo-labels)
        if 'is_fraud' in df.columns:
            y = df['is_fraud']
            print("📊 Training with Ground Truth labels.")
        else:
            # Self-Supervised: Use the unsupervised anomalies as pseudo-labels for the classifier
            y = df['iso_score']
            print("🤖 Training with Self-Supervised Pseudo-labels (Real-time Market Data).")
            
        X_plus = df[features + ['iso_score']]
        X_train, X_test, y_train, y_test = train_test_split(X_plus, y, test_size=0.2, random_state=42)
        
        self.classifier.fit(X_train, y_train)
        
        try:
            preds = self.classifier.predict(X_test)
            print("Model Performance (Self-Supervised):")
            print(classification_report(y_test, preds))
        except Exception as e:
            print(f"Metrics calculation failed: {e}")
        
        # Save models
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.iso_forest, "models/iso_forest.joblib")
        joblib.dump(self.classifier, "models/xgb_classifier.joblib")
        
    def predict(self, df):
        features = ['price', 'volume', 'price_change', 'vol_change', 'volatility', 'dist_from_sma', 'rsi', 'bb_width']
        X = df[features]
        
        iso_scores = self.iso_forest.predict(X)
        df['iso_score'] = np.where(iso_scores == -1, 1, 0)
        
        X_plus = df[features + ['iso_score']]
        probs = self.classifier.predict_proba(X_plus)[:, 1]
        return probs

class TradingStrategy:
    """
    Generates high-precision trading signals based on technical indicators 
    and fraud risk filtering. Supports dynamic parameter optimization.
    """
    def __init__(self, rsi_buy=35, rsi_sell=65, bb_mult=1.02):
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell
        self.bb_mult = bb_mult

    def generate_signals(self, df):
        signals = []
        for i in range(len(df)):
            row = df.iloc[i]
            risk = row['fraud_prob']
            rsi = row['rsi']
            price = row['price']
            bb_lower = row['bb_lower']
            bb_upper = row['bb_upper']
            
            # Strategy with dynamic thresholds
            if rsi < self.rsi_buy and price <= bb_lower * self.bb_mult and risk < 0.3:
                signals.append("BUY")
            elif (rsi > self.rsi_sell and price >= bb_upper * (2 - self.bb_mult)) or risk > 0.8:
                signals.append("SELL")
            else:
                signals.append("HOLD")
        
        return signals
if __name__ == "__main__":
    from src.data_generator import generate_crypto_data
    df = generate_crypto_data(n_points=2000)
    
    detector = FraudDetector()
    processed_df = detector.prepare_features(df)
    detector.train(processed_df)
