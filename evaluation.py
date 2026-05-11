def evaluate_answers(questions, user_answers):
    results = []
    score = 0

    for q in questions:
        qid = str(q["id"])
        user_answer = user_answers.get(qid, "").strip().lower()
        correct = q["correct"].strip().lower()

        # Empty answer (skipped) is always wrong
        if not user_answer:
            is_correct = False
        else:
            is_correct = (user_answer == correct) or (user_answer in correct) or (correct in user_answer)

        if is_correct:
            score += 1

        results.append({
            "question_id": qid,
            "is_correct": is_correct,
            "similarity": 1.0 if is_correct else 0.0,
            "topic": q.get("topic", "General")
        })

    return {
        "score": score,
        "question_results": results
    }
