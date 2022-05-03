import torch
import pandas as pd
from sklearn.preprocessing import StandardScaler


def createDataset(csv_file, seed=0):
    df = pd.read_csv(csv_file)
    df.sample(frac=1, random_state=seed) # random shuffle
    X, y = [], []
    for i, row in df.iterrows():
        row = list(row[1:])
        X.append(row[:7])
        y.append([row[7]])
    
    # Train-test split
    n = int(len(X) * 0.8)
    X_train, y_train, X_test, y_test = X[:n], y[:n], X[n:], y[n:]

    # Normalization
    scaler = StandardScaler().fit(X)
    X_train= scaler.transform(X_train)
    X_test= scaler.transform(X_test)

    # print("Data stats:", scaler.mean_, scaler.scale_)

    return Dataset(X_train, y_train), Dataset(X_test, y_test)


class Dataset(torch.utils.data.Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i], self.y[i]