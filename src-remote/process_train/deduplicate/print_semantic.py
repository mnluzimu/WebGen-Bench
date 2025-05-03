from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import argparse

def load_questions(jsonl_path, key="Q"):
    """
    Load questions from a JSONL file. Each line is a dict with a 'Q' field.
    """
    questions = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            if key in obj:
                questions.append(obj[key])
    return questions

def compute_similarity_matrix(test_qs, train_qs, model_name='all-MiniLM-L6-v2'):
    """
    Compute cosine similarity between test and training questions.
    """
    model = SentenceTransformer(model_name)

    test_embeddings = model.encode(test_qs, convert_to_tensor=True, show_progress_bar=True)
    train_embeddings = model.encode(train_qs, convert_to_tensor=True, show_progress_bar=True)

    similarity_matrix = cosine_similarity(test_embeddings.cpu().numpy(), train_embeddings.cpu().numpy())
    return similarity_matrix

def print_top_matches(test_qs, train_qs, sim_matrix, top_k=5, sim_threshold=0.9):
    """
    Print top-K most similar training questions for each test question.
    """
    top_matches = []
    for i, test_q in enumerate(test_qs):
        scores = list(enumerate(sim_matrix[i]))
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
        print(f"\nTest Q[{i}]: {test_q}")
        entry = {"test_instruction": test_q, "matches": []}
        for j, score in sorted_scores:
            if score >= sim_threshold:
                print(f"  ↪ Similarity: {score:.4f} | Train Q[{j}]: {train_qs[j]}")
                entry["matches"].append({"train_instruction": train_qs[j], "similarity": float(score)})
        top_matches.append(entry)
    return top_matches

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_file", type=str, required=True, help="Path to JSONL file with test questions (key='Q')")
    parser.add_argument("--train_file", type=str, required=True, help="Path to JSONL file with train QA pairs (key='Q')")
    parser.add_argument("--top_k", type=int, default=5, help="Top-K matches to print")
    parser.add_argument("--sim_threshold", type=float, default=0.9, help="Min similarity to print")
    args = parser.parse_args()

    test_qs = load_questions(args.test_file, key="instruction")
    train_qs = load_questions(args.train_file, key="instruction")

    sim_matrix = compute_similarity_matrix(test_qs, train_qs)
    top_matches = print_top_matches(test_qs, train_qs, sim_matrix, top_k=args.top_k, sim_threshold=args.sim_threshold)
    with open("src-remote/process_train/deduplicate/top_matches.json", "w", encoding="utf-8") as f:
        json.dump(top_matches, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
