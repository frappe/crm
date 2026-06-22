import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate, add_days


class TestStudentAbonementFIFO(FrappeTestCase):
    """Test FIFO deduction logic in Student Attendance -> Student Abonement."""

    def setUp(self):
        self.contact = frappe.get_doc(
            {
                "doctype": "Contact",
                "first_name": "FIFO",
                "last_name": "Test",
                "email_id": "fifo@test.test",
            }
        ).insert(ignore_permissions=True)

        self.student = frappe.get_doc(
            {
                "doctype": "Student",
                "student_name": "FIFO Test",
                "contact": self.contact.name,
            }
        ).insert(ignore_permissions=True)

        self.abotype = frappe.get_doc(
            {
                "doctype": "Abonement Type",
                "abonement_name": "Test 10 Classes",
                "total_classes": 10,
                "validity_days": 60,
                "price": 5000,
            }
        ).insert(ignore_permissions=True)

        self.old_abonement = frappe.get_doc(
            {
                "doctype": "Student Abonement",
                "student": self.student.name,
                "abonement_type": self.abotype.name,
                "start_date": add_days(nowdate(), -10),
                "status": "Active",
                "total_classes": 10,
                "classes_remaining": 10,
            }
        ).insert(ignore_permissions=True)

        self.new_abonement = frappe.get_doc(
            {
                "doctype": "Student Abonement",
                "student": self.student.name,
                "abonement_type": self.abotype.name,
                "start_date": nowdate(),
                "status": "Active",
                "total_classes": 10,
                "classes_remaining": 10,
            }
        ).insert(ignore_permissions=True)

        # Shared resources: Course + Student Group (reused by all sessions)
        self.course = frappe.get_doc(
            {"doctype": "Course", "title": "FIFO Test Course"}
        ).insert(ignore_permissions=True)

        self.group = frappe.get_doc(
            {
                "doctype": "Student Group",
                "group_name": "FIFO Test Group",
                "course": self.course.name,
                "instructor": "Administrator",
                "schedule": [
                    {
                        "day_of_week": "Monday",
                        "start_time": "10:00:00",
                        "end_time": "11:30:00",
                    }
                ],
            }
        ).insert(ignore_permissions=True)

    _session_counter = 0

    def _make_session(self, suffix="", hour_offset=0):
        """Create a unique Academic Session with non-overlapping time."""
        TestStudentAbonementFIFO._session_counter += 1
        n = TestStudentAbonementFIFO._session_counter
        h = 10 + n  # 10:00, 11:00, 12:00, ...
        return frappe.get_doc(
            {
                "doctype": "Academic Session",
                "title": f"Session {suffix}" if suffix else f"Session {n}",
                "group": self.group.name,
                "date": nowdate(),
                "start_time": f"{h:02d}:00:00",
                "end_time": f"{h+1:02d}:00:00",
            }
        ).insert(ignore_permissions=True)

    def _create_attendance(self, status="Present", session=None):
        """Helper to create a Student Attendance record."""
        if session is None:
            session = self._make_session()
        doc = frappe.get_doc(
            {
                "doctype": "Student Attendance",
                "student": self.student.name,
                "academic_session": session.name,
                "status": status,
            }
        )
        doc.insert(ignore_permissions=True)
        return doc

    def tearDown(self):
        frappe.db.rollback()

    # ---------------------------------------------------------------
    # Tests
    # ---------------------------------------------------------------

    def test_fifo_deducts_from_oldest_abonement(self):
        """Attendance deduction hits the oldest (first-created) abonement."""
        self._create_attendance("Present")

        old = frappe.get_doc("Student Abonement", self.old_abonement.name)
        new = frappe.get_doc("Student Abonement", self.new_abonement.name)

        self.assertEqual(old.classes_remaining, 9)
        self.assertEqual(new.classes_remaining, 10)

    def test_fifo_multiple_deductions(self):
        """Multiple attendance records continue deducting from the same oldest abonement."""
        s1 = self._make_session("m1")
        s2 = self._make_session("m2")
        self._create_attendance("Present", session=s1)
        self._create_attendance("Late", session=s2)

        old = frappe.get_doc("Student Abonement", self.old_abonement.name)
        self.assertEqual(old.classes_remaining, 8)

    def test_fifo_depletes_oldest_then_moves_to_next(self):
        """Once the oldest abonement reaches 0, deduction moves to the next oldest."""
        frappe.db.set_value(
            "Student Abonement", self.old_abonement.name, "classes_remaining", 1
        )

        s1 = self._make_session("dep1")
        self._create_attendance("Present", session=s1)
        old = frappe.get_doc("Student Abonement", self.old_abonement.name)
        self.assertEqual(old.classes_remaining, 0)
        self.assertEqual(old.status, "Expired")

        s2 = self._make_session("dep2")
        self._create_attendance("Late", session=s2)
        new = frappe.get_doc("Student Abonement", self.new_abonement.name)
        self.assertEqual(new.classes_remaining, 9)

    def test_restore_on_absent(self):
        """Changing Present -> Absent restores the class to the abonement."""
        att = self._create_attendance("Present")
        old = frappe.get_doc("Student Abonement", self.old_abonement.name)
        self.assertEqual(old.classes_remaining, 9)
        self.assertIsNotNone(att.linked_abonement)

        att.status = "Absent"
        att.save(ignore_permissions=True)

        old.reload()
        self.assertEqual(old.classes_remaining, 10)

    def test_restore_on_excused(self):
        """Changing Present -> Excused also restores the class."""
        att = self._create_attendance("Present")
        old = frappe.get_doc("Student Abonement", self.old_abonement.name)
        self.assertEqual(old.classes_remaining, 9)

        att.status = "Excused"
        att.save(ignore_permissions=True)

        old.reload()
        self.assertEqual(old.classes_remaining, 10)

    def test_throw_when_no_abonement_available(self):
        """Attendance without any valid abonement raises an error."""
        frappe.db.set_value(
            "Student Abonement", self.old_abonement.name, "classes_remaining", 0
        )
        frappe.db.set_value(
            "Student Abonement", self.old_abonement.name, "status", "Expired"
        )
        frappe.db.set_value(
            "Student Abonement", self.new_abonement.name, "classes_remaining", 0
        )
        frappe.db.set_value(
            "Student Abonement", self.new_abonement.name, "status", "Expired"
        )

        with self.assertRaises(frappe.ValidationError):
            self._create_attendance("Present")

    def test_late_is_treated_as_present(self):
        """'Late' status should also trigger deduction."""
        self._create_attendance("Late")
        old = frappe.get_doc("Student Abonement", self.old_abonement.name)
        self.assertEqual(old.classes_remaining, 9)

    def test_absent_does_not_deduct(self):
        """'Absent' status should NOT trigger any deduction."""
        self._create_attendance("Absent")
        old = frappe.get_doc("Student Abonement", self.old_abonement.name)
        self.assertEqual(old.classes_remaining, 10)
