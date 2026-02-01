# Copyright (c) 2026, irfyx and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CustomApprovalMatrix(Document):
    def validate(self):
        self.validate_amount_range()
        self.check_overlap()

    def validate_amount_range(self):
        if self.min_amount > self.max_amount:
            frappe.throw("Minimum Amount cannot be greater than Maximum Amount")

    def check_overlap(self):
        existing = frappe.db.sql("""
            SELECT name FROM `tabCustom Approval Matrix`
            WHERE
                reference_doctype = %s
                AND company = %s
                AND is_active = 1
                AND name != %s
                AND (
                    (%s BETWEEN min_amount AND max_amount)
                    OR
                    (%s BETWEEN min_amount AND max_amount)
                )
        """, (
            self.reference_doctype,
            self.company,
            self.name or "",
            self.min_amount,
            self.max_amount
        ))

        if existing:
            frappe.throw("Approval range overlaps with an existing rule")
