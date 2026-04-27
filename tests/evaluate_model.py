import pandas as pd
import numpy as np
from src.data_generator import generate_crypto_data
from src.model import FraudDetector
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def evaluate():
    print("🚀 Starting Model Evaluation...")
    
    # 1. Generate a large test dataset (unseen by training in current session)
    print("Generating 5000 points of test data...")
    df = generate_crypto_data(n_points=5000)
    
    detector = FraudDetector()
    processed_df = detector.prepare_features(df)
    
    # 2. Train on a separate training set
    print("Training on 2000 points...")
    train_df = generate_crypto_data(n_points=2000)
    train_processed = detector.prepare_features(train_df)
    detector.train(train_processed)
    
    # 3. Predict on test set
    print("Evaluating on test set...")
    probs = detector.predict(processed_df)
    y_true = processed_df['is_fraud']
    y_pred = (probs > 0.5).astype(int)
    
    # 4. Calculate Metrics
    report = classification_report(y_true, y_pred, output_dict=True)
    auc = roc_auc_score(y_true, probs)
    cm = confusion_matrix(y_true, y_pred)
    
    print("\n--- PERFORMANCE SUMMARY ---")
    print(f"Overall Accuracy: {report['accuracy']:.4f}")
    print(f"Fraud Precision: {report['1']['precision']:.4f}")
    print(f"Fraud Recall:    {report['1']['recall']:.4f}")
    print(f"Fraud F1-Score:  {report['1']['f1-score']:.4f}")
    print(f"ROC AUC Score:   {auc:.4f}")
    print("\nConfusion Matrix:")
    print(cm)
    
    return report, auc

if __name__ == "__main__":
    evaluate()
