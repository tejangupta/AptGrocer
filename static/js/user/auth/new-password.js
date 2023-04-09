//
$(document).ready(function() {

	// click on user login form button
    $("#btn-user-update").on('click', function() {
		const password = $("#new-password").val();
		const confirm = $("#confirm-new-password").val();

		if (password.length > 0 && confirm.length > 0) {
			if (password === confirm) {

				const formData = {
					password: password
				}

				const verificationToken = window.location.href.split('/').pop();
				const url = `/update_password/${verificationToken}`;
				$.ajax({
					url: url,
					type: "POST",
					dataType: "json",
					data: JSON.stringify(formData),
					success: function() {
						$("#error-login").addClass("hidden")
						$("#success-login").removeClass("hidden");
					},
					error: function (xhr) {
						$("#success-login").addClass("hidden");
						$("#error-login").removeClass("hidden");

						if(xhr.status === 400) {	// receiving 400 status code
							const response = JSON.parse(xhr.responseText);
							$("#error-login-message").html(response.message);
						}
					},
					contentType: "application/json"
				});

			} else {
				$("#success-login").addClass("hidden");
				$("#error-login").removeClass("hidden");
				$("#error-login-message").html("Passwords do not match");
			}
		} else {
			$("#success-login").addClass("hidden");
			$("#error-login").removeClass("hidden");
			$("#error-login-message").html("The fields cannot be blank");
		}
    });

	// click on user login form button
    $("#btn-error-close").on('click', function() {
		$("#error-login").addClass("hidden");
	});

	// click on user login form button
    $("#btn-err-close").on('click', function() {
		$("#err-login").addClass("hidden");
	});
});
