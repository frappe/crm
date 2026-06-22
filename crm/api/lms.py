# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def _require_role(role):
    if role not in frappe.get_roles():
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def _resolve_student_from_session():
    students = frappe.get_all("Student", filters={"user": frappe.session.user}, limit=1)
    return students[0].name if students else None


def _update_course_lesson_count(course):
    count = frappe.db.count("Course Lecture", {"course": course})
    frappe.db.set_value("Course", course, "lesson_count", count)


@frappe.whitelist()
def get_courses():
    courses = frappe.get_all(
        "Course",
        fields=[
            "name",
            "title",
            "category",
            "status",
            "price",
            "duration",
            "lesson_count",
            "student_count",
            "image",
            "instructor",
        ],
        order_by="modified desc",
    )
    return courses


@frappe.whitelist()
def get_course_detail(course):
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
        fields=[
            "name",
            "title",
            "module",
            "position",
            "duration",
            "content_type",
            "video_url",
        ],
        order_by="position asc",
    )
    return {
        "course": course_doc,
        "modules": modules,
        "lectures": lectures,
    }


@frappe.whitelist()
def get_lecture_detail(lecture):
    lecture_doc = frappe.get_doc("Course Lecture", lecture)
    lecture_doc.materials = frappe.get_all(
        "Lecture Material",
        filters={"parent": lecture},
        fields=["file_name", "type", "file"],
    )
    return lecture_doc


@frappe.whitelist()
def create_course(data):
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    course = frappe.new_doc("Course")
    course.update(
        {
            "title": data.get("title"),
            "category": data.get("category"),
            "status": data.get("status") or "Draft",
            "price": data.get("price", 0),
            "duration": data.get("duration", 0),
            "description": data.get("description"),
            "instructor": data.get("instructor"),
            "image": data.get("image"),
        }
    )
    course.insert(ignore_permissions=True)

    for i, module_data in enumerate(data.get("modules", [])):
        mod = frappe.new_doc("Course Module")
        mod.course = course.name
        mod.module_name = module_data.get("module_name")
        mod.position = module_data.get("position", i + 1)
        mod.description = module_data.get("description")
        mod.insert(ignore_permissions=True)

    return course.name


@frappe.whitelist()
def create_lecture(data):
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    lecture = frappe.new_doc("Course Lecture")
    lecture.update(
        {
            "title": data.get("title"),
            "course": data.get("course"),
            "module": data.get("module"),
            "position": data.get("position", 0),
            "duration": data.get("duration", 0),
            "content_type": data.get("content_type", "Text"),
            "content": data.get("content"),
            "video_url": data.get("video_url"),
        }
    )

    for material_data in data.get("materials", []):
        material = lecture.append("materials", {})
        material.file_name = material_data.get("file_name")
        material.type = material_data.get("type", "Document")
        material.file = material_data.get("file")

    lecture.insert(ignore_permissions=True)
    _update_course_lesson_count(lecture.course)
    return lecture.name


@frappe.whitelist()
def delete_lecture(lecture):
    _require_role("Instructor")
    lecture_doc = frappe.get_doc("Course Lecture", lecture)
    course = lecture_doc.course
    lecture_doc.delete()
    _update_course_lesson_count(course)
    return True


@frappe.whitelist()
def get_courses_by_instructor(instructor=None):
    if not instructor:
        instructor = frappe.session.user
    courses = frappe.get_all(
        "Course",
        filters={"instructor": instructor},
        fields=["name", "title", "status", "lesson_count", "student_count"],
        order_by="modified desc",
    )
    return courses


@frappe.whitelist()
def get_course_categories():
    categories = frappe.get_all(
        "Course Category",
        fields=["name", "category_name", "image"],
        order_by="category_name asc",
    )
    return categories


# ---------------------------------------------------------------------------
# Stage 2 — Students, Enrollments, Groups, Sessions, Attendance
# ---------------------------------------------------------------------------


def on_deal_won_create_student(doc, method):
    """Hook: when CRM Deal status type changes to "Won", auto-create Student + Enrollment."""
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
    student.insert(ignore_permissions=True)

    course = doc.get("custom_course")
    if course:
        enrollment = frappe.new_doc("Enrollment")
        enrollment.student = student.name
        enrollment.course = course
        enrollment.enrollment_date = frappe.utils.nowdate()
        enrollment.status = "Active"
        enrollment.insert(ignore_permissions=True)


# --- Student APIs ---


@frappe.whitelist()
def get_students():
    students = frappe.get_all(
        "Student",
        fields=[
            "name",
            "student_name",
            "contact",
            "user",
            "image",
            "status",
            "enrolled_on",
            "date_of_birth",
            "gender",
            "parent_name",
            "parent_phone",
        ],
        order_by="student_name asc",
    )
    return students


@frappe.whitelist()
def get_student_detail(student):
    student_doc = frappe.get_doc("Student", student)
    enrollments = frappe.get_all(
        "Enrollment",
        filters={"student": student},
        fields=["name", "course", "group", "enrollment_date", "status"],
        order_by="enrollment_date desc",
    )
    return {
        "student": student_doc,
        "enrollments": enrollments,
    }


# --- Enrollment APIs ---


@frappe.whitelist()
def get_enrollments(course=None, student=None, group=None):
    if not student:
        student = _resolve_student_from_session()
    if not student:
        return []

    filters = {"student": student}
    if course:
        filters["course"] = course
    if group:
        filters["group"] = group

    enrollments = frappe.get_all(
        "Enrollment",
        filters=filters,
        fields=[
            "name",
            "student",
            "course",
            "group",
            "enrollment_date",
            "status",
            "total_lessons",
            "completed_lessons",
        ],
        order_by="enrollment_date desc",
    )
    return enrollments


@frappe.whitelist()
def create_enrollment(data):
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    enrollment = frappe.new_doc("Enrollment")
    enrollment.update(
        {
            "student": data.get("student"),
            "course": data.get("course"),
            "group": data.get("group"),
            "enrollment_date": data.get("enrollment_date") or frappe.utils.nowdate(),
            "status": data.get("status") or "Active",
        }
    )
    enrollment.insert(ignore_permissions=True)
    return enrollment.name


# --- Student Group APIs ---


@frappe.whitelist()
def get_student_groups(course=None):
    filters = {}
    if course:
        filters["course"] = course

    groups = frappe.get_all(
        "Student Group",
        filters=filters,
        fields=["name", "group_name", "course", "instructor", "max_students", "status"],
        order_by="group_name asc",
    )
    return groups


# --- Academic Session APIs ---


@frappe.whitelist()
def get_academic_sessions(group=None, date=None):
    filters = {}
    if group:
        filters["group"] = group
    if date:
        filters["date"] = date

    sessions = frappe.get_all(
        "Academic Session",
        filters=filters,
        fields=[
            "name",
            "title",
            "group",
            "course",
            "date",
            "start_time",
            "end_time",
            "status",
            "topic",
        ],
        order_by="date desc, start_time asc",
    )
    return sessions


# --- Attendance APIs ---


@frappe.whitelist()
def mark_attendance(data):
    """Mark attendance for a single student in a session."""
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    attendance = frappe.new_doc("Student Attendance")
    attendance.update(
        {
            "student": data.get("student"),
            "academic_session": data.get("academic_session"),
            "status": data.get("status", "Present"),
            "notes": data.get("notes"),
        }
    )
    attendance.insert(ignore_permissions=True)
    return attendance.name


@frappe.whitelist()
def batch_mark_attendance(data):
    """Batch mark attendance for a session.

    data: {
        "academic_session": "AS-...",
        "attendance_list": [
            {"student": "STU-...", "status": "Present", "notes": ""},
            ...
        ]
    }
    """
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

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
        attendance.insert(ignore_permissions=True)
        results.append({"student": entry.get("student"), "status": "created", "name": attendance.name})

    return results


@frappe.whitelist()
def get_attendance(session=None, student=None, date=None):
    filters = {}
    if session:
        filters["academic_session"] = session
    if student:
        filters["student"] = student
    if date:
        filters["date"] = date

    records = frappe.get_all(
        "Student Attendance",
        filters=filters,
        fields=["name", "student", "academic_session", "group", "course", "date", "status", "notes"],
        order_by="date desc",
    )
    return records


# ---------------------------------------------------------------------------
# Stage 3 — Abonements, Payments, Assignments
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_abonement_types():
    types = frappe.get_all(
        "Abonement Type",
        fields=["name", "abonement_name", "total_classes", "price", "validity_days"],
        order_by="abonement_name asc",
    )
    return types


@frappe.whitelist()
def get_student_abonements(student=None):
    filters = {}
    if student:
        filters["student"] = student

    abonements = frappe.get_all(
        "Student Abonement",
        filters=filters,
        fields=[
            "name",
            "student",
            "abonement_type",
            "status",
            "total_classes",
            "classes_remaining",
            "start_date",
            "end_date",
        ],
        order_by="start_date desc",
    )
    return abonements


@frappe.whitelist()
def create_student_abonement(data):
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    ab = frappe.new_doc("Student Abonement")
    ab.update(
        {
            "student": data.get("student"),
            "abonement_type": data.get("abonement_type"),
            "start_date": data.get("start_date") or frappe.utils.nowdate(),
            "status": data.get("status") or "Active",
        }
    )
    ab.insert(ignore_permissions=True)
    return ab.name


