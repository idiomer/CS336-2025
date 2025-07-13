#%% NaiveBPE
from typing import Union, List, Dict, Tuple


class NaiveBPE:
  """ 基于UTF8，按字节分词，循环贪心合并最频繁的字节对加入词库，直至达到目标词库数量或再无pair
  """
  def __init__(self, max_vocab_num:int=257) -> None:
    # 初始化基础字节表(256)
    self.pair2token = {(i,):i for i in range(256)}
    self.token2bytes = {i:bytes([i]) for i in range(256)}
    self.max_vocab_num = max(256, max_vocab_num)

  def get_pair_occur(self, tokens:List[int]) -> Dict[Tuple[int], int]:
    """ 给定tokens，统计所有pair的出现次数 """
    counter = dict()
    for i in range(len(tokens)-1):
      if (pair:=(tokens[i], tokens[i+1])) in counter:
        counter[pair] += 1
      else:
        counter[pair] = 1
    return counter

  def merge(self, tokens:List[int], target_pair:Tuple[int, int], target_id:int) -> List[int]:
    """ 将tokens中的target_pair替换成target_id """
    j, new_tokens = 0, list()
    while j < len(tokens):
      if j+1 == len(tokens) or (tokens[j], tokens[j+1]) != target_pair:
        new_tokens.append(tokens[j]); j += 1
      else:
        new_tokens.append(target_id); j += 2
    return new_tokens

  def fit(self, text_corpus: List[str]) -> None:
    """ 训练：贪心合并最频繁字节对，直至词表达到预定目标或无法再合并 """
    token_corpus = [list(text.encode('utf-8')) for text in text_corpus]
    while len(self.pair2token) < self.max_vocab_num:
      # 统计 字节对 频率
      pair2count = dict()
      for tokens in token_corpus:
        for pair, count in self.get_pair_occur(tokens).items():
          pair2count[pair] = pair2count.get(pair, 0) + count
      if len(pair2count) == 0:
        break

      # 查找当前最频繁的字节对，平局优先选择字典序较大的
      max_pair = max((cnt, pair) for pair, cnt in pair2count.items())[1]
      self.pair2token[max_pair] = len(self.pair2token)

      # 用新token替换旧token对
      max_index = self.pair2token[max_pair]
      for i, tokens in enumerate(token_corpus):
        token_corpus[i] = self.merge(tokens, max_pair, max_index)
    self.update_token2bytes()
    return self

  def update_token2bytes(self) -> None:
    for pair, token in self.pair2token.items():
      if len(pair)==2:
        self.token2bytes[token] = self.token2bytes[pair[0]] + self.token2bytes[pair[1]]

  def encode(self, text:str) -> List[int]:
    """ 将文本编码成tokens """
    tokens = list(text.encode('utf-8'))
    while len(tokens) >= 2:
      # 查找序列中最小序号的pair
      pair2count = self.get_pair_occur(tokens)
      target_pair = min(pair2count, key=lambda p: self.pair2token.get(p, float('inf')))
      if target_pair not in self.pair2token:
        break

      # 合并当前最小序号的pair成token_index
      target_id = self.pair2token[target_pair]
      tokens = self.merge(tokens, target_pair, target_id)
    return tokens

  def decode(self, tokens:List[int], errors:str='strict') -> str:
    """ 将tokens解码成text """
    bytes_arr = (self.token2bytes[token] for token in tokens)
    return b"".join(bytes_arr).decode('utf-8', errors=errors)


if __name__ == '__main__':
  bpe = NaiveBPE(max_vocab_num=256+1)
  bpe.fit(['你好啊，你好世界'])

  text = '你好啊，你好世界 abc 算法'
  print("text =", text)
  print("token =", bpe.encode(text))
  print("decoded_text =", bpe.decode(bpe.encode(text)))
