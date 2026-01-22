const loadBtn = document.getElementById("loadBtn");
const askBtn = document.getElementById("askBtn");
const videoInput = document.getElementById("videoUrl");
const questionInput = document.getElementById("question");
const chatBox = document.getElementById("chatBox");
const videoPlayer = document.getElementById("ytPlayer");

// Extract video ID
function extractVideoId(url) {
    try {
        if (!url.startsWith("http")) {
            url = "https://" + url;
        }
        const parsed = new URL(url);

        if (parsed.hostname.includes("youtube.com")) {
            return parsed.searchParams.get("v");
        }
        if (parsed.hostname.includes("youtu.be")) {
            return parsed.pathname.slice(1);
        }
        return null;
    } catch {
        return null;
    }
}

// Load video
loadBtn.addEventListener("click", () => {
    const videoId = extractVideoId(videoInput.value);
    if (!videoId) {
        alert("Invalid YouTube URL");
        return;
    }
    videoPlayer.src = `https://www.youtube.com/embed/${videoId}`;
});

// Add message to UI
function appendMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = `message ${sender}`;
    msg.innerText = text;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msg;
}

// Ask question
askBtn.addEventListener("click", async () => {
    console.log("ASK CLICKED");

    const video_url = videoInput.value;
    const question = questionInput.value.trim();

    if (!video_url || !question) {
        alert("Enter video URL and question");
        return;
    }

    appendMessage(question, "user");
    questionInput.value = "";

    const thinking = appendMessage("Thinking...", "bot");

    try {
        const res = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_url, question })
        });

        const data = await res.json();
        thinking.innerText = "🤖 " + (data.answer || "No answer");

    } catch (err) {
        thinking.innerText = "Error: " + err.message;
    }
});
