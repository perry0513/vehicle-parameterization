import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from sklearn.preprocessing import StandardScaler

import pandas as pd
from net import Net

class Dataset(torch.utils.data.Dataset):

  def __init__(self, X, y, scale_data=True):
    if not torch.is_tensor(X) and not torch.is_tensor(y):
      # Apply scaling if necessary
      if scale_data:
          X = StandardScaler().fit_transform(X)
      self.X = torch.Tensor(X)
      self.y = torch.Tensor(y)

  def __len__(self):
      return len(self.X)

  def __getitem__(self, i):
      return self.X[i], self.y[i]

def createDataset(csv_file):
    df = pd.read_csv(csv_file)
    X = []
    y = []
    for i, row in df.iterrows():
        row = list(row[1:])
        X.append(row[:7])
        y.append([row[7]])
    return Dataset(X, y)

if __name__ == '__main__':
    model = Net()

    dataset = createDataset('result.csv')
    trainloader = torch.utils.data.DataLoader(dataset, batch_size=10, shuffle=True, num_workers=0)

    epochs = 50
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for i in range(epochs):
        l = 0
        for input, target in trainloader:

            optimizer.zero_grad()   # zero the gradient buffers
            output = model(input)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()    # Does the update

            l += loss.item()
            # print(loss.item())
        print(f'Epoch {i} loss: {l/500}')

    torch.save(model.state_dict(), 'model.pt')
            
