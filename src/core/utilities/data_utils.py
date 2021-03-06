import pickle
import re
import gensim
import numpy as np
import time
import json

UNK = "$UNK$"
NUM = "$NUM$"
NONE = "O"

class Utils:

    def __init__(self):
        """
        Constructor...
        """


    def load_glove_txt(self, filename):
        """
        Load the glove model from a given path
        """
        start = time.time()
        print("Started importing Glove Model from textfile")
        self.glove = gensim.models.KeyedVectors.load_word2vec_format(filename, binary=False)
        print("Finished importing Glove Model in ", start - time.time(), " seconds")

    def save_glove_pkl(self, filename):
        """
        Save the pretrained glove embeddings to pkl file
        """
        with open(filename, 'wb') as output:
            print("Started saving embeddings to binary")
            pickle.dump(self.glove, output, pickle.HIGHEST_PROTOCOL)
            print("Finished")

    def save_classes_to_json(self, class_dict,filename):
        """
        Save a class_dict to json file
        """
        with open(filename, 'w') as output:
            json_data = json.dumps(class_dict)
            output.write(json_data)
            output.close

    def load_classes_from_json(self,filename):
        """
        Load class_dict from json file
        """
        with open(filename) as f:
            return json.load(f)

    def save_embeddings(self, embeddings, filename):
        """
        Save embeddings for webserver
        """
        np.save(filename, embeddings)

    def load_embeddings(self, filename):
        """
        Load embeddings for webserver
        """
        return np.load(filename)

    def load_glove_pkl(self, filename):
        """
        Load pretrained glove embeddings from file
        Always do this first, since importing the sentences depends on a lookup in GloVe Model
        """
        start = time.time()
        with open(filename, 'rb') as inp:
            print("Started importing Glove Model from binary file")
            self.glove = pickle.load(inp)
            print("Imported binary embeddings in ", time.time()-start, " seconds!")


    def parse_pos(self, filename):
        """
        pos:
        POS tags are according to the Penn Treebank POS tagset: https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
        format:
        word \t tag
        One word per line, sentences separated by newline.

        Parsing to an array of dicts, maybe not the best solution
        """
        start = time.time()
        print("Started loading sentences form textfile")
        sentences = []
        tmpdic = {'words': [], 'tags':[], 'wc': 0}
        dictionary_dic = {}
        index = 0
        classes_dic = {}
        classindex = 0
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                if line != "\n":
                    word, tag = line.split()
                    if word in self.glove.wv.vocab:
                        tmpdic['words'].append(word)
                        if word not in dictionary_dic.keys():
                            dictionary_dic[word]= index
                            index+=1
                        if tag not in classes_dic.keys():
                            classes_dic[tag] = classindex
                            classindex+=1
                        tmpdic['tags'].append(tag)
                else:
                    tmpdic['wc'] = len(tmpdic['words'])
                    for key in tmpdic.keys():
                        tmpdic[key]= np.array(tmpdic[key])
                    if tmpdic['wc'] == 0:
                        tmpdic = {'words': [], 'tags':[], 'wc': 0}
                    else:
                        sentences.append(tmpdic)
                        tmpdic = {'words': [], 'tags':[], 'wc': 0}
        print("Imported sentences in ", time.time()-start, " seconds")
        return sentences, dictionary_dic, classes_dic

    def parse_ner(self, filename):
        """
        ner:
        format:
        word \t tag
        One word per line, sentences separated by newline.
        Additionally, documents are separated by a line
        -DOCSTART-	|O
        followed by an empty line.

        data is annoated in IOB-Format, I-LABEL denotes that a NE span starts B-LABEL denotes that a NE span continues, O means outside of an NE
        we have the NE types
        PER (person)
        ORG (organization)
        LOC (location)
        MISC (miscellaneous)
        """
        start = time.time()
        print('Starting NER parsing of', filename)
        sentences = []
        tmpdic = {'words': [], 'tags': [], 'wc': 0}
        dictionary_dic = {}
        index = 0
        classes_dic = {}
        classindex = 0
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                # if '-DOCSTART-' in line:
                #    continue
                if line != '\n':
                    word, tag = line.split('\t')
                    tag = tag[1:-1]  # remove leading '|'
                    if word in self.glove.wv.vocab:
                        tmpdic['words'].append(word)
                        if word not in dictionary_dic.keys():
                            dictionary_dic[word] = index
                            index += 1
                        if tag not in classes_dic.keys():
                            classes_dic[tag] = classindex
                            classindex += 1
                        tmpdic['tags'].append(tag)
                else:
                    tmpdic['wc'] = len(tmpdic['words'])
                    for key in tmpdic.keys():
                        tmpdic[key] = np.array(tmpdic[key])
                    if tmpdic['wc'] == 0:
                        tmpdic = {'words': [], 'tags': [], 'wc': 0}
                    else:
                        sentences.append(tmpdic)
                        tmpdic = {'words': [], 'tags': [], 'wc': 0}
        print("Imported NER sentences in {} seconds".format(time.time()-start))
        return sentences, dictionary_dic, classes_dic


    def _pad_sequences(self,sequences, pad_tok, max_length):
        """
        Args:
            sequences: a generator of list or tuple
            pad_tok: the char to pad with
        Returns:
            a list of list where each sublist has same length
        """
        sequence_padded, sequence_length = [], []

        for seq in sequences:
            seq = list(seq)
            seq_ = seq[:max_length] + [pad_tok]*max(max_length - len(seq), 0)
            sequence_padded +=  [seq_]
            sequence_length += [min(len(seq), max_length)]

        return sequence_padded, sequence_length


    def pad_sequences(self, sequences, pad_tok, nlevels=1):
        """
        Args:
            sequences: a generator of list or tuple
            pad_tok: the char to pad with
            nlevels: "depth" of padding, for the case where we have characters ids
        Returns:
            a list of list where each sublist has same length
        """
        max_length = max(map(lambda x : len(x), sequences))
        sequence_padded, sequence_length = self._pad_sequences(sequences,
                                                pad_tok, max_length)
        return sequence_padded, sequence_length


    def words2ids (self, sen, dictionary):
        """
        Convert a list of words into a list of ids according to vocab
        """
        l = []
        for word in sen:
            l.append(dictionary[word])
        return l


    def tags_to_int(self, tags, classes_dic):
        """
        Convert class tags to int
        """
        l = list()
        for tag in tags:
            l.append(classes_dic[tag])
        return l


    def sen_dict_to_tuple(self, sentences, dictionary, classes_dic):
        """
        Returns a list of tuples (sentences, tags)
        """
        l = []
        for sen in sentences:
            tmp = self.words2ids(sen["words"], dictionary)
            tags = self.tags_to_int(sen["tags"], classes_dic)
            l.append((tmp, tags))
        return l

    def sen_dict_to_tuple_pred(self, sentences, dictionary):
        """
        Returns a list of tuples (sentences, tags)
        """
        l = []
        for sen in sentences:
            tmp = self.words2ids(sen["words"], dictionary)
            l.append((tmp, None))
        return l

    def split_sentence(self, sentence):
        return re.findall(r"[\w']+|[.,!?;]", sentence)

    def minibatches(self, data, minibatch_size):
        """
        Args:
            data: generator of (sentence, tags) tuples
            minibatch_size: (int)
        Yields:
            list of tuples
        """
        x_batch, y_batch = [], []
        for (x, y) in data:
            if len(x_batch) == minibatch_size:
                yield x_batch, y_batch
                x_batch, y_batch = [], []

            if type(x[0]) == tuple:
                x = zip(*x)
            x_batch += [x]
            y_batch += [y]

        if len(x_batch) != 0:
            yield x_batch, y_batch

    def mixed_minibatches(self, data_pos, data_ner, minibatch_size):
        is_pos = True
        generator_pos = iter(self.minibatches(data_pos, minibatch_size))
        generator_ner = iter(self.minibatches(data_ner, minibatch_size))
        while True:
            if is_pos:
                try:
                    x_batch, y_batch = next(generator_pos)
                    yield x_batch, y_batch, "pos"
                except StopIteration:
                    break
            else:
                try:
                    x_batch, y_batch = next (generator_ner)
                    yield x_batch, y_batch, "ner"
                except StopIteration:
                    break
            is_pos = not is_pos

    def old_mixed_minibatches(self, data_pos, data_ner, minibatch_size):
        """
        Args:
            data: generator of (sentence, tags) tuples
            minibatch_size: (int)
        Yields:
            list of tuples

        in every iteration, yield (in an alternating fashion) minibatches for PoS and NER
        """
        stopped = False
        state = 'pos'
        pos_iter = iter(data_pos)
        ner_iter = iter(data_ner)
        x_batch, y_batch = [], []
        pos, ner = True, True
        while pos or ner:
            if state =="pos":
                while len(x_batch) < minibatch_size:
                    try:
                        (x,y) = next(pos_iter)
                        x_batch+=[x]
                        y_batch+=[y]
                    except StopIteration:
                        pos = False
                print("Mixed minibatch yielding:", len(x_batch), y_batch.__len__())
                yield x_batch, y_batch, "pos"
                x_batch,y_batch =[],[]
                state = "ner"

            if state =="ner":
                while len(x_batch) < minibatch_size:
                    try:
                        (x,y) = next(ner_iter)
                        x_batch+=[x]
                        y_batch+=[y]
                    except StopIteration:
                        ner = False
                yield x_batch, y_batch, "ner"
                x_batch,y_batch =[],[]
                state = "pos"

    def generate_embeddings(self, dictionaries):
        """
        Args:
             dictionaries: list of dictionaries
        Returns:
             merged dictionary and embeddings matrix

        TODO This can be much faster, maybe this function is also useless. For a production ready model probably the complete GloVe vocab is needed
        """
        res = dict()
        ind = 0
        for dic in dictionaries:
            for key in dic:
                if key not in res:
                    res[key] = ind
                    ind+=1
        embeddings = np.zeros([len(res), 300])
        for key in res:
            word_idx = res[key]
            embeddings[word_idx] = np.asarray(self.glove[key])
        return res, embeddings

    def get_chunk_type(self, tok, idx_to_tag):
        """
        Args:
            tok: id of token, ex 4
            idx_to_tag: dictionary {4: "B-PER", ...}
        Returns:
            tuple: "B", "PER"
        """
        tag_name = idx_to_tag[tok]
        tag_class = tag_name.split('-')[0]
        tag_type = tag_name.split('-')[-1]
        return tag_class, tag_type


    def get_chunks(self, seq, tags):
        """Given a sequence of tags, group entities and their position
        Args:
            seq: [4, 4, 0, 0, ...] sequence of labels
            tags: dict["O"] = 4
        Returns:
            list of (chunk_type, chunk_start, chunk_end)
        Example:
            seq = [4, 5, 0, 3]
            tags = {"B-PER": 4, "I-PER": 5, "B-LOC": 3}
            result = [("PER", 0, 2), ("LOC", 3, 4)]
        """
        default = tags[NONE]
        idx_to_tag = {idx: tag for tag, idx in tags.items()}
        chunks = []
        chunk_type, chunk_start = None, None
        for i, tok in enumerate(seq):
            # End of a chunk 1
            if tok == default and chunk_type is not None:
                # Add a chunk.
                chunk = (chunk_type, chunk_start, i)
                chunks.append(chunk)
                chunk_type, chunk_start = None, None

            # End of a chunk + start of a chunk!
            elif tok != default:
                tok_chunk_class, tok_chunk_type = self.get_chunk_type(tok, idx_to_tag)
                if chunk_type is None:
                    chunk_type, chunk_start = tok_chunk_type, i
                elif tok_chunk_type != chunk_type or tok_chunk_class == "B":
                    chunk = (chunk_type, chunk_start, i)
                    chunks.append(chunk)
                    chunk_type, chunk_start = tok_chunk_type, i
            else:
                pass

        # end condition
        if chunk_type is not None:
            chunk = (chunk_type, chunk_start, len(seq))
            chunks.append(chunk)

        return chunks


util = Utils()
