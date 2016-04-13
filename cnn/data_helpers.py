import numpy as np
import re
import random
import itertools
from collections import Counter
from csv import reader
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
from string import punctuation


def tokenize_str(string):
    """
    Tokenize a string.
    """
    #string = re.sub(r"(?:\@|https?\://)\S+", "", string.lower())
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    tknzr = TweetTokenizer()
    words = tknzr.tokenize(string.lower())
    words = [word for word in words if len(word) > 0 and word not in punctuation]
    return words


def load_data_and_labels(pos_file, neg_file, sample_size):
    """
    Loads polarity data from files, splits the data into words and generates 
        labels.
    Returns split sentences and labels.
    """
    # Load data from files
    positive_examples = open(pos_file, "r").readlines()
    random.shuffle(positive_examples)
    positive_examples = list(positive_examples[:sample_size/2])
    positive_examples = [s.strip() for s in positive_examples]
    negative_examples = open(neg_file, "r").readlines()
    random.shuffle(negative_examples)
    negative_examples = list(negative_examples[:sample_size/2])
    negative_examples = [s.strip() for s in negative_examples]
    # Split by words
    x_text = positive_examples + negative_examples
    x_text = [tokenize_str(sent) for sent in x_text]

    # Generate labels
    positive_labels = [[0, 1] for _ in positive_examples]
    negative_labels = [[1, 0] for _ in negative_examples]
    y = np.concatenate([positive_labels, negative_labels], 0)
    return [x_text, y]


def pad_sentences(sentences, sequence_length, padding_word="UNK"):
    """
    Pads all sentences to the same length. The length is defined by the longest 
        sentence.
    Returns padded sentences.
    """
    #if sequence_length <= 0:
        #sequence_length = max(len(x) for x in sentences)
        #print "Sequence length set to", sequence_length
    padded_sentences = []
    for i in range(len(sentences)):
        sentence = sentences[i]
        num_padding = sequence_length - len(sentence)
        new_sentence = sentence + [padding_word] * num_padding
        padded_sentences.append(new_sentence)
    return padded_sentences


def build_vocab(vocab_file, sentences):
    """
    Builds a vocabulary mapping from word to index based on the sentences.
    Returns vocabulary mapping and inverse vocabulary mapping.
    """

    stopset = set(stopwords.words('english'))

    # Load vocabulary file
    id2word = [] # Mapping from index to word
    word2id = {} # Mapping from word to index
    with open(vocab_file, "r") as file:
        for i, line in enumerate(reader(file, delimiter=" ")):
            id2word.append(line[0])
            word2id[line[0]] = i

    #Add frequent words not in vocabulary
    #word_counts = Counter(itertools.chain(*sentences))
    # Mapping from index to word
    #id2word = [x[0] for x in word_counts.most_common()] # if x[1] > 10 and len(x[0]) >= 3 and x[0] not in stopset]
    #id2word = list(sorted(id2word))
    # Mapping from word to index
    #word2id = {x: i for i, x in enumerate(id2word)}

    return [word2id, id2word]


def build_input_data(sentences, labels, word2id):
    """
    Maps sentencs and labels to vectors based on a vocabulary.
    """
    #tot = mis = 0
    #x = []
    #for sentence in sentences:
    #    sent = []
    #    for word in sentence:
    #        if word != "UNK": tot += 1
    #        if word in word2id:
    #            sent.append(int(word2id[word]))
    #        else:
    #            sent.append(int(0))
    #            if word != "UNK": mis += 1
    #    x.append(sent)
    #print "{} out of {} words are not in vocabulary.".format(mis, tot)
    #x = np.array(x)
    x = np.array([[word2id[word] if word in word2id else 0 for word in sentence]
        for sentence in sentences])
    y = np.array(labels)
    return [x, y]


def load_data(vocab_file, pos_file, neg_file, sequence_length, sample_size=0):
    """
    Loads and preprocessed data. 
    Returns input vectors, labels, word-to-ID and ID-to-word mappings.
    """

    # Load and preprocess data
    sentences, labels = load_data_and_labels(pos_file, neg_file, sample_size)
    sentences_padded = pad_sentences(sentences, sequence_length)

    word2id, id2word = build_vocab(vocab_file, sentences)
    x, y = build_input_data(sentences_padded, labels, word2id)

    return [x, y, word2id, id2word]


def batch_iter(data, batch_size, num_epochs, shuffle=True):
    """
    Generates a batch iterator for a dataset.
    """
    data = np.array(data)
    data_size = len(data)
    num_batches_per_epoch = int(len(data)/batch_size) + 1
    for epoch in range(num_epochs):
        # Shuffle the data at each epoch
        if shuffle:
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data = data[shuffle_indices]
        else:
            shuffled_data = data
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, data_size)
            yield shuffled_data[start_index:end_index]
