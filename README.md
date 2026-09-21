## Resources

### RAG on code base:

https://medium.com/google-cloud/build-a-rag-system-for-your-codebase-in-5-easy-steps-a3506c10599b

### AST Modules python:

https://www.youtube.com/watch?v=A0vR3l1X-CU

### Chunk strategy:

https://mbrenndoerfer.com/writing/document-chunking-rag-strategies-retrieval#sentence-based-chunking

### Retrieval augmented generation system book:

https://mallahyari.github.io/rag-ebook/intro.html

### Invert Index:

https://www.geeksforgeeks.org/dbms/inverted-index/

Build your chunker in increasingly sophisticated stages:

File-based: one file = one chunk (baseline).
AST-based: one function or class = one chunk.
Parent-aware: methods include class context.
Dependency-aware: attach relevant imports and constants to each chunk.
Hierarchical: maintain relationships such as repository → module → class → method.
Semantic: merge or split chunks based on token limits while preserving logical boundaries.
This progression mirrors how many production code RAG systems evolve, moving from simple syntax-aware chunking to richer, context-preserving retrieval.

### Project of chunking using ast

https://github.com/yilinjz/astchunk.git

### chunking algo

```text
Algorithm 1 AST-based Chunking Algorithm
MAX_SIZE ← maximum chunk size

function CHUNKCODE(code)
    tree ← PARSEAST(code)
    if GETSIZE(code) ≤ MAX_SIZE then
    return [tree]
    else
    return CHUNKNODES(tree.children)
    end if
   end function

function CHUNKNODES(nodes)
    chunks ← [ ], chunk ← [ ], size ← 0
    for node in nodes do
        s ← GETSIZE(node)
        if (chunk = [] and s > MAX_SIZE) or
            (size + s > MAX_SIZE) then
            if chunk̸ = [ ] then
                chunks.append(chunk)
                chunk, size ← [ ], 0
        end if
        if s > MAX_SIZE then
            subchunks ← CHUNKNODES(node.children)
            chunks.extend(subchunks)
            continue
        end if
        else
            chunk.append(node); size ← size + s
            end if
            end for
            if chunk̸ = [ ] then
            chunks.append(chunk)
        end if
    return chunks
end function
```

### ALGO OF CHUNKING THE CODE

https://www.cs.cmu.edu/~sherryw/assets/pubs/2025-cast.pdf

### Langchain text spliter

https://github.com/langchain-ai/langchain/tree/master/libs/text-splitters

### Image for MB25 SYSTEM

https://docs.weaviate.io/assets/images/bm25_operators_light-fe6a283b72823515e7f70dc0a6fc6d29.png

### Retrieval systems:

https://nlp.stanford.edu/IR-book/


## benchmark: more than 1h => 6:09 (without inserting the document terms) => 5:49(without inserting the document terms) => 4:15 => 1.30

### vector Embeding
https://www.youtube.com/watch?v=gl1r1XV0SLw

### vector indexing:
https://medium.com/@myscale/understanding-vector-indexing-a-comprehensive-guide-d1abe36ccd3c

### how to build vector storage
https://oneuptime.com/blog/post/2026-01-30-rag-vector-storage/view


### HNSW search:
https://www.youtube.com/watch?v=77QH0Y2PYKg
https://www.youtube.com/watch?v=rhZgXNdhWDY

### SKIPED LINKED LIST
https://ocw.mit.edu/courses/6-046j-introduction-to-algorithms-sma-5503-fall-2005/resources/lecture-12-skip-lists/
https://www.youtube.com/watch?v=2g9OSRKJuzM
