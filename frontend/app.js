const loadBtn = document.getElementById("loadBtn");
const askBtn = document.getElementById("askBtn");
const videoInput = document.getElementById("videoUrl");
const questionInput = document.getElementById("question");
const chatBox = document.getElementById("chatBox");
const videoPlayer = document.getElementById("ytPlayer");

let videoLoaded = false;

// Extract video ID from any YouTube URL
function extractVideoId(url) {
    try {
        if (!url.startsWith("http")) url = "https://" + url;
        const parsed = new URL(url);

        if (parsed.hostname.includes("youtube.com")) {
            if (parsed.pathname === "/watch") return parsed.searchParams.get("v");
            if (parsed.pathname.startsWith("/embed/")) return parsed.pathname.split("/embed/")[1];
        }
        if (parsed.hostname.includes("youtu.be")) return parsed.pathname.slice(1);

        return null;
    } catch {
        return null;
    }
}

// ---------------- Load video dynamically ----------------
loadBtn.addEventListener("click", () => {
    const url = videoInput.value.trim();
    const videoId = extractVideoId(url);

    if (!videoId) {
        alert("❌ Invalid YouTube URL");
        return;
    }

    // Update iframe dynamically
    videoPlayer.src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
    videoLoaded = true;

    // Clear previous chat
    chatBox.innerHTML = "";
});

// ---------------- Chat UI ----------------
function appendMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = `message ${sender}`;
    msg.innerText = text;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msg;
}

// ---------------- Ask question (Streaming SSE) ----------------
askBtn.addEventListener("click", () => {
    const video_url = videoInput.value.trim();
    const question = questionInput.value.trim();

    if (!videoLoaded) {
        alert("⚠️ Load a video first");
        return;
    }
    if (!question) {
        alert("⚠️ Enter a question");
        return;
    }

    appendMessage(question, "user");
    questionInput.value = "";

    const botMsg = appendMessage("🤖 ", "bot");

    const streamUrl = `/stream?video_url=${encodeURIComponent(video_url)}&question=${encodeURIComponent(question)}`;
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
        botMsg.innerText += "\n❌ Error while streaming";
        eventSource.close();
    };
});
