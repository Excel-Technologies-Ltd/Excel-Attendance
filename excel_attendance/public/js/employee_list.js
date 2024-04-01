frappe.listview_settings['Employee'] = {
    refresh: function(listview) {
        listview.page.add_inner_button("Set Device Id", function() {
            frappe.call({
                method: 'excel_attendance.checkin.set_device_id',
                callback: function(r) {
                    if(r.message) {
                        frappe.msgprint("Device IDs set successfully.");
                        // Optionally, you can refresh the list view after setting device IDs
                        listview.refresh();
                    }
                }
            });
        });
    }
};
