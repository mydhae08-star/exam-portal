import json
import os
import random
from typing import Any, Dict, List, Optional

DEFAULT_DATA_PATH = os.environ.get("EXAM_DATA_PATH", os.path.join(os.path.dirname(__file__), "exam_data.json"))


def _load_data(data_path: str = DEFAULT_DATA_PATH) -> Dict[str, Any]:
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Cannot find exam data file at: {data_path}\n"
            f"Make sure exam_data.json is in the same folder as this file:\n"
            f"{os.path.dirname(__file__)}"
        )
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_departments(data_path: str = DEFAULT_DATA_PATH) -> List[str]:
    data = _load_data(data_path)
    return sorted([d["name"] for d in data.get("departments", [])])


def list_processes(department: str, data_path: str = DEFAULT_DATA_PATH) -> List[str]:
    data = _load_data(data_path)
    for d in data.get("departments", []):
        if d.get("name") == department:
            return sorted([p["name"] for p in d.get("processes", [])])
    return []


def list_exams(department: str, process: str, data_path: str = DEFAULT_DATA_PATH) -> List[Dict[str, Any]]:
    data = _load_data(data_path)
    for d in data.get("departments", []):
        if d.get("name") != department:
            continue
        for p in d.get("processes", []):
            if p.get("name") != process:
                continue
            return [
                {
                    "id": e["id"],
                    "name": e["title"],
                    "duration_minutes": e.get("duration_minutes"),
                    "pass_score": e.get("pass_score"),
                }
                for e in p.get("exams", [])
            ]
    return []


def load_exam(exam_id: str, data_path: str = DEFAULT_DATA_PATH, *, randomize: Optional[bool] = None) -> Dict[str, Any]:
    data = _load_data(data_path)
    for d in data.get("departments", []):
        for p in d.get("processes", []):
            for e in p.get("exams", []):
                if e.get("id") == exam_id:
                    exam = json.loads(json.dumps(e))  # deep copy
                    do_rand = exam.get("randomize_questions", False) if randomize is None else bool(randomize)
                    if do_rand and isinstance(exam.get("questions"), list):
                        random.shuffle(exam["questions"])
                    return exam
    raise KeyError(f"Exam ID '{exam_id}' not found.")


def grade_exam(exam: Dict[str, Any], user_answers: Dict[str, Any]) -> Dict[str, Any]:
    total = 0
    earned = 0
    breakdown = []

    for q in exam.get("questions", []):
        qid = q.get("id")
        pts = int(q.get("points", 0))
        total += pts

        correct = q.get("answer")
        given = user_answers.get(qid)

        is_correct = (given == correct)
        if is_correct:
            earned += pts

        breakdown.append(
            {
                "question_id": qid,
                "given": given,
                "correct": correct,
                "is_correct": is_correct,
                "points": pts,
            }
        )

    score_pct = (earned / total * 100.0) if total else 0.0
    pass_score = float(exam.get("pass_score", 0))

    return {
        "score_pct": round(score_pct, 2),
        "passed": score_pct >= pass_score,
        "breakdown": breakdown,
    }
