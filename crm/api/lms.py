import frappe
from frappe import _


def _require_role(role: str) -> None:
    if role not in frappe.get_roles():
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def _resolve_student_from_session() -> str | None:
    students = frappe.get_all("Student", filters={"user": frappe.session.user}, limit=1)
    return students[0].name if students else None


def _update_course_lesson_count(course: str) -> None:
    count = frappe.db.count("Course Lecture", {"course": course})
    frappe.db.set_value("Course", course, "lesson_count", count)


def _has_instructor_role() -> bool:
    return "Instructor" in frappe.get_roles()


def _paginate(doctype: str, fields: list, filters: dict | None = None, start: int = 0, page_length: int = 20, order_by: str = "modified desc", pluck: str | None = None):
    kwargs = {
        "doctype": doctype,
        "filters": filters or {},
        "start": start,
        "page_length": page_length,
        "order_by": order_by,
    }
    if pluck:
        kwargs["pluck"] = pluck
    else:
        kwargs["fields"] = fields
    data = frappe.get_all(**kwargs)
    total = frappe.db.count(doctype, filters or {})
    return {"data": data, "total": total}


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_courses(start: int = 0, page_length: int = 20) -> dict:
    return _paginate(
        "Course",
        fields=["name", "title", "category", "status", "price", "duration", "lesson_count", "student_count", "image", "instructor"],
        order_by="modified desc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def get_course_detail(course: str) -> dict:
    course_doc = frappe.get_doc("Course", course)
    modules = frappe.get_all(
        "Course Module",
        filters={"course": course},
        fields=["name", "module_name", "position", "description"],
        order_by="position asc",
    )
    lectures = frappe.get_all(
        "Course Lecture",
        filters={"course": course},
        fields=["name", "title", "module", "position", "duration", "content_type", "video_url"],
        order_by="position asc",
    )
    return {"course": course_doc, "modules": modules, "lectures": lectures}


@frappe.whitelist()
def get_lecture_detail(lecture: str) -> dict:
    lecture_doc = frappe.get_doc("Course Lecture", lecture)
    lecture_doc.materials = frappe.get_all(
        "Lecture Material",
        filters={"parent": lecture},
        fields=["file_name", "type", "file"],
    )
    return lecture_doc


@frappe.whitelist()
def create_course(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Course", "create"):
        frappe.throw(_("Not permitted to create Course"), frappe.PermissionError)

    course = frappe.new_doc("Course")
    course.update({
        "title": data.get("title"),
        "category": data.get("category"),
        "status": data.get("status") or "Draft",
        "price": data.get("price", 0),
        "duration": data.get("duration", 0),
        "description": data.get("description"),
        "instructor": data.get("instructor"),
        "image": data.get("image"),
    })
    course.insert()

    for i, module_data in enumerate(data.get("modules", [])):
        mod = frappe.new_doc("Course Module")
        mod.course = course.name
        mod.module_name = module_data.get("module_name")
        mod.position = module_data.get("position", i + 1)
        mod.description = module_data.get("description")
        mod.insert()

    return course.name


@frappe.whitelist()
def create_lecture(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Course Lecture", "create"):
        frappe.throw(_("Not permitted to create Lecture"), frappe.PermissionError)

    lecture = frappe.new_doc("Course Lecture")
    lecture.update({
        "title": data.get("title"),
        "course": data.get("course"),
        "module": data.get("module"),
        "position": data.get("position", 0),
        "duration": data.get("duration", 0),
        "content_type": data.get("content_type", "Text"),
        "content": data.get("content"),
        "video_url": data.get("video_url"),
    })

    for material_data in data.get("materials", []):
        material = lecture.append("materials", {})
        material.file_name = material_data.get("file_name")
        material.type = material_data.get("type", "Document")
        material.file = material_data.get("file")

    lecture.insert()
    _update_course_lesson_count(lecture.course)
    return lecture.name


@frappe.whitelist()
def delete_lecture(lecture: str) -> bool:
    _require_role("Instructor")
    if not frappe.has_permission("Course Lecture", "delete"):
        frappe.throw(_("Not permitted to delete Lecture"), frappe.PermissionError)

    lecture_doc = frappe.get_doc("Course Lecture", lecture)
    course = lecture_doc.course
    lecture_doc.delete()
    _update_course_lesson_count(course)
    return True


@frappe.whitelist()
def get_courses_by_instructor(instructor: str | None = None) -> list:
    if not instructor:
        instructor = frappe.session.user
    elif instructor != frappe.session.user:
        if "System Manager" not in frappe.get_roles() and not _has_instructor_role():
            frappe.throw(_("Not permitted to view this instructor's courses"), frappe.PermissionError)
    return frappe.get_all(
        "Course",
        filters={"instructor": instructor},
        fields=["name", "title", "status", "lesson_count", "student_count"],
        order_by="modified desc",
    )


@frappe.whitelist()
def get_course_categories() -> list:
    return frappe.get_all(
        "Course Category",
        fields=["name", "category_name", "image"],
        order_by="category_name asc",
    )


# ---------------------------------------------------------------------------
# Students, Enrollments, Groups, Sessions, Attendance
# ---------------------------------------------------------------------------


def on_deal_won_create_student(doc, method) -> None:
    """Hook: when CRM Deal status type changes to Won, auto-create Student + Enrollment."""
    status_type = frappe.db.get_value("CRM Deal Status", doc.status, "type")
    if status_type != "Won":
        return

    primary_contact = None
    for c in doc.contacts:
        if c.is_primary:
            primary_contact = c.contact
            break

    if not primary_contact:
        return

    if frappe.db.exists("Student", {"contact": primary_contact}):
        return

    contact = frappe.get_doc("Contact", primary_contact)
    student = frappe.new_doc("Student")
    student.student_name = contact.full_name or contact.first_name
    student.contact = primary_contact
    if contact.email_id:
        email_user = frappe.db.get_value("User", {"email": contact.email_id}, "name")
        if email_user:
            student.user = email_user
    student.status = "Active"
    student.enrolled_on = frappe.utils.nowdate()
    student.insert()

    course = doc.get("custom_course")
    if course:
        enrollment = frappe.new_doc("Enrollment")
        enrollment.student = student.name
        enrollment.course = course
        enrollment.enrollment_date = frappe.utils.nowdate()
        enrollment.status = "Active"
        enrollment.insert()


@frappe.whitelist()
def get_students(start: int = 0, page_length: int = 20) -> dict:
    return _paginate(
        "Student",
        fields=["name", "student_name", "contact", "user", "image", "status", "enrolled_on", "date_of_birth", "gender", "parent_name", "parent_phone"],
        order_by="student_name asc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def get_student_detail(student: str) -> dict:
    student_doc = frappe.get_doc("Student", student)
    enrollments = frappe.get_all(
        "Enrollment",
        filters={"student": student},
        fields=["name", "course", "group", "enrollment_date", "status", "total_lessons", "completed_lessons"],
        order_by="enrollment_date desc",
    )
    return {"student": student_doc, "enrollments": enrollments}


@frappe.whitelist()
def get_enrollments(course: str | None = None, student: str | None = None, group: str | None = None, start: int = 0, page_length: int = 20) -> dict:
    if not student:
        student = _resolve_student_from_session()
    if not student:
        return {"data": [], "total": 0}

    filters = {"student": student}
    if course:
        filters["course"] = course
    if group:
        filters["group"] = group

    return _paginate(
        "Enrollment",
        filters=filters,
        fields=["name", "student", "course", "group", "enrollment_date", "status", "total_lessons", "completed_lessons"],
        order_by="enrollment_date desc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def create_enrollment(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Enrollment", "create"):
        frappe.throw(_("Not permitted to create Enrollment"), frappe.PermissionError)

    enrollment = frappe.new_doc("Enrollment")
    enrollment.update({
        "student": data.get("student"),
        "course": data.get("course"),
        "group": data.get("group"),
        "enrollment_date": data.get("enrollment_date") or frappe.utils.nowdate(),
        "status": data.get("status") or "Active",
    })
    enrollment.insert()
    return enrollment.name


@frappe.whitelist()
def get_student_groups(course: str | None = None, start: int = 0, page_length: int = 20) -> dict:
    filters = {}
    if course:
        filters["course"] = course

    return _paginate(
        "Student Group",
        filters=filters,
        fields=["name", "group_name", "course", "instructor", "max_students", "status"],
        order_by="group_name asc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def get_academic_sessions(group: str | None = None, date: str | None = None, start: int = 0, page_length: int = 20) -> dict:
    filters = {}
    if group:
        filters["group"] = group
    if date:
        filters["date"] = date

    return _paginate(
        "Academic Session",
        filters=filters,
        fields=["name", "title", "group", "course", "date", "start_time", "end_time", "status", "topic"],
        order_by="date desc, start_time asc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def mark_attendance(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Student Attendance", "create"):
        frappe.throw(_("Not permitted to mark attendance"), frappe.PermissionError)

    attendance = frappe.new_doc("Student Attendance")
    attendance.update({
        "student": data.get("student"),
        "academic_session": data.get("academic_session"),
        "status": data.get("status", "Present"),
        "notes": data.get("notes"),
    })
    attendance.insert()
    return attendance.name


@frappe.whitelist()
def batch_mark_attendance(data: str | dict) -> list:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Student Attendance", "create"):
        frappe.throw(_("Not permitted to mark attendance"), frappe.PermissionError)

    session = data.get("academic_session")
    attendance_list = data.get("attendance_list", [])
    results = []

    for entry in attendance_list:
        existing = frappe.db.exists(
            "Student Attendance",
            {"student": entry.get("student"), "academic_session": session},
        )
        if existing:
            results.append({"student": entry.get("student"), "status": "skipped", "name": existing})
            continue

        attendance = frappe.new_doc("Student Attendance")
        attendance.student = entry.get("student")
        attendance.academic_session = session
        attendance.status = entry.get("status", "Present")
        attendance.notes = entry.get("notes", "")
        attendance.insert()
        results.append({"student": entry.get("student"), "status": "created", "name": attendance.name})

    return results


@frappe.whitelist()
def get_attendance(session: str | None = None, student: str | None = None, date: str | None = None, start: int = 0, page_length: int = 20) -> dict:
    filters = {}
    if session:
        filters["academic_session"] = session
    if student:
        filters["student"] = student
    if date:
        filters["date"] = date

    return _paginate(
        "Student Attendance",
        filters=filters,
        fields=["name", "student", "academic_session", "group", "course", "date", "status", "notes"],
        order_by="date desc",
        start=start,
        page_length=page_length,
    )


# ---------------------------------------------------------------------------
# Abonements, Payments, Assignments
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_abonement_types(start: int = 0, page_length: int = 20) -> dict:
    return _paginate(
        "Abonement Type",
        fields=["name", "abonement_name", "total_classes", "price", "validity_days"],
        order_by="abonement_name asc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def get_student_abonements(student: str | None = None, start: int = 0, page_length: int = 20) -> dict:
    filters = {}
    if student:
        filters["student"] = student

    return _paginate(
        "Student Abonement",
        filters=filters,
        fields=["name", "student", "abonement_type", "status", "total_classes", "classes_remaining", "start_date", "end_date"],
        order_by="start_date desc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def create_student_abonement(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Student Abonement", "create"):
        frappe.throw(_("Not permitted to create Abonement"), frappe.PermissionError)

    ab = frappe.new_doc("Student Abonement")
    ab.update({
        "student": data.get("student"),
        "abonement_type": data.get("abonement_type"),
        "start_date": data.get("start_date") or frappe.utils.nowdate(),
        "status": data.get("status") or "Active",
    })
    ab.insert()
    return ab.name


@frappe.whitelist()
def get_payments(student: str | None = None, start: int = 0, page_length: int = 20) -> dict:
    filters = {}
    if student:
        filters["student"] = student

    return _paginate(
        "Payment",
        filters=filters,
        fields=["name", "student", "student_abonement", "amount", "payment_method", "payment_date", "notes"],
        order_by="payment_date desc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def create_payment(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Payment", "create"):
        frappe.throw(_("Not permitted to create Payment"), frappe.PermissionError)

    payment = frappe.new_doc("Payment")
    payment.update({
        "student": data.get("student"),
        "student_abonement": data.get("student_abonement"),
        "amount": data.get("amount"),
        "payment_method": data.get("payment_method", "Cash"),
        "payment_date": data.get("payment_date") or frappe.utils.nowdate(),
        "notes": data.get("notes"),
    })
    payment.insert()
    return payment.name


@frappe.whitelist()
def get_assignments(student: str | None = None, lecture: str | None = None, start: int = 0, page_length: int = 20) -> dict:
    filters = {}
    if student:
        filters["student"] = student
    if lecture:
        filters["lecture"] = lecture

    return _paginate(
        "Student Assignment",
        filters=filters,
        fields=["name", "student", "lecture", "course", "title", "status", "score", "instructor", "comment", "submitted_at", "due_date", "file"],
        order_by="modified desc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def submit_assignment(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data

    assignment_name = data.get("name")
    if assignment_name and frappe.db.exists("Student Assignment", assignment_name):
        assignment = frappe.get_doc("Student Assignment", assignment_name)
        if not frappe.has_permission("Student Assignment", "write", assignment):
            frappe.throw(_("Not permitted to update this assignment"), frappe.PermissionError)
    else:
        if not frappe.has_permission("Student Assignment", "create"):
            frappe.throw(_("Not permitted to create assignments"), frappe.PermissionError)
        assignment = frappe.new_doc("Student Assignment")
        assignment.student = data.get("student")
        assignment.lecture = data.get("lecture")
        if not assignment.title:
            student_name = frappe.db.get_value("Student", assignment.student, "student_name")
            lecture_title = frappe.db.get_value("Course Lecture", assignment.lecture, "title")
            assignment.title = f"{student_name} — {lecture_title}"

    assignment.status = "Submitted"
    assignment.file = data.get("file")
    assignment.submitted_at = frappe.utils.now_datetime()
    assignment.save()
    return assignment.name


@frappe.whitelist()
def grade_assignment(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Student Assignment", "write"):
        frappe.throw(_("Not permitted to grade assignments"), frappe.PermissionError)

    assignment = frappe.get_doc("Student Assignment", data.get("assignment"))
    assignment.score = data.get("score")
    assignment.comment = data.get("comment")
    assignment.instructor = data.get("instructor") or frappe.session.user
    assignment.status = data.get("status", "Approved")
    assignment.save()
    return assignment.name


# ---------------------------------------------------------------------------
# Instructor Dashboard, Journal, Coins, Knowledge Base, Reports
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_instructor_dashboard(instructor: str | None = None) -> dict:
    if not instructor:
        instructor = frappe.session.user
    elif instructor != frappe.session.user:
        if "System Manager" not in frappe.get_roles() and not _has_instructor_role():
            frappe.throw(_("Not permitted to view this instructor's dashboard"), frappe.PermissionError)

    today = frappe.utils.nowdate()
    my_groups = frappe.get_all(
        "Student Group",
        filters={"instructor": instructor},
        pluck="name",
    )

    sessions = frappe.get_all(
        "Academic Session",
        filters={"date": today, "group": ["in", my_groups]},
        fields=["name", "title", "group", "course", "date", "start_time", "end_time", "status", "topic", "room", "video_recording_url"],
        order_by="start_time asc",
    ) if my_groups else []

    groups = frappe.get_all(
        "Student Group",
        filters={"instructor": instructor},
        fields=["name", "group_name", "course", "max_students", "status"],
        order_by="group_name asc",
    )
    group_names = [g.name for g in groups]

    enrolled_counts = {}
    total_les_counts = {}
    completed_les_counts = {}

    if group_names:
        enrolled_data = frappe.get_all(
            "Enrollment",
            filters={"group": ["in", group_names], "status": "Active"},
            fields=["group", "name"],
        )
        for g_name in group_names:
            enrolled_counts[g_name] = sum(1 for e in enrolled_data if e.group == g_name)

        course_map = {g.name: g.course for g in groups}
        for g in groups:
            total_les_counts[g.name] = frappe.db.count("Course Lecture", {"course": g.course})
            completed_les_counts[g.name] = frappe.db.count(
                "Academic Session",
                {"group": g.name, "status": "Completed"},
            )

    for g in groups:
        g.enrolled_count = enrolled_counts.get(g.name, 0)
        total = total_les_counts.get(g.name, 0)
        completed = completed_les_counts.get(g.name, 0)
        g.total_lessons = total
        g.completed_lessons = completed
        g.progress_pct = round((completed / total * 100) if total else 0)

    pending_assignments = 0
    if group_names:
        students_in_my_groups = frappe.get_all(
            "Enrollment",
            filters={"group": ["in", group_names], "status": "Active"},
            pluck="student",
        )
        if students_in_my_groups:
            pending_assignments = frappe.db.count(
                "Student Assignment",
                {"student": ["in", students_in_my_groups], "status": "Submitted"},
            )

    return {
        "sessions": sessions,
        "groups": groups,
        "pending_assignments": pending_assignments,
    }


@frappe.whitelist()
def get_group_students(group: str, date: str | None = None) -> dict:
    if not date:
        date = frappe.utils.nowdate()

    enrollments = frappe.get_all(
        "Enrollment",
        filters={"group": group, "status": "Active"},
        fields=["student"],
        order_by="student asc",
    )
    student_names = [e.student for e in enrollments]

    today_session = frappe.get_all(
        "Academic Session",
        filters={"group": group, "date": date},
        fields=["name", "start_time", "end_time", "topic"],
        order_by="start_time asc",
        limit=1,
    )
    session = today_session[0] if today_session else None

    attendance_map = {}
    if session:
        records = frappe.get_all(
            "Student Attendance",
            filters={"academic_session": session.name},
            fields=["student", "status", "name"],
        )
        for r in records:
            attendance_map[r.student] = r

    scores_map = {}
    if session:
        course = frappe.db.get_value("Student Group", group, "course")
        lectures = frappe.get_all("Course Lecture", filters={"course": course}, pluck="name") if course else []
        if lectures and student_names:
            assignments = frappe.get_all(
                "Student Assignment",
                filters={"student": ["in", student_names], "lecture": ["in", lectures]},
                fields=["student", "lecture", "score", "status", "name"],
            )
            for a in assignments:
                scores_map.setdefault(a.student, []).append(a)

    # Batch-load all students in one query instead of N+1 get_doc calls
    student_docs_map = {}
    if student_names:
        student_data = frappe.get_all(
            "Student",
            filters={"name": ["in", student_names]},
            fields=["name", "student_name", "image", "codify_coins", "parent_name"],
        )
        student_docs_map = {s.name: s for s in student_data}

    students = []
    for s_name in student_names:
        sd = student_docs_map.get(s_name, {})
        att = attendance_map.get(s_name)
        students.append({
            "name": s_name,
            "student_name": sd.get("student_name", ""),
            "image": sd.get("image"),
            "codify_coins": sd.get("codify_coins") or 0,
            "attendance_status": att.status if att else None,
            "attendance_name": att.name if att else None,
            "scores": scores_map.get(s_name, []),
            "parent_name": sd.get("parent_name"),
        })

    return {"students": students, "session": session}


@frappe.whitelist()
def update_student_coins(data: str | dict) -> dict:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Student", "write"):
        frappe.throw(_("Not permitted to update student coins"), frappe.PermissionError)

    student = frappe.get_doc("Student", data.get("student"))
    delta = int(data.get("delta", 0))
    student.codify_coins = (student.codify_coins or 0) + delta
    student.save()

    return {
        "student": student.name,
        "codify_coins": student.codify_coins,
        "delta": delta,
        "reason": data.get("reason", ""),
    }


@frappe.whitelist()
def update_student_score(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Student Assignment", "write"):
        frappe.throw(_("Not permitted to update scores"), frappe.PermissionError)

    assignment_name = data.get("assignment")
    if assignment_name and frappe.db.exists("Student Assignment", assignment_name):
        assignment = frappe.get_doc("Student Assignment", assignment_name)
    else:
        assignment = frappe.new_doc("Student Assignment")
        assignment.student = data.get("student")
        assignment.lecture = data.get("lecture")
        student_name = frappe.db.get_value("Student", assignment.student, "student_name")
        lecture_title = frappe.db.get_value("Course Lecture", assignment.lecture, "title")
        assignment.title = f"{student_name} — {lecture_title}"

    assignment.score = data.get("score")
    assignment.status = data.get("status", "Approved")
    assignment.instructor = data.get("instructor") or frappe.session.user
    if data.get("comment"):
        assignment.comment = data.get("comment")
    assignment.save()
    return assignment.name


@frappe.whitelist()
def get_lectures_by_module(course: str | None = None, module: str | None = None) -> dict:
    modules = frappe.get_all(
        "Course Module",
        filters={"course": course} if course else {},
        fields=["name", "module_name", "position", "description"],
        order_by="position asc",
    )

    for m in modules:
        m.lectures = frappe.get_all(
            "Course Lecture",
            filters={"module": m.name},
            fields=["name", "title", "position", "duration", "content_type", "content", "video_url"],
            order_by="position asc",
        )

    ungrouped = frappe.get_all(
        "Course Lecture",
        filters={"course": course, "module": ["is", "not set"]} if course else None,
        fields=["name", "title", "position", "duration", "content_type"],
        order_by="position asc",
    )

    return {"modules": modules, "ungrouped": ungrouped or []}


@frappe.whitelist()
def update_session_recording(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Academic Session", "write"):
        frappe.throw(_("Not permitted to update session recording"), frappe.PermissionError)

    session = frappe.get_doc("Academic Session", data.get("session"))
    session.video_recording_url = data.get("video_url")
    session.save()
    return session.name


@frappe.whitelist()
def get_student_reports(student: str | None = None, instructor: str | None = None, start: int = 0, page_length: int = 20) -> dict:
    filters = {}
    if student:
        filters["student"] = student
    if instructor:
        filters["instructor"] = instructor

    return _paginate(
        "Student Report",
        filters=filters,
        fields=["name", "student", "student_name", "instructor", "report_date", "template", "overall_performance", "is_published"],
        order_by="report_date desc",
        start=start,
        page_length=page_length,
    )


@frappe.whitelist()
def get_student_report_detail(report: str) -> dict:
    doc = frappe.get_doc("Student Report", report)
    if not frappe.has_permission("Student Report", "read", doc):
        frappe.throw(_("Not permitted to view this report"), frappe.PermissionError)
    return doc


@frappe.whitelist()
def create_student_report(data: str | dict) -> str:
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")
    if not frappe.has_permission("Student Report", "create") and not frappe.has_permission("Student Report", "write"):
        frappe.throw(_("Not permitted to create or update reports"), frappe.PermissionError)

    report_name = data.get("name")
    if report_name and frappe.db.exists("Student Report", report_name):
        report = frappe.get_doc("Student Report", report_name)
    else:
        report = frappe.new_doc("Student Report")
        report.student = data.get("student")

    report.instructor = data.get("instructor") or frappe.session.user
    report.report_date = data.get("report_date") or frappe.utils.nowdate()
    report.template = data.get("template", "General Progress")
    report.overall_performance = data.get("overall_performance")
    report.technical_skills = data.get("technical_skills")
    report.behavior = data.get("behavior")
    report.engagement = data.get("engagement")
    report.recommendations = data.get("recommendations")
    report.is_published = data.get("is_published", 0)
    report.save()
    return report.name


@frappe.whitelist()
def delete_student_report(report: str) -> bool:
    _require_role("Instructor")
    if not frappe.has_permission("Student Report", "delete"):
        frappe.throw(_("Not permitted to delete reports"), frappe.PermissionError)

    frappe.get_doc("Student Report", report).delete()
    return True


# ---------------------------------------------------------------------------
# Lecture Progress
# ---------------------------------------------------------------------------


@frappe.whitelist()
def mark_lecture_complete(data: str | dict) -> str:
    """Mark a lecture as completed for a student. Auto-updates enrollment progress."""
    data = frappe.parse_json(data) if isinstance(data, str) else data

    student = data.get("student")
    lecture = data.get("lecture")

    student_user = frappe.db.get_value("Student", student, "user")
    if student_user and student_user != frappe.session.user:
        if not _has_instructor_role():
            frappe.throw(_("Not permitted to mark completion for another student"), frappe.PermissionError)

    existing = frappe.db.exists(
        "Lecture Progress",
        {"student": student, "lecture": lecture, "status": "Completed"},
    )
    if existing:
        return existing

    progress = frappe.new_doc("Lecture Progress")
    progress.student = student
    progress.lecture = lecture
    progress.status = "Completed"
    progress.insert()

    return progress.name


@frappe.whitelist()
def get_lecture_progress(student: str | None = None, course: str | None = None) -> dict:
    """Get lecture completion progress for a student, optionally filtered by course."""
    if not student:
        student = _resolve_student_from_session()
    if not student:
        return {"data": [], "total": 0}

    filters = {"student": student}
    if course:
        filters["course"] = course

    records = frappe.get_all(
        "Lecture Progress",
        filters=filters,
        fields=["name", "lecture", "course", "enrollment", "status", "completed_at", "time_spent"],
        order_by="modified desc",
    )

    total = frappe.db.count("Course Lecture", {"course": course}) if course else 0
    completed = sum(1 for r in records if r.status == "Completed")

    return {
        "data": records,
        "total_lectures": total,
        "completed": completed,
        "progress_pct": round((completed / total * 100) if total else 0),
    }
