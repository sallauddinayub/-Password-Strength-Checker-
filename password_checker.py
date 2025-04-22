from flask import Flask, render_template_string, request, session
import re
import math

app = Flask(__name__)
app.secret_key = 'your-secret-key'

COMMON_PASSWORDS = {
    '123456', 'password', '123456789', '12345678', '12345',
    '1234567', 'qwerty', 'abc123', 'football', 'monkey',
    '111111', 'letmein', '1234', '123123', 'admin'
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Password Strength Checker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #89f7fe, #66a6ff);
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 450px;
        }
        h2 { text-align: center; }
        .field {
            margin-top: 15px;
            position: relative;
            width: 100%;
        }
        .field input[type="password"],
        .field input[type="text"] {
            width: 100%;
            padding: 10px 40px 10px 10px;
            font-size: 16px;
            box-sizing: border-box;
        }
        .toggle {
            position: absolute;
            top: 50%;
            right: 10px;
            transform: translateY(-50%);
            cursor: pointer;
            font-size: 18px;
        }
        .progress-bar {
            width: 100%;
            height: 10px;
            background: #eee;
            border-radius: 5px;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            border-radius: 5px;
            transition: width 0.3s ease;
        }
        .feedback {
            margin-top: 15px;
            font-weight: bold;
            text-align: center;
        }
        .suggestion {
            font-size: 14px;
            color: #555;
            margin-top: 10px;
        }
        .match-check {
            font-size: 14px;
            margin-top: 5px;
        }
        .weak { color: red; }
        .medium { color: orange; }
        .strong { color: green; }
        button {
            margin-top: 20px;
            width: 100%;
            padding: 10px;
            background-color: #007BFF;
            color: white;
            border: none;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
        }
    </style>
</head>
<body>
<div class="container">
    <h2>Password Strength Checker</h2>
    <form method="POST">
        <div class="field">
            <input type="password" name="password" id="password" placeholder="Enter password" required oninput="checkPassword()">
            <span class="toggle" onclick="toggleVisibility('password', this)">👁️</span>
        </div>
        <div class="field">
            <input type="password" name="confirm_password" id="confirm_password" placeholder="Confirm password" oninput="checkMatch()">
            <span class="toggle" onclick="toggleVisibility('confirm_password', this)">👁️</span>
            <div id="matchMessage" class="match-check"></div>
        </div>

        <div class="progress-bar"><div id="progress" class="progress-fill"></div></div>
        <div class="feedback" id="feedbackText"></div>
        <div class="suggestion" id="suggestionText"></div>

        <button type="submit">Submit</button>
    </form>

    {% if result %}
        <div class="feedback {{ result_class }}">{{ result }}</div>
    {% endif %}
</div>

<script>
    function toggleVisibility(id, icon) {
        const field = document.getElementById(id);
        if (field.type === "password") {
            field.type = "text";
            icon.textContent = "🙈";
        } else {
            field.type = "password";
            icon.textContent = "👁️";
        }
    }

    function checkPassword() {
        const pw = document.getElementById('password').value;
        const progress = document.getElementById('progress');
        const feedback = document.getElementById('feedbackText');
        const suggestion = document.getElementById('suggestionText');

        let score = 0;
        const suggestions = [];

        if (pw.length >= 8) score++;
        else suggestions.push("Use at least 8 characters");

        if (/[A-Z]/.test(pw)) score++; else suggestions.push("Add an uppercase letter");
        if (/[a-z]/.test(pw)) score++;
        if (/\d/.test(pw)) score++; else suggestions.push("Add a number");
        if (/[!@#$%^&*(),.?":{}|<>]/.test(pw)) score++; else suggestions.push("Add a special character");

        if (["123456", "password", "qwerty"].includes(pw)) {
            score = 0;
            suggestions.push("Don't use common passwords");
        }

        let width = "0%", color = "red", level = "Weak";
        if (score >= 4) { width = "100%"; color = "green"; level = "Strong"; }
        else if (score === 3) { width = "66%"; color = "orange"; level = "Moderate"; }
        else if (score <= 2) { width = "33%"; color = "red"; level = "Weak"; }

        progress.style.width = width;
        progress.style.backgroundColor = color;
        feedback.textContent = level;
        feedback.className = "feedback " + level.toLowerCase();
        suggestion.textContent = (level === "Strong") ? "" : "Suggestions: " + suggestions.join(", ");
    }

    function checkMatch() {
        const pw = document.getElementById('password').value;
        const cpw = document.getElementById('confirm_password').value;
        const msg = document.getElementById('matchMessage');
        if (cpw && pw !== cpw) {
            msg.textContent = "Passwords do not match";
            msg.style.color = "red";
        } else {
            msg.textContent = pw && cpw ? "Passwords match" : "";
            msg.style.color = "green";
        }
    }
</script>
</body>
</html>
"""

def calculate_entropy(password):
    charset = 0
    if re.search(r'[a-z]', password): charset += 26
    if re.search(r'[A-Z]', password): charset += 26
    if re.search(r'\d', password): charset += 10
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): charset += 32
    return len(password) * math.log2(charset) if charset else 0

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    result_class = ""
    if request.method == "POST":
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        prev_password = session.get("last_password")
        if prev_password and password == prev_password:
            result = "Password is too similar to the last one!"
            result_class = "weak"
        elif password in COMMON_PASSWORDS:
            result = "Common password detected! Choose something more secure."
            result_class = "weak"
        elif password != confirm:
            result = "Passwords do not match!"
            result_class = "weak"
        else:
            entropy = calculate_entropy(password)
            if entropy > 60:
                result = "Strong password with high entropy!"
                result_class = "strong"
            elif entropy > 40:
                result = "Moderately secure password."
                result_class = "medium"
            else:
                result = "Weak password. Improve it."
                result_class = "weak"
            session["last_password"] = password

    return render_template_string(HTML_TEMPLATE, result=result, result_class=result_class)

if __name__ == "__main__":
    app.run(debug=True)
