import pickle
import os


class Cfg(object):
    def __init__(self):
        self.checkpoint = {
            'topic': './data/checkpoint/topic',
            'senti': './data/checkpoint/senti'
        }

        self.topic = ['恋爱关系', '学业方面', '职业发展', '心理方面']
        self.label_dict = {
            '中性': 0,
            '正向低': 1,
            '正向中': 2,
            '正向高': 3,
            '负向低': 4,
            '负向中': 5,
            '负向高': 6
        }

        self.tmp = r'C:\Users\king\Documents\code\data\tmp'

        self.word2vec_from_scratch = './data/word2vec'
        self.vocab_size = len(pickle.load(
            open('./data/word2vec/25_vocab.pkl', 'rb')
        ))
