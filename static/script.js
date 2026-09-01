// Client-side validation for the Fresher Party registration form.
// This runs BEFORE the form is submitted to Flask, giving instant feedback.
// The server (app.py) still re-validates everything for security.

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("registerForm");
  if (!form) return; // script also loads on other pages; do nothing there

  form.addEventListener("submit", function (e) {
    let isValid = true;
    clearErrors();

    const name = document.getElementById("name");
    const email = document.getElementById("email");
    const mobile = document.getElementById("mobile");
    const course = document.getElementById("course");
    const year = document.getElementById("year");
    const gender = document.getElementById("gender");
    const studentId = document.getElementById("student_id");

    if (!name.value.trim()) {
      showError(name, "err-name", "Name is required.");
      isValid = false;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.value.trim()) {
      showError(email, "err-email", "Email is required.");
      isValid = false;
    } else if (!emailPattern.test(email.value.trim())) {
      showError(email, "err-email", "Enter a valid email address.");
      isValid = false;
    }

    const mobilePattern = /^[0-9]{10}$/;
    if (!mobile.value.trim()) {
      showError(mobile, "err-mobile", "Mobile number is required.");
      isValid = false;
    } else if (!mobilePattern.test(mobile.value.trim())) {
      showError(mobile, "err-mobile", "Mobile number must be exactly 10 digits.");
      isValid = false;
    }

    if (!course.value.trim()) {
      showError(course, "err-course", "Course is required.");
      isValid = false;
    }

    if (!year.value) {
      showError(year, "err-year", "Please select year/semester.");
      isValid = false;
    }

    if (!gender.value) {
      showError(gender, "err-gender", "Please select gender.");
      isValid = false;
    }

    if (!studentId.value.trim()) {
      showError(studentId, "err-student_id", "Student ID is required.");
      isValid = false;
    }

    if (!isValid) {
      e.preventDefault(); // stop the form from submitting to Flask
    }
  });

  // Only allow digits in the mobile field, live as the user types
  const mobileInput = document.getElementById("mobile");
  if (mobileInput) {
    mobileInput.addEventListener("input", function () {
      mobileInput.value = mobileInput.value.replace(/[^0-9]/g, "").slice(0, 10);
    });
  }

  function showError(inputEl, errorSpanId, message) {
    inputEl.classList.add("input-error");
    const span = document.getElementById(errorSpanId);
    if (span) span.textContent = message;
  }

  function clearErrors() {
    document.querySelectorAll(".error-text").forEach((el) => (el.textContent = ""));
    document.querySelectorAll("input, select").forEach((el) => el.classList.remove("input-error"));
  }
});