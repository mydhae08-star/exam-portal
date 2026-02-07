from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from . import exam_catalog


def test_import(request):
    departments = exam_catalog.list_departments()
    return HttpResponse("Departments: " + ", ".join(departments))


@login_required
def choose_exam(request):
    dept = request.POST.get("department", "")
    proc = request.POST.get("process", "")
    exam_id = request.POST.get("exam_id", "")

    departments = exam_catalog.list_departments()
    processes = exam_catalog.list_processes(dept) if dept else []
    exams = exam_catalog.list_exams(dept, proc) if (dept and proc) else []

    if request.method == "POST" and exam_id:
        return redirect("start_exam", exam_id=exam_id)

    return render(
        request,
        "choose_exam.html",
        {
            "departments": departments,
            "processes": processes,
            "exams": exams,
            "selected_dept": dept,
            "selected_proc": proc,
        },
    )


@login_required
def start_exam(request, exam_id: str):
    # store attempt in session (simple prototype)
    request.session["exam_id"] = exam_id
    request.session["answers"] = {}  # {"Q1":"B", "Q2":"A", ...}
    return redirect("question_page", q_index=0)


@login_required
def question_page(request, q_index: int):
    exam_id = request.session.get("exam_id")
    if not exam_id:
        return redirect("choose_exam")

    exam = exam_catalog.load_exam(exam_id, randomize=False)
    questions = exam.get("questions", [])
    total = len(questions)

    if total == 0:
        return redirect("choose_exam")

    # clamp q_index so it never goes out of range
    if q_index < 0:
        q_index = 0
    if q_index >= total:
        return redirect("exam_result")

    q = questions[q_index]

    answers = request.session.get("answers", {})
    current_answer = answers.get(q["id"], None)

    if request.method == "POST":
        # Save answer (if provided)
        raw_answer = request.POST.get("answer", "").strip()

        if raw_answer != "":
            if q["type"] == "true_false":
                val = raw_answer.lower()
                answer = True if val in ("true", "t", "yes", "y", "1") else False
            else:
                answer = raw_answer.upper()

            answers[q["id"]] = answer
            request.session["answers"] = answers

        action = request.POST.get("action", "next")

        if action == "back":
            return redirect("question_page", q_index=q_index - 1)

        # last question: submit -> result
        if action == "submit" or q_index == total - 1:
            return redirect("exam_result")

        return redirect("question_page", q_index=q_index + 1)

    return render(
        request,
        "question.html",
        {
            "exam": exam,
            "q": q,
            "q_index": q_index,
            "total": total,
            "is_first": (q_index == 0),
            "is_last": (q_index == total - 1),
            "current_answer": current_answer,
        },
    )


@login_required
def exam_result(request):
    exam_id = request.session.get("exam_id")
    if not exam_id:
        return redirect("choose_exam")

    exam = exam_catalog.load_exam(exam_id, randomize=False)
    answers = request.session.get("answers", {})
    result = exam_catalog.grade_exam(exam, answers)

    return render(request, "result.html", {"exam": exam, "result": result, "answers": answers})


import csv
from datetime import datetime
from django.http import HttpResponse

@login_required
def download_result(request):
    exam_id = request.session.get("exam_id")
    if not exam_id:
        return redirect("choose_exam")

    exam = exam_catalog.load_exam(exam_id, randomize=False)
    answers = request.session.get("answers", {})
    result = exam_catalog.grade_exam(exam, answers)

    username = request.user.username
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    response = HttpResponse(content_type="text/csv")
    filename = f"exam_result_{username}_{exam_id}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # Header info
    writer.writerow(["Username", username])
    writer.writerow(["Exam ID", exam_id])
    writer.writerow(["Exam Title", exam["title"]])
    writer.writerow(["Score (%)", result["score_pct"]])
    writer.writerow(["Passed", result["passed"]])
    writer.writerow(["Completed At", timestamp])
    writer.writerow([])

    # Question breakdown
    writer.writerow(["Question ID", "Question", "Given Answer", "Correct Answer", "Correct"])
    for row in result["breakdown"]:
        q = next(q for q in exam["questions"] if q["id"] == row["question_id"])
        writer.writerow([
            row["question_id"],
            q["prompt"],
            row["given"],
            row["correct"],
            row["is_correct"],
        ])

    return response

