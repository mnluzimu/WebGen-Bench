import json
from tqdm import tqdm
from typing import Set


def get_ngrams(text: str, n: int) -> Set[str]:
    """
    Generate a set of n-grams from a given text.
    """
    tokens = text.split()
    return set(' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1))


def ngram_jaccard_similarity(text1: str, text2: str, n: int = 5) -> float:
    """
    Compute the Jaccard similarity between two texts based on n-grams.

    Args:
        text1: First input string.
        text2: Second input string.
        n: Size of n-grams to use (default is 5).

    Returns:
        A float representing the Jaccard similarity (0.0 to 1.0).
    """
    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    intersection = ngrams1.intersection(ngrams2)
    union = ngrams1.union(ngrams2)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [json.loads(line) for line in file]


def write_jsonl(file_path, records):
    with open(file_path, 'w', encoding='utf-8') as file:
        for record in records:
            json.dump(record, file, ensure_ascii=False)
            file.write('\n')


def is_contaminated(train_instruction, test_instruction, threshold=0.8):
    train_words = set(train_instruction.split())
    test_words = set(test_instruction.split())

    intersection = train_words.intersection(test_words)
    smaller_set_size = min(len(train_words), len(test_words))

    if smaller_set_size == 0:
        return False

    ngram_jaccard_similarity_value = ngram_jaccard_similarity(train_instruction, test_instruction, n=5)
    if ngram_jaccard_similarity_value > threshold:
        return True

    return len(intersection) / smaller_set_size > threshold


def decontaminate(train_data, test_data, threshold):
    test_instructions = [item['instruction'] for item in test_data]

    decontaminated_train = []
    contaminated_train = []
    for train_item in tqdm(train_data):
        if not any(is_contaminated(train_item['instruction'], test_inst, threshold) for test_inst in test_instructions):
            decontaminated_train.append(train_item)
        else:
            contaminated_train.append(train_item)

    return decontaminated_train, contaminated_train


if __name__ == "__main__":
    train_data = read_jsonl('data/train_processed/train_deduplicated.jsonl')
    test_data = read_jsonl('data/test.jsonl')

    decontaminated_train_data, contaminated_train_data = decontaminate(train_data, test_data, 0.6)

    write_jsonl('data/train_processed/train_decontaminated_ngram5.jsonl', decontaminated_train_data)

    print(f"Decontaminated {len(train_data) - len(decontaminated_train_data)} samples from training data.")
