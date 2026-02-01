import frappe
from frappe.utils import now

def check_approval_matrix(doc, method):
    # sirf submit ke waqt approve mark karo
    if doc.docstatus != 1:
        return

    amount = doc.grand_total
    company = doc.company

    matrix = frappe.db.sql("""
        SELECT
            required_role,
            approved_by_user,
            `condition`,
            approval_level
        FROM `tabCustom Approval Matrix`
        WHERE
            reference_doctype = %s
            AND company = %s
            AND is_active = 1
            AND %s BETWEEN min_amount AND max_amount
        ORDER BY approval_level ASC
        LIMIT 1
    """, (doc.doctype, company, amount), as_dict=True)

    if not matrix:
        return

    rule = matrix[0]

    # -------------------------
    # CONDITION CHECK
    # -------------------------
    if rule.condition:
        if not frappe.safe_eval(rule.condition, None, {"doc": doc}):
            return

    # -------------------------
    # AUTHORIZATION CHECK
    # -------------------------
    if rule.approved_by_user:
        if frappe.session.user != rule.approved_by_user:
            frappe.throw("Only assigned approver can submit this document")

    elif rule.required_role not in frappe.get_roles():
        frappe.throw(f"Approval required from role: {rule.required_role}")

    # =========================
    # ✅ NEW CODE SECTION START
    # =========================

    # 1️⃣ Approval trace on document
    doc.approved_by = frappe.session.user
    doc.approved_on = now()
    doc.approval_status = "Approved"

    # 2️⃣ Maintain approval level (future multi-level ready)
    doc.approval_level = rule.approval_level or 1

    # 3️⃣ Approval history (Child Table)
    if hasattr(doc, "approval_history"):
        doc.append("approval_history", {
            "approved_by": frappe.session.user,
            "approved_on": now(),
            "approval_level": rule.approval_level,
            "remarks": "Approved during submit"
        })

    # 4️⃣ Clear pending approver info
    if hasattr(doc, "current_approver_role"):
        doc.current_approver_role = None

    # =========================
    # ✅ NEW CODE SECTION END
    # =========================
