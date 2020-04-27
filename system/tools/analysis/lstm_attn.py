# coding: UTF-8
import torch
import torch.nn as nn
import os
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence
from torch.nn.utils.rnn import pad_packed_sequence
import numpy as np
import pickle
from config import Cfg


class Config(object):
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # 设备
        self.vec = os.path.join(Cfg().word2vec_from_scratch, '25_embeddings.pkl')
        self.vocab = os.path.join(Cfg().word2vec_from_scratch, '25_vocab.pkl')
        self.dropout = 0.15  # 随机失活
        self.require_improvement = 1000  # 若超过1000batch效果还没提升，则提前结束训练
        self.num_classes = 7  # 类别数
        self.n_vocab = 0  # 词表大小，在运行时赋值
        self.num_epochs = 200  # epoch数
        self.info_freq = 100
        self.val_freq = 3000
        self.model_save_path = Cfg().checkpoint['senti']
        self.batch_size = 32 # mini-batch大小
        self.pad_size = 32  # 每句话处理成的长度(短填长切)
        self.learning_rate = 0.001  # 学习率
        self.embed = 100


config = Config()


class BiLstm(nn.Module):
    def __init__(self, hidden_size=128, input_size=100, bidirectional=True, num_layers=2, num_classes=7):
        super(BiLstm, self).__init__()

        weights = torch.from_numpy(
            pickle.load(open(os.path.join(Cfg().word2vec_from_scratch, '25_embeddings.pkl'), 'rb'))
        ).float()
        self.embeddings = nn.Embedding.from_pretrained(weights, freeze=True)

        self.model_name = 'BLSTM'
        self.hidden_size = hidden_size
        self.input_size = input_size
        self.bidirectional = bidirectional
        self.num_layers = num_layers
        self.num_classes = num_classes

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers=num_layers, batch_first=True,
                            bidirectional=bidirectional, dropout=config.dropout)

        self.fc = nn.Linear(
            self.hidden_size * 2 if self.bidirectional else self.hidden_size
            , self.num_classes
        )

    def forward(self, inputs, length):
        packed_inputs = pack_padded_sequence(inputs, lengths=length, batch_first=True, enforce_sorted=False)
        sorted_idx, resort_idx = packed_inputs.sorted_indices, packed_inputs.unsorted_indices
        sorted_idx = [int(v) for v in list(sorted_idx)]

        sorted_inputs = inputs[sorted_idx]
        sorted_length = length[sorted_idx]
        embedded = self.embeddings(sorted_inputs)
        packed_embbed = pack_padded_sequence(embedded, sorted_length, batch_first=True)
        out, _ = self.lstm(packed_embbed)
        padded_out = pad_packed_sequence(out, batch_first=True)[0]
        resort_out = padded_out[resort_idx]

        out = torch.sum(resort_out, 1)
        out1 = self.fc(out)
        return out1


class AttnModel(nn.Module):
    def __init__(self, hidden_size=128, input_size=100, bidirectional=True, num_layers=2, num_classes=7):
        super(AttnModel, self).__init__()

        weights = torch.from_numpy(
            pickle.load(open(os.path.join(Cfg().word2vec_from_scratch, '25_embeddings.pkl'), 'rb'))
        ).float()
        self.embeddings = nn.Embedding.from_pretrained(weights, freeze=True)

        self.model_name = '5ABLstm'
        self.hidden_size = hidden_size
        self.hidden_size2 = 128
        self.input_size = input_size
        self.bidirectional = bidirectional
        self.num_layers = num_layers
        self.num_classes = num_classes

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers=num_layers, batch_first=True,
                            bidirectional=bidirectional, dropout=config.dropout)
        self.tanh1 = nn.Tanh()
        self.w = nn.Parameter(torch.Tensor(self.hidden_size * 2))
        self.tanh2 = nn.Tanh()
        self.fc1 = nn.Linear(self.hidden_size * 2, self.hidden_size2)
        self.fc = nn.Linear(self.hidden_size2, self.num_classes)

    def init_hidden(self):
        return (torch.zeros(1 + int(self.bidirectional), 1, self.hidden_size),
                torch.zeros(1 + int(self.bidirectional), 1, self.hidden_size))

    def forward(self, inputs, length, phase):

        # packed_inputs = pack_padded_sequence(inputs, lengths=length, batch_first=True, enforce_sorted=False)
        # sorted_idx, resort_idx = packed_inputs.sorted_indices, packed_inputs.unsorted_indices
        # sorted_idx = [int(v) for v in list(sorted_idx)]
        #
        # sorted_inputs = inputs[sorted_idx]
        # sorted_length = length[sorted_idx]
        #
        # embedded = pack_padded_sequence(self.embeddings(sorted_inputs), sorted_length, batch_first=True)
        embedded = self.embeddings(inputs)
        out, _ = self.lstm(embedded)
        # unpack_out = pad_packed_sequence(out, batch_first=True)[0].data
        # resort_out = unpack_out[resort_idx]

        u = torch.tanh(torch.matmul(out, self.w))
        alpha = F.softmax(
            u, dim=1
        ).unsqueeze(-1)

        attn_out = out * alpha
        out = torch.sum(attn_out, 1)

        fc_out = self.fc1(out)
        fc1_out = self.fc(fc_out)
        if phase == 'test':
            return alpha.squeeze().detach().numpy(), fc1_out
        else:
            return fc1_out

    # if phase == 'train' else alpha.squeeze().detach().numpy(), fc1_out

    def forward1(self, inputs, length):
        packed_inputs = pack_padded_sequence(inputs, lengths=length, batch_first=True, enforce_sorted=False)
        sorted_idx, resort_idx = packed_inputs.sorted_indices, packed_inputs.unsorted_indices
        sorted_idx = [int(v) for v in list(sorted_idx)]

        sorted_inputs = inputs[sorted_idx]
        sorted_length = length[sorted_idx]
        embedded = self.embeddings(sorted_inputs)
        packed_embbed = pack_padded_sequence(embedded, sorted_length, batch_first=True)

        hidden, _ = self.lstm(packed_embbed)

        padded_out = pad_packed_sequence(hidden, batch_first=True)[0]
        resort_padded_out = padded_out[resort_idx]
        alpha = F.softmax(torch.matmul(resort_padded_out, self.w), dim=1).unsqueeze(-1)
        out = padded_out * alpha
        out = torch.sum(out, 1)

        out = F.relu(out)
        out = self.fc(self.fc1(out))
        return out


class CRA(nn.Module):
    def __init__(self, hidden_size=128, input_size=100, bidirectional=True, num_layers=2, num_classes=7):
        super(CRA, self).__init__()

        weights = torch.from_numpy(
            pickle.load(open(os.path.join(Cfg().word2vec_from_scratch, 'emb_weights.pkl'), 'rb'))
        ).float()
        self.embeddings = nn.Embedding.from_pretrained(weights, freeze=True)

        self.model_name = 'BLSTM'
        self.hidden_size = hidden_size
        self.input_size = input_size
        self.bidirectional = bidirectional
        self.num_layers = num_layers
        self.num_classes = num_classes

        self.cnn = nn.Sequential(

        )

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers=num_layers, batch_first=True,
                            bidirectional=bidirectional)

        self.fc = nn.Linear(
            self.hidden_size * 2 if self.bidirectional else self.hidden_size
            , self.num_classes
        )
