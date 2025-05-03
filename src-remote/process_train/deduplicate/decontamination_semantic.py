import json
import argparse
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import numpy as np


def load_questions(jsonl_path, key="instruction"):
    data = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            if key in obj:
                data.append(obj)
    return data


def extract_questions(data, key="instruction"):
    return [item[key] for item in data]


def compute_similarity_matrix(test_qs, train_qs, model_name='all-MiniLM-L6-v2'):
    model = SentenceTransformer(model_name)
    test_embeddings = model.encode(test_qs, convert_to_tensor=True, show_progress_bar=True)
    train_embeddings = model.encode(train_qs, convert_to_tensor=True, show_progress_bar=True)
    sim_matrix = cosine_similarity(test_embeddings.cpu().numpy(), train_embeddings.cpu().numpy())
    return sim_matrix


def filter_training_data(train_data, sim_matrix, threshold=0.9):
    """
    Remove training samples if they are similar to any test sample above the threshold.
    """
    to_remove = set()
    num_test = sim_matrix.shape[0]
    num_train = sim_matrix.shape[1]

    for train_idx in range(num_train):
        for test_idx in range(num_test):
            if sim_matrix[test_idx, train_idx] >= threshold:
                to_remove.add(train_idx)
                break

    filtered_data = [ex for idx, ex in enumerate(train_data) if idx not in to_remove]
    removed_data = [ex for idx, ex in enumerate(train_data) if idx in to_remove]
    return filtered_data, to_remove, removed_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_file", type=str, required=True, help="Path to test JSONL (with 'Q')")
    parser.add_argument("--train_file", type=str, required=True, help="Path to training JSONL (with 'Q' and 'A')")
    parser.add_argument("--output_file", type=str, default="filtered_train.jsonl", help="Output filtered train file")
    parser.add_argument("--contaminated_file", type=str, default="contaminated_train.jsonl", help="Output filtered train file")
    parser.add_argument("--sim_threshold", type=float, default=0.9, help="Similarity threshold")

    args = parser.parse_args()

    print("🔹 Loading data...")
    test_data = load_questions(args.test_file, key="instruction")
    train_data = load_questions(args.train_file, key="instruction")

    test_qs = extract_questions(test_data, key="instruction")
    train_qs = extract_questions(train_data, key="instruction")

    print("🔹 Computing semantic similarity...")
    sim_matrix = compute_similarity_matrix(test_qs, train_qs)

    print("🔹 Filtering training samples...")
    filtered_train_data, removed_indices, removed_data = filter_training_data(train_data, sim_matrix, threshold=args.sim_threshold)

    print(f"✅ Removed {len(removed_indices)} out of {len(train_data)} training samples.")

    print(f"🔹 Writing filtered training set to: {args.output_file}")
    with open(args.output_file, 'w', encoding='utf-8') as f:
        for entry in filtered_train_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    with open(args.contaminated_file, 'w', encoding='utf-8') as f:
        for entry in removed_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
