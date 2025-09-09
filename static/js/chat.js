$(function() {
  // Handle login/register
  $("#authForm").submit(function(e) {
    e.preventDefault();
    const username = $("#username").val();
    $.ajax({
      url: "/api/register", // try register first
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({username}),
      success: function(res) {
        $("#chatContainer").show();
        $("#authForm").hide();
        appendMessage("System", "Welcome " + res.user.username + "!");
      },
      error: function(xhr) {
        // If already exists, fallback to login
        $.ajax({
          url: "/api/login",
          method: "POST",
          contentType: "application/json",
          data: JSON.stringify({username}),
          success: function(res) {
            $("#chatContainer").show();
            $("#authForm").hide();
            appendMessage("System", "Welcome back " + res.user.username + "!");
          },
          error: function(err) {
            alert("Login failed: " + err.responseJSON.error);
          }
        });
      }
    });
  });

  // Handle chat messages
  $("#chatForm").submit(function(e) {
    e.preventDefault();
    const text = $("#chatInput").val();
    appendMessage("You", text);
    $("#chatInput").val("");
    $.ajax({
      url: "/api/chat",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({text}),
      success: function(res) {
        appendMessage("Assistant", res.reply);
      },
      error: function(err) {
        appendMessage("System", "Error: " + err.responseJSON.error);
      }
    });
  });

  // Handle logout
  $("#logoutBtn").click(function() {
    $.post("/api/logout", function(res) {
      // Clear any client-side stored data
      localStorage.clear();
      sessionStorage.clear();
      document.cookie = "";

      $("#chatContainer").hide();
      $("#authForm").show();
      $("#username").val("");
      appendMessage("System", "Logged out.");
      window.location.reload();
    });
  });

  function appendMessage(sender, msg) {
    $("#chatBox").append("<p><strong>" + sender + ":</strong> " + msg + "</p>");
    $("#chatBox").scrollTop($("#chatBox")[0].scrollHeight);
  }
});