@frappe.whitelist()
def get_payments(student=None):
    filters = {}
    if student:
        filters["student"] = student

    payments = frappe.get_all(
        "Payment",
        filters=filters,
        fields=[
            "name",
            "student",
            "student_abonement",
            "amount",
            "payment_method",
            "payment_date",
            "notes",
        ],
        order_by="payment_date desc",
    )
    return payments


@frappe.whitelist()
def create_payment(data):
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    payment = frappe.new_doc("Payment")
    payment.update(
        {
            "student": data.get("student"),
            "student_abonement": data.get("student_abonement"),
            "amount": data.get("amount"),
            "payment_method": data.get("payment_method", "Cash"),
            "payment_date": data.get("payment_date") or frappe.utils.nowdate(),
            "notes": data.get("notes"),
        }
    )
    payment.insert(ignore_permissions=True)
    return payment.name


@frappe.whitelist()
def get_assignments(student=None, lecture=None):
    filters = {}
    if student:
        filters["student"] = student
    if lecture:
        filters["lecture"] = lecture

    assignments = frappe.get_all(
        "Student Assignment",
        filters=filters,
        fields=[
            "name",
            "student",
            "lecture",
            "course",
            "title",
            "status",
            "score",
            "instructor",
            "comment",
            "submitted_at",
            "due_date",
            "file",
        ],
        order_by="modified desc",
    )
    return assignments


@frappe.whitelist()
def submit_assignment(data):
    """Student or Instructor — upload file, set status to Submitted."""
    data = frappe.parse_json(data) if isinstance(data, str) else data

    assignment_name = data.get("name")
    if assignment_name and frappe.db.exists("Student Assignment", assignment_name):
        assignment = frappe.get_doc("Student Assignment", assignment_name)
    else:
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
    assignment.save(ignore_permissions=True)
    return assignment.name


@frappe.whitelist()
def grade_assignment(data):
    """Instructor only — set score, comment, status (Approved/Rejected)."""
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    assignment = frappe.get_doc("Student Assignment", data.get("assignment"))
    assignment.score = data.get("score")
    assignment.comment = data.get("comment")
    assignment.instructor = data.get("instructor") or frappe.session.user
    assignment.status = data.get("status", "Approved")
    assignment.save(ignore_permissions=True)
    return assignment.name


# ---------------------------------------------------------------------------
# Stage 4 — Instructor Dashboard, Journal, Coins, Knowledge Base, Reports
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_instructor_dashboard(instructor=None):
    """Return today's schedule + active groups summary for the instructor."""
    if not instructor:
        instructor = frappe.session.user

    today = frappe.utils.nowdate()

    # Today's sessions (schedule)
    sessions = frappe.get_all(
        "Academic Session",
        filters={
            "date": today,
        },
        fields=[
            "name",
            "title",
            "group",
            "course",
            "date",
            "start_time",
            "end_time",
            "status",
            "topic",
            "room",
            "video_recording_url",
        ],
        order_by="start_time asc",
    )
    # Filter by groups where this user is the instructor
    my_groups = frappe.get_all(
        "Student Group",
        filters={"instructor": instructor},
        pluck="name",
    )
    sessions = [s for s in sessions if s.group in my_groups]

    # Active groups with progress
    groups = frappe.get_all(
        "Student Group",
        filters={"instructor": instructor},
        fields=[
            "name",
            "group_name",
            "course",
            "max_students",
            "status",
        ],
        order_by="group_name asc",
    )
    for g in groups:
        enrolled = frappe.db.count("Enrollment", {"group": g.name, "status": "Active"})
        g.enrolled_count = enrolled

        total_lessons = frappe.db.count("Course Lecture", {"course": g.course})
        completed_lessons = frappe.db.count(
            "Academic Session",
            {"group": g.name, "status": "Completed"},
        )
        g.total_lessons = total_lessons
        g.completed_lessons = completed_lessons
        g.progress_pct = round((completed_lessons / total_lessons * 100) if total_lessons else 0)

    # Count pending assignments for instructor's groups
    group_names = [g.name for g in groups]
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
                {
                    "student": ["in", students_in_my_groups],
                    "status": "Submitted",
                },
            )

    return {
        "sessions": sessions,
        "groups": groups,
        "pending_assignments": pending_assignments,
    }


