// Client-side validation for the Fresher Party registration form.
// The server (app.py) also validates everything before saving.

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("registerForm");

  if (!form) return;

  form.addEventListener("submit", function (e) {
    let isValid = true;

    clearErrors();

    const name = document.getElementById("name");
    const mobile = document.getElementById("mobile");
    const course = document.getElementById("course");
    const year = document.getElementById("year");
    const gender = document.getElementById("gender");
    const enrollmentNumber =
      document.getElementById("enrollment_number");

    // ---------------------------------------------------
    // NAME
    // ---------------------------------------------------

    if (!name.value.trim()) {
      showError(
        name,
        "err-name",
        "Name is required."
      );

      isValid = false;
    }

    // ---------------------------------------------------
    // MOBILE NUMBER
    // ---------------------------------------------------

    const mobilePattern = /^[0-9]{10}$/;

    if (!mobile.value.trim()) {

      showError(
        mobile,
        "err-mobile",
        "Mobile number is required."
      );

      isValid = false;

    } else if (
      !mobilePattern.test(
        mobile.value.trim()
      )
    ) {

      showError(
        mobile,
        "err-mobile",
        "Mobile number must be exactly 10 digits."
      );

      isValid = false;
    }

    // ---------------------------------------------------
    // COURSE
    // ---------------------------------------------------

    if (!course.value.trim()) {

      showError(
        course,
        "err-course",
        "Course is required."
      );

      isValid = false;
    }

    // ---------------------------------------------------
    // YEAR / SEMESTER
    // ---------------------------------------------------

    if (!year.value) {

      showError(
        year,
        "err-year",
        "Please select year/semester."
      );

      isValid = false;
    }

    // ---------------------------------------------------
    // GENDER
    // ---------------------------------------------------

    if (!gender.value) {

      showError(
        gender,
        "err-gender",
        "Please select gender."
      );

      isValid = false;
    }

    // ---------------------------------------------------
    // ENROLLMENT NUMBER
    // ---------------------------------------------------

    if (!enrollmentNumber.value.trim()) {

      showError(
        enrollmentNumber,
        "err-enrollment_number",
        "Enrollment Number is required."
      );

      isValid = false;
    }

    // ---------------------------------------------------
    // STOP FORM IF INVALID
    // ---------------------------------------------------

    if (!isValid) {
      e.preventDefault();
    }
  });


  // =====================================================
  // MOBILE NUMBER - ONLY DIGITS
  // =====================================================

  const mobileInput =
    document.getElementById("mobile");

  if (mobileInput) {

    mobileInput.addEventListener(
      "input",
      function () {

        mobileInput.value =
          mobileInput.value
            .replace(/[^0-9]/g, "")
            .slice(0, 10);

      }
    );
  }


  // =====================================================
  // SHOW ERROR
  // =====================================================

  function showError(
    inputEl,
    errorSpanId,
    message
  ) {

    inputEl.classList.add(
      "input-error"
    );

    const span =
      document.getElementById(
        errorSpanId
      );

    if (span) {
      span.textContent = message;
    }
  }


  // =====================================================
  // CLEAR ERRORS
  // =====================================================

  function clearErrors() {

    document
      .querySelectorAll(
        ".error-text"
      )
      .forEach(
        (el) => {
          el.textContent = "";
        }
      );

    document
      .querySelectorAll(
        "input, select"
      )
      .forEach(
        (el) => {
          el.classList.remove(
            "input-error"
          );
        }
      );
  }

});