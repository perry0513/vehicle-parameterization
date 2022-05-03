import os 
import pandas as pd

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from surrogates.dataset import createDataset
from surrogates.net import Net

DATA_PATH = os.path.join('surrogates', 'result.csv')
MODEL_PATH = os.path.join('surrogates', 'model.pt')

'''
2-layered NN + MSE loss
 - hidden_size=30 => test loss=455.2901
 - hidden_size=40 => test loss=446.6851
 - hidden_size=50 => test loss=444.3011

3-layered NN + MSE loss
 - hidden_size=30 => test loss=455.2501
 - hidden_size=40 => test loss=458.7501
 - hidden_size=50 => test loss=447.5958
'''

if __name__ == '__main__':

    # seeding
    seed = 0
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    train_dataset, test_dataset = createDataset(DATA_PATH, seed=seed)
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=1000, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=1000)

    epochs = 2000
    criterion = nn.MSELoss() # nn.SmoothL1Loss() 
    net = Net().cuda()
    optimizer = optim.Adam(net.parameters(), lr=0.001)
    best_mse = float('inf')
    for i in range(epochs):
        training_loss, test_loss = 0, 0
        training_mse, test_mse = 0, 0
        training_mae, test_mae = 0, 0
        net.train()
        for input, target in train_loader:
            target = target.cuda()
            pred = net(input.cuda())
            loss = criterion(pred, target)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()    

            training_loss += loss.item()
            training_mse += F.mse_loss(pred, target, reduction='sum').item()
            training_mae += F.smooth_l1_loss(pred, target, reduction='sum').item()
            # if i % 200 == 0:
            #     print(training_loss)

        net.eval()
        for input, target in test_loader:
            target = target.cuda()
            with torch.no_grad():
                pred = net(input.cuda())
            test_loss += criterion(net(input.cuda()), target.cuda()).item()
            test_mse += F.mse_loss(pred, target, reduction='sum').item()
            test_mae += F.smooth_l1_loss(pred, target, reduction='sum').item()

        # if i % 100 == 0:
        #     print(net(input.cuda()).detach().cpu()[:10], '\n', target.detach().cpu()[:10])

        training_mse, training_mae = training_mse / len(train_dataset), training_mae / len(train_dataset)
        test_mse, test_mae = test_mse / len(test_dataset), test_mae / len(test_dataset)

        if i % 100 == 0:
            print(f'Epoch {i:5d} | train/test mse: {training_mse:.4f}/{test_mse:.4f} | ' + 
                f'train/test mae: {training_mae:.4f}/{test_mae:.4f}')
        
        if test_mse <= best_mse:
            torch.save(net.state_dict(), MODEL_PATH)
            best_mse = test_mse



