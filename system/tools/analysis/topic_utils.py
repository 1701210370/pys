import torch
from config import Cfg
import os
import pickle
import jieba

config = Cfg()
UNK, PAD = '<UNK>', '<PAD>'
from textCNN import Model, Config

# topic_model = Model(Config())
# topic_model.load_state_dict(torch.load(
#     os.path.join(config.checkpoint['topic'], 'best.ckpt')))
# topic_model.eval()
label_dict = {0: '职业发展', 1: '学业方面', 2: '心理方面', 3: '恋爱关系', 4:'其他'}


def stop_words_dict():
    with open('./data/stop.txt', 'rb') as fp:
        stop_words_dict = pickle.load(fp)
        return stop_words_dict


stop_words_dict = stop_words_dict()


def remove_stop_words(source):
    ret = []
    for words in source:
        if words in stop_words_dict:
            continue
        ret.append(words)
    return ret


def build_test_data(sentence):
    import pickle
    # print(os.path.join(config.word2vec_from_scratch, 'topic_vocab.pkl'))
    vocab = pickle.load(open(os.path.join(config.word2vec_from_scratch, 'topic_vocab_4_7.pkl'), 'rb'))
    words_line = []
    seg_list = jieba.cut(sentence)
    result = remove_stop_words(seg_list)
    result = ' '.join(result)
    if len(result) <= 1:
        return []
    else:
        # print('分词，去掉停用词后====={}'.format(result))
        result = result.split(' ')
        if len(result) < 32:
            result.extend([vocab.get(PAD)] * (32 - len(result)))
        else:
            result = result[:32]
        for word in result:
            words_line.append(vocab.get(word, vocab.get(UNK)))
        return [words_line]


model = Model(Config())
model.load_state_dict(torch.load(
    os.path.join(config.checkpoint['topic'], 'topic.ckpt')))
model.eval()
model.float()


def test(sentence):
    # print('要预测的句子是：{}'.format(sentence))
    if len(sentence) <= 1:
        return '其他'
    data = build_test_data(sentence)
    if len(data) == 0:
        return '其他'

    predict = model((torch.LongTensor(data), 0))
    # return int(torch.max(predict.data, 1)[1].cpu())
    return label_dict[int(torch.max(predict.data, 1)[1].cpu())]


print(test('真得好难，宁愿自己死了，也不愿意放弃'))