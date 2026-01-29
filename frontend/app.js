// Ask question (STREAMING)
askBtn.addEventListener("click", () => {
    console.log("ASK CLICKED (STREAM)");

    const video_url = videoInput.value;
    const question = questionInput.value.trim();

    if (!video_url || !question) {
        alert("Enter video URL and question");
        return;
    }

    // Show user message
    appendMessage(question, "user");
    questionInput.value = "";

    // Create bot message container (empty for streaming)
    const botMsg = appendMessage("🤖 ", "bot");

    // Build stream URL
    const streamUrl = `/stream?video_url=${encodeURIComponent(video_url)}&question=${encodeURIComponent(question)}`;

    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
        if (event.data === "[DONE]") {
            eventSource.close();
            return;
        }

        // Append streamed token
        botMsg.innerText += event.data;
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    eventSource.onerror = (err) => {
        console.error("SSE error", err);
        botMsg.innerText += "\n\n❌ Stream error";
        eventSource.close();
    };
});
