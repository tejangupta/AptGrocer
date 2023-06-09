//
$(document).ready(function() {

	// click on user create form button
    $("#btn-user-create").on('click', function() {
		const regex = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/; 
		const name = $("#name").val().trim();
		const email = $("#email").val().trim();
		const contact = $("#mobile").val().trim();
		const password = $("#password").val();
		const confirm = $("#confirm-password").val();

		if (name.length > 0 && email.length > 0 && contact.length > 0 && password.length > 0 && confirm.length > 0) {
			if (regex.test(email)) {
				if(contact.length === 10) {
					if (password === confirm) {

						const formData = {
							name: name,
							email: email,
							mobile: contact,
							password: password
						}
						
						$.ajax({
							url: "/user/new",
							type: "POST",
							dataType: "json",
							data: JSON.stringify(formData),
							success: function() {
								$("#error-create").addClass("hidden")
								$("#success-create").removeClass("hidden");
							},
							error: function (xhr) {
								$("#success-create").addClass("hidden");
								$("#error-create").removeClass("hidden");
								
								if(xhr.status === 400) {	// receiving 400 status code
									$("#error-create-message").html("This email id is already registered");
								}
							},
							contentType: "application/json"
						});
					} else {
						$("#success-create").addClass("hidden");
						$("#error-create").removeClass("hidden");
						$("#error-create-message").html("Password does not match the confirm password.");
					}
				} else {
					$("#success-create").addClass("hidden");
					$("#error-create").removeClass("hidden");
					$("#error-create-message").html("Invalid contact number.");
				}
			} else {
				$("#success-create").addClass("hidden");
				$("#error-create").removeClass("hidden");
				$("#error-create-message").html("Invalid email id format");
			}
		} else {
			$("#success-create").addClass("hidden");
			$("#error-create").removeClass("hidden");
			$("#error-create-message").html("The fields cannot be blank");
		}
    });

	// click on user login form button
    $("#btn-error-close").on('click', function() {
		$("#error-create").addClass("hidden");
	});
});
