from collections import Counter

def normalize_entities(entities):

    pairs = [(e["word"], e["entity_group"]) for e in entities]

    counter = Counter(pairs)

    result = []

    for (word, ent_type), count in counter.items():
        result.append({
            "word": word,
            "type": ent_type,
            "count": count
        })

    return result

def chunk_text(text, tokenizer, max_tokens=512):

    words = text.split()
    chunks = []
    current = []

    for word in words:
        current.append(word)

        if len(tokenizer(" ".join(current))["input_ids"]) > max_tokens:
            chunks.append(" ".join(current[:-1]))
            current = [word]

    if current:
        chunks.append(" ".join(current))

    return chunks