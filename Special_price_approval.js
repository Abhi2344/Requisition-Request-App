// Client Script for DocType: Special Price Approval
frappe.ui.form.on('Special Price Approval', {
    refresh: function(frm) {
        if (frm.doc.locked || frm.doc.workflow_state === 'HO Approved') {
            // disable field editing
            frm.set_read_only();
            // keep action buttons like Print Format visible
            // But you can allow specific roles to add comments if needed
            frm.disable_save();
        } else {
            frm.enable_save();
        }
    }
});
