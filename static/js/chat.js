$(function() {
  // Handle login/register
  $("#authForm").submit(function(e) {
    e.preventDefault();
    const username = $("#username").val().trim();
    if (!username) return;

    $.ajax({
      url: "/api/register", // try register first
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ username }),
      success: function(res) {
        $("#loginSection").hide();
        $("#chatContainer").show();
        appendMessage("assistant", "👋 Welcome " + res.user.username + "!");
      },
      error: function(xhr) {
        // If already exists, fallback to login
        $.ajax({
          url: "/api/login",
          method: "POST",
          contentType: "application/json",
          data: JSON.stringify({ username }),
          success: function(res) {
            $("#loginSection").hide();
            $("#chatContainer").show();
            appendMessage("assistant", "👋 Welcome back " + res.user.username + "!");
          },
          error: function(err) {
            alert("Login failed: " + (err.responseJSON?.error || err.statusText));
          }
        });
      }
    });
  });

  // Handle chat messages
  $("#chatForm").submit(function(e) {
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
      success: function(res) {
        appendMessage("assistant", res.reply);
      },
      error: function(err) {
        appendMessage("assistant", "⚠️ Error: " + (err.responseJSON?.error || err.statusText));
      }
    });
  });

  // Handle logout
  $("#logoutBtn").click(function() {
    $.post("/api/logout", function() {
      // Clear client-side state
      localStorage.clear();
      sessionStorage.clear();
      document.cookie = "";

      
      appendMessage("assistant", "✅ Logged out.");
      $("#chatContainer").hide();
      $("#loginSection").show();
      $("#username").val("");
      $("#chatBox").empty();
      $("#typingIndicator").hide();
      window.location.reload();

    });
  });

  // Append chat message
  function appendMessage(sender, msg) {
    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    $("#chatBox").append(
      `<div class="msg ${sender}">
         <div class="msg-text">${msg}</div>
       </div>`
    );
    $("#chatBox").scrollTop($("#chatBox")[0].scrollHeight);
    $("#typingIndicator").hide();
  }
});
