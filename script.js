function login(event) {
  event.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  // Demo credentials
  if (email === "admin@loyalink.com" && password === "123456") {
    window.location.href = "dashboard.html";
  } else {
    alert("Invalid email or password");
  }
}
