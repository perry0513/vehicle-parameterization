import torch
import torch.nn as nn
import torch.nn.functional as F
 
class Net(nn.Module):
    def __init__(self, hidden_size=50):
        super(Net, self).__init__()
        self.hidden_size = hidden_size
        self.fc = nn.Sequential(
            nn.Linear(7, hidden_size),
            nn.ReLU(),
            # nn.Linear(hidden_size, hidden_size),
            # nn.ReLU(),
            nn.Linear(hidden_size, 1),
            nn.ReLU()
        )

    def forward(self, x):
        x = self.fc(x)
        return x

