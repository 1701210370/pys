# encoding=utf-8
import pickle
import os
import re
import pkuseg
from config import Cfg

config = Cfg()
seg = pkuseg.pkuseg()
cop = re.compile("[^\u4e00-\u9fa5^.^,^，^a-z^A-Z^]")
topic_list = ['恋爱关系', '学业方面', '职业发展', '心理方面', '其他']
label_dict = {
    '中性': 0,
    '正向低': 1,
    '正向中': 2,
    '正向高': 3,
    '负向低': 4,
    '负向中': 5,
    '负向高': 6
}
reverse_label_dict = {v: k for k, v in label_dict.items()}
pad_size = 32


def build_lstm_test_data(sentence):

    # print(sentence,type(sentence))
    UNK, PAD = '<UNK>', '<PAD>'
    res = []
    vocab = pickle.load(open(os.path.join(config.word2vec_from_scratch, '25_vocab.pkl'), 'rb'))
    seg_sentence = list(seg.cut(cop.sub('', sentence.strip())))
    for seg_word in seg.cut(cop.sub('', sentence.strip())):
        try:
            res.append(vocab[seg_word])
        except:
            res.append(vocab[UNK])
    if len(res) < pad_size:
        res += [vocab[PAD] for _ in range(pad_size - len(res))]
    else:
        res = res[:pad_size]

    return [res]


def get_topic_senti_att(sentence):
    import torch
    from torch.utils.data import DataLoader
    from corpus_dataloader import PakedData
    from lstm_attn import AttnModel

    model = AttnModel()
    model.load_state_dict(
        torch.load(
            os.path.join(Cfg().checkpoint['senti'], '5ABLstm_24.ckpt')
        )
    )
    model.eval()

    numeric_data = build_lstm_test_data(sentence=sentence)
    if len(numeric_data) <= 0:
        return
    test_data = PakedData(numeric_data, phase='test')
    test_iter = DataLoader(test_data, batch_size=1)
    for sample in test_iter:
        att, pred = model(sample['data'][0].long(), sample['length'], 'test')
        predict = torch.max(pred.data, 1)[1].cpu().numpy()
        return int(predict[0]), list(att)


def main1():
    print(get_topic_senti_att('是抑郁症吧应该看病吃药'))


if __name__ == '__main__':
    pass