@frappe.whitelist()
def get_group_students(group, date=None):
    """Return students in a group with their attendance, scores, and coins for the given date."""
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

    # Attendance for today
    attendance_map = {}
    if session:
        records = frappe.get_all(
            "Student Attendance",
            filters={"academic_session": session.name},
            fields=["student", "status", "name"],
        )
        for r in records:
            attendance_map[r.student] = r

    # Assignments/scores per student
    scores_map = {}
    if session:
        course = frappe.db.get_value("Student Group", group, "course")
        lectures = frappe.get_all(
            "Course Lecture",
            filters={"course": course},
            pluck="name",
        )
        if lectures:
            assignments = frappe.get_all(
                "Student Assignment",
                filters={
                    "student": ["in", student_names],
                    "lecture": ["in", lectures],
                },
                fields=["student", "lecture", "score", "status", "name"],
            )
            for a in assignments:
                if a.student not in scores_map:
                    scores_map[a.student] = []
                scores_map[a.student].append(a)

    # Student details with coins
    students = []
    for s_name in student_names:
        student_doc = frappe.get_doc("Student", s_name)
        att = attendance_map.get(s_name)
        students.append(
            {
                "name": s_name,
                "student_name": student_doc.student_name,
                "image": student_doc.image,
                "codify_coins": student_doc.codify_coins or 0,
                "attendance_status": att.status if att else None,
                "attendance_name": att.name if att else None,
                "scores": scores_map.get(s_name, []),
                "parent_name": student_doc.parent_name,
            }
        )

    return {
        "students": students,
        "session": session,
    }


@frappe.whitelist()
def update_student_coins(data):
    """Add or subtract Codify Coins for a student."""
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    student = frappe.get_doc("Student", data.get("student"))
    delta = int(data.get("delta", 0))
    reason = data.get("reason", "")

    student.codify_coins = (student.codify_coins or 0) + delta
    student.save(ignore_permissions=True)

    # You could log coin transactions here

    return {
        "student": student.name,
        "codify_coins": student.codify_coins,
        "delta": delta,
        "reason": reason,
    }


@frappe.whitelist()
def update_student_score(data):
    """Update homework score for a student's assignment in a given lecture."""
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    assignment_name = data.get("assignment")
    if assignment_name and frappe.db.exists("Student Assignment", assignment_name):
        assignment = frappe.get_doc("Student Assignment", assignment_name)
    else:
        # Create new assignment if none exists
        assignment = frappe.new_doc("Student Assignment")
        assignment.student = data.get("student")
        assignment.lecture = data.get("lecture")
        student_name = frappe.db.get_value("Student", assignment.student, "student_name")
        lecture_title = frappe.db.get_value("Course Lecture", assignment.lecture, "title")
        assignment.title = f"{student_name} — {lecture_title}"

    assignment.score = data.get("score")
    assignment.status = data.get("status", "Graded")
    assignment.instructor = data.get("instructor") or frappe.session.user
    if data.get("comment"):
        assignment.comment = data.get("comment")
    assignment.save(ignore_permissions=True)
    return assignment.name


@frappe.whitelist()
def get_lectures_by_module(course=None, module=None):
    """Return lectures grouped by module for knowledge base view."""
    filters = {}
    if course:
        filters["course"] = course
    if module:
        filters["module"] = module

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
            fields=[
                "name",
                "title",
                "position",
                "duration",
                "content_type",
                "content",
                "video_url",
            ],
            order_by="position asc",
        )

    # Also get ungrouped lectures
    ungrouped = frappe.get_all(
        "Course Lecture",
        filters={"course": course, "module": ["is", "not set"]} if course else None,
        fields=["name", "title", "position", "duration", "content_type"],
        order_by="position asc",
    )

    return {
        "modules": modules,
        "ungrouped": ungrouped or [],
    }


@frappe.whitelist()
def update_session_recording(data):
    """Save video recording URL for an academic session."""
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

    session = frappe.get_doc("Academic Session", data.get("session"))
    session.video_recording_url = data.get("video_url")
    session.save(ignore_permissions=True)
    return session.name


# --- Smart Reports ---


@frappe.whitelist()
def get_student_reports(student=None, instructor=None):
    """Return reports for a student, optionally filtered by instructor."""
    filters = {}
    if student:
        filters["student"] = student
    if instructor:
        filters["instructor"] = instructor

    reports = frappe.get_all(
        "Student Report",
        filters=filters,
        fields=[
            "name",
            "student",
            "student_name",
            "instructor",
            "report_date",
            "template",
            "overall_performance",
            "is_published",
        ],
        order_by="report_date desc",
    )
    return reports


@frappe.whitelist()
def get_student_report_detail(report):
    """Return full report content."""
    return frappe.get_doc("Student Report", report)


@frappe.whitelist()
def create_student_report(data):
    """Create or update a smart report for a student."""
    data = frappe.parse_json(data) if isinstance(data, str) else data
    _require_role("Instructor")

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
    report.save(ignore_permissions=True)
    return report.name


@frappe.whitelist()
def delete_student_report(report):
    """Delete a student report."""
    _require_role("Instructor")
    frappe.get_doc("Student Report", report).delete()
    return True
