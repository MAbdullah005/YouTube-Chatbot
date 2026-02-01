const loadBtn = document.getElementById("loadBtn");
const askBtn = document.getElementById("askBtn");
const videoInput = document.getElementById("videoUrl");
const questionInput = document.getElementById("question");
const chatBox = document.getElementById("chatBox");
const videoPlayer = document.getElementById("ytPlayer");

// --------------------
// Extract YouTube ID
// --------------------
function extractVideoId(url) {
    const regExp =
        /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([^&?/]+)/;
    const match = url.match(regExp);
    return match ? match[1] : null;
}

// --------------------
// Append chat message
// --------------------
function appendMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = "message";
    msg.innerText = text;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msg;
}

// --------------------
// Load video
// --------------------
loadBtn.addEventListener("click", () => {
    const url = videoInput.value.trim();
    const videoId = extractVideoId(url);

    if (!videoId) {
        alert("Invalid YouTube URL");
        return;
    }

    videoPlayer.src = `https://www.youtube.com/embed/${videoId}`;
});

// --------------------
// Ask question (STREAM)
// --------------------
askBtn.addEventListener("click", () => {
    const video_url = videoInput.value.trim();
    const question = questionInput.value.trim();

    if (!video_url || !question) {
        alert("Enter video URL and question");
        return;
    }

    appendMessage(question, "user");
    questionInput.value = "";

    const botMsg = appendMessage("🤖 ", "bot");

    const streamUrl = `/stream?video_url=${encodeURIComponent(
        video_url
    )}&question=${encodeURIComponent(question)}`;

    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
        if (event.data === "[DONE]") {
            eventSource.close();
            return;
        }

        botMsg.innerText += event.data;
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    eventSource.onerror = () => {
        botMsg.innerText += "\n\n❌ Stream error";
        eventSource.close();
    };
});
