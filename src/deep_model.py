import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dim, seq_len):
        super(LSTMAutoencoder, self).__init__()
        self.seq_len = seq_len
        self.input_dim = input_dim
        
        # Encoder
        self.encoder = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        # Decoder
        self.decoder = nn.LSTM(hidden_dim, input_dim, batch_first=True)
        self.output_layer = nn.Linear(input_dim, input_dim)

    def forward(self, x):
        # x shape: (batch, seq_len, input_dim)
        _, (hidden, _) = self.encoder(x)
        # hidden shape: (1, batch, hidden_dim)
        
        # Repeat hidden state for each timestep in sequence
        x = hidden.repeat(self.seq_len, 1, 1).transpose(0, 1)
        # x shape: (batch, seq_len, hidden_dim)
        
        x, _ = self.decoder(x)
        # x shape: (batch, seq_len, input_dim)
        
        return self.output_layer(x)

class DeepFraudDetector:
    def __init__(self, input_dim=8, hidden_dim=16, seq_len=10):
        self.seq_len = seq_len
        self.model = LSTMAutoencoder(input_dim, hidden_dim, seq_len)
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.scaler = StandardScaler()

    def prepare_sequences(self, df, features):
        data = self.scaler.fit_transform(df[features])
        sequences = []
        for i in range(len(data) - self.seq_len):
            sequences.append(data[i:i+self.seq_len])
        return torch.FloatTensor(np.array(sequences))

    def train_model(self, df, features, epochs=20):
        sequences = self.prepare_sequences(df, features)
        self.model.train()
        for epoch in range(epochs):
            self.optimizer.zero_grad()
            output = self.model(sequences)
            loss = self.criterion(output, sequences)
            loss.backward()
            self.optimizer.step()
            if (epoch+1) % 5 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')

    def get_anomaly_scores(self, df, features):
        sequences = self.prepare_sequences(df, features)
        self.model.eval()
        with torch.no_grad():
            output = self.model(sequences)
            # Calculate MSE for each sequence
            mse = torch.mean((output - sequences)**2, dim=(1, 2))
            
        # Pad with zeros for the first seq_len points
        scores = np.zeros(len(df))
        scores[self.seq_len:] = mse.numpy()
        return scores

if __name__ == "__main__":
    # Test
    from src.data_generator import generate_crypto_data
    from src.model import FraudDetector
    
    df = generate_crypto_data(n_points=500)
    detector = FraudDetector()
    processed_df = detector.prepare_features(df)
    
    features = ['price', 'volume', 'price_change', 'vol_change', 'volatility', 'dist_from_sma', 'rsi', 'bb_width']
    deep_detector = DeepFraudDetector(input_dim=len(features))
    deep_detector.train_model(processed_df, features, epochs=10)
    scores = deep_detector.get_anomaly_scores(processed_df, features)
    print(f"Generated {len(scores)} deep anomaly scores.")
