## Frequency Staturation

if the word appears in many times in document how much extra relevance should
each additional occurences give.

# TD-IDF:

An older search method that multiplies how often a word apears in document by how rarly appears accross all documents

## Limitations:

- does not staturate repeated occurences or normalize document length
- Document length created another bias. Longer documents have more
  opportunities to contain query terms, so a 50-page technical report might
  outrank a focused two-page summary even when the summary better answers the
  query.

# BN-25:

A ranking algorithm that determines how relevant documents are to the search
queries by using probabilty theory instead of simple countint methods.
**_BM25_** follows the probabilistic ranking principle: documents should be ordered
by their estimated probability of relevance. Its scoring function approximates
this ordering with contributions for term rarity and saturated term frequency,
adjusted for document length

## BM25 answer of the Frequency Saturation:

More occurences increase the socre but each additional occurences gives less
benefit than the previous one

## The problem that it solve:

- Consider a collection of news articles and the query "president." A
  full-length 10,000-word biography of a president will mention the word
  hundreds of times. A tight 200-word breaking news story might mention it
  twice. Raw term frequency ranking would always favor the longer document,
  even when the short article is more relevant to your query. Length bias is
  one of the most fundamental failure modes of naive retrieval.

- The second failure mode is treating all terms equally. If your query is "the
  president of the United States," the word "the" appears in essentially every
  document. Counting "the" provides no discriminative signal. You want to
  reward documents for containing informative, specific terms, not common
  filler words.

- The third failure mode is not recognizing diminishing returns. Once a document
  has established that it's about machine learning by mentioning the term ten
  times, the eleventh mention adds very little new information. Treating each
  occurrence as equally valuable leads to systems that can be gamed by keyword
  repetition.

$$
BM25(D,Q)=∑i=1nIDF(qi)⋅f(qi,D)⋅(k1+1)f(qi,D)+k1⋅(1−b+b⋅∣D∣avgdl)
$$
