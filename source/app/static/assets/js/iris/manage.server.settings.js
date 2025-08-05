function update_settings() {
    var data_sent = $('form#form_srv_settings').serializeObject();
    data_sent['prevent_post_mod_repush'] = $('#prevent_post_mod_repush').is(":checked");
    data_sent['prevent_post_objects_repush'] = $('#prevent_post_objects_repush').is(":checked");
    data_sent['password_policy_upper_case'] = $('#password_policy_upper_case').is(":checked");
    data_sent['password_policy_lower_case'] = $('#password_policy_lower_case').is(":checked");
    data_sent['password_policy_digit'] = $('#password_policy_digit').is(":checked");
    data_sent['enforce_mfa'] = $('#enforce_mfa').is(":checked");
    data_sent['password_policy_min_length'] = $('#password_policy_min_length').val().toString();

    post_request_api('/manage/settings/update', JSON.stringify(data_sent), true)
    .done((data) => {
        notify_auto_api(data);
    });
}


function init_db_backup() {

    get_request_api('/manage/server/backups/make-db')
    .done((data) => {
            msg = ""
            for (idx in data.data) {
                msg += data.data[idx] + '\n';
            }
            swal("Done",
             msg,
            {
                icon: "success"
            });
    })
    .fail((error) => {
        for (idx in error.responseJSON.data) {
            msg += data.data[idx] + '\n';
        }

        swal("Error",
         msg,
        {
            icon: "error"
        });
    });
}

function check_delete_cases() {
    var start_date = $('#delete_start_date').val();
    var end_date = $('#delete_end_date').val();
    
    if (!start_date || !end_date) {
        swal("Error", "Please select both start and end dates.", {
            icon: "error"
        });
        return;
    }
    
    if (start_date > end_date) {
        swal("Error", "Start date must be before or equal to end date.", {
            icon: "error"
        });
        return;
    }
    
    // Show loading state
    $('#delete_cases_btn').prop('disabled', true).text('Checking...');
    
    var data = {
        start_date: start_date,
        end_date: end_date,
        csrf_token: $('#csrf_token').val()
    };
    
    // Set a longer timeout for bulk operations
    $.ajaxSetup({
        timeout: 900000  // 15 minutes timeout (matches nginx)
    });
    
    post_request_api('/manage/settings/check-delete-cases', JSON.stringify(data), true)
    .done((response) => {
        $('#delete_cases_btn').prop('disabled', false).text('Delete Cases');
        
        if (response.data.cases_count === 0) {
            swal("No Cases Found", "No cases found in the specified date range (excluding the protected primary case).", {
                icon: "info"
            });
            return;
        }
        
        var message = `This will permanently delete:\n\n` +
                     `• ${response.data.cases_count} cases\n` +
                     `• ${response.data.alerts_count} alerts\n` +
                     `• All related assets, IOCs, comments, and other data\n\n` +
                     `Note: The primary case (ID: 1) will be protected from deletion.\n\n` +
                     `This action cannot be undone. Are you sure you want to continue?`;
        
        swal({
            title: "Confirm Deletion",
            text: message,
            icon: "warning",
            buttons: {
                cancel: {
                    text: "Cancel",
                    value: null,
                    visible: true,
                    className: "btn btn-secondary",
                    closeModal: true,
                },
                confirm: {
                    text: "Confirm Delete",
                    value: true,
                    visible: true,
                    className: "btn btn-danger",
                    closeModal: true
                }
            },
            dangerMode: true,
        })
        .then((willDelete) => {
            if (willDelete) {
                delete_cases(start_date, end_date);
            }
        });
    })
    .fail((error) => {
        $('#delete_cases_btn').prop('disabled', false).text('Delete Cases');
        swal("Error", "Failed to check cases. Please try again.", {
            icon: "error"
        });
    });
}

function delete_cases(start_date, end_date) {
    // Show loading state
    $('#delete_cases_btn').prop('disabled', true).text('Deleting...');
    
    var data = {
        start_date: start_date,
        end_date: end_date,
        csrf_token: $('#csrf_token').val()
    };
    
    // Set a longer timeout for bulk deletion operations
    $.ajaxSetup({
        timeout: 900000  // 15 minutes timeout (matches nginx)
    });
    
    post_request_api('/manage/settings/delete-cases', JSON.stringify(data), true)
    .done((response) => {
        $('#delete_cases_btn').prop('disabled', false).text('Delete Cases');
        
        var message = `Successfully deleted:\n\n` +
                     `• ${response.data.cases_count} cases\n` +
                     `• ${response.data.alerts_count} alerts\n` +
                     `• All related data\n\n` +
                     `Note: The primary case (ID: 1) was protected from deletion.`;
        
        swal("Deletion Complete", message, {
            icon: "success"
        });
        
        // Clear the date inputs
        $('#delete_start_date').val('');
        $('#delete_end_date').val('');
    })
    .fail((error) => {
        $('#delete_cases_btn').prop('disabled', false).text('Delete Cases');
        
        var errorMsg = "Failed to delete cases.";
        if (error.responseJSON && error.responseJSON.msg) {
            errorMsg = error.responseJSON.msg;
        }
        
        swal("Error", errorMsg, {
            icon: "error"
        });
    });
}