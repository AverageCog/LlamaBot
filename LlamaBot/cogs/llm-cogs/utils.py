import re

def split_into_chunks(text, max_length):
    chunks = []
    current_chunk = ""

    sentences = re.findall(r'(?s)(.*?(?<=[.!?])\s+)', text)

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks