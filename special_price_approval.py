import frappe
from frappe.utils import nowdate

def on_update_special_price_approval(doc, method=None):
    # Only run when workflow_state becomes HO Approved
    # and when doc is already submitted (doc.docstatus == 1)
    if getattr(doc, "workflow_state", "") == "HO Approved" and doc.docstatus == 1:
        # Avoid duplicate SO creation
        if doc.sales_order_reference:
            return

        create_sales_order_from_approval(doc)

def create_sales_order_from_approval(doc):
    # Create Sales Order
    so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": doc.customer,
        "transaction_date": nowdate(),
        "delivery_date": None,
        "territory": doc.territory or "",
        "special_price_approval_ref": doc.name,  # custom field on SO
        "items": []
    })

    for row in doc.get("items") or []:
        rate = row.approved_rate if row.approved_rate else row.requested_rate
        item = {
            "doctype": "Sales Order Item",
            "item_code": row.item_code,
            "qty": row.quantity,
            "rate": rate,
            "amount": (row.quantity or 0) * (rate or 0),
            # add other mapping if needed like warehouse, uom...
        }
        so.append("items", item)

    # set any other SO defaults such as sales_person if you map
    if doc.sales_person:
        so.set("sales_person", doc.sales_person)

    so.insert(ignore_permissions=True)  # or use .save() ; prefer insert to create new record
    # Optionally submit the Sales Order automatically? The acceptance didn't require auto-submit.
    # If you want auto-submit:
    # so.submit()

    # Link back
    doc.db_set("sales_order_reference", so.name)
    doc.db_set("locked", 1)  # lock for front-end to disable editing

    # Add timeline comment & notify
    frappe.add_comment(doc=doc, comment=f"Sales Order {so.name} created after HO approval.")
    # Notify ASM via email
    try:
        frappe.sendmail(
            recipients=[doc.owner],  # doc.owner is user who created
            subject=f"Sales Order {so.name} created from Special Price Approval {doc.name}",
            message=f"Sales Order {so.name} has been created for Special Price Approval {doc.name}."
        )
    except Exception:
        # do not fail main transaction on email errors
        frappe.log_error("Failed to send SO creation email", "special_price_approval")

