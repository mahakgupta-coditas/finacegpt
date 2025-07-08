def chunk_paragraphs(text, max_length = 500, overlap = 100):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + max_length
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += max_length - overlap  

    return chunks
