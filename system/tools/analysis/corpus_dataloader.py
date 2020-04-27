from torch.utils.data import Dataset
import torch.nn.utils.rnn as rnn_utils
import numpy as np
import pickle
import os
from config import Cfg


class PakedData(Dataset):
    def __init__(self, data, phase='train'):
        super(PakedData, self).__init__()
        if phase == 'train':
            self.data = data
        else:
            self.data = [data]
        self.phase = phase

    def __len__(self):
        if self.phase == 'train':
            assert len(self.data[0]) == len(self.data[1])
        return len(self.data[0])

    def __getitem__(self, idx):
        ret = {}
        if self.phase == 'train':
            ret['data'] = self.data[0][idx]
            ret['length'] = len(ret['data'][ret['data'] != Cfg().vocab_size - 1])
            ret['label'] = self.data[1][idx]
        else:

            ret['data'] = np.array(self.data[idx])
            ret['length'] = len(ret['data'][ret['data'] != Cfg().vocab_size - 1])
        return ret


class MyTrainValData(Dataset):
    def __init__(self, data):
        super(MyTrainValData, self).__init__()
        self.data = data
        self.embeddings = pickle.load(
            open(os.path.join(Cfg().word2vec_from_scratch, 'emb_weights.pkl'), 'rb'))

    def __len__(self):
        assert len(self.data[0]) == len(self.data[1])
        return len(self.data[0])

    def __getitem__(self, idx):
        ret = {}
        ret['data'] = self.embeddings[self.data[0][idx]]
        ret['label'] = self.data[1][idx]
        print(ret['data'])
        os._exit(0)
        return ret

# def collate_fn(data):
#     data.sort(key=lambda x: len(x), reverse=True)
#     data_length = [len(sq) for sq in data]
#     return data, data_length
