$(function () {
 
  // ----------------------------
  // Handle login/register
  // ----------------------------
  $("#authForm").submit(function (e) {
    e.preventDefault();
    const username = $("#username").val().trim();
    if (!username) return;

    $.ajax({
      url: "/api/register",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ username }),
      success: function (res) {
        sessionStorage.setItem("welcomeMsg", res.is_new
            ? "👋 Welcome " + res.user.username + "!"
            : "👋 Welcome back " + res.user.username + "!"
          );
        window.location.href = "/chat";
      },
      error: function () {
        // try login instead
        $.ajax({
          url: "/api/login",
          method: "POST",
          contentType: "application/json",
          data: JSON.stringify({ username }),
          success: function (res) {
            sessionStorage.setItem("welcomeMsg", res.is_new
            ? "👋 Welcome " + res.user.username + "!"
            : "👋 Welcome back " + res.user.username + "!"
          );
            window.location.href = "/chat";
          },
          error: function (err) {
            alert(
              "Login failed: " + (err.responseJSON?.error || err.statusText)
            );
          },
        });
      },
    });
  });

  // ----------------------------
  // Handle chat messages
  // ----------------------------
  $("#chatForm").submit(function (e) {
    e.preventDefault();
    const text = $("#chatInput").val().trim();
    if (!text) return;

    appendMessage("user-ask", text);
    $("#chatInput").val("");
    $("#typingIndicator").show();

    $.ajax({
      url: "/api/chat",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ text }),
      success: function (res) {
        appendMessage("assistant", res.reply);
      },
      error: function (err) {
        appendMessage(
          "assistant",
          "⚠️ Error: " + (err.responseJSON?.error || err.statusText)
        );
      },
    });
  });

  // ----------------------------
  // Handle logout
  // ----------------------------
  $("#logoutBtn").click(function () {
    $.post("/api/logout", function () {
      window.location.href = "/login";
    });
  });

  // ----------------------------
  // Append chat message
  // ----------------------------
  function appendMessage(sender, msg) {
    $("#chatBox").append(
      `<div class="msg ${sender}"><div class="msg-text">${msg}</div></div>`
    );
    $("#chatBox").scrollTop($("#chatBox")[0].scrollHeight);
    $("#typingIndicator").hide();
  }

  const msg = sessionStorage.getItem("welcomeMsg");
  if (msg) {
    appendMessage("assistant", msg);
    sessionStorage.removeItem("welcomeMsg"); // clear after showing
  }
});
