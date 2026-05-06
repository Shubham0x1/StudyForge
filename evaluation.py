from sentence_transformers import util
from rag import get_embedding_model


def evaluate_answers(questions, user_answers):
    results = []
    score = 0

    for q in questions:
        qid = str(q["id"])
        user_answer = user_answers.get(qid, "")

        correct = q["correct"]

        model = get_embedding_model()
        emb1 = model.encode(user_answer, convert_to_tensor=True)
        emb2 = model.encode(correct, convert_to_tensor=True)

        similarity = util.cos_sim(emb1, emb2).item()

        is_correct = similarity > 0.6

        if is_correct:
            score += 1

        results.append({
            "question_id": qid,
            "is_correct": is_correct,
            "similarity": round(similarity, 2),
            "topic": q.get("topic", "General")
        })

    return {
        "score": score,
        "question_results": results
    }
