const askBtn = document.getElementById("askBtn");
const videoInput = document.getElementById("videoUrl");
const questionInput = document.getElementById("question");
const answerDiv = document.getElementById("answer");

askBtn.addEventListener("click", async () => {
    const video_url = videoInput.value;
    const question = questionInput.value;

    if (!video_url || !question) {
        alert("Please enter both video URL and question!");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_url, question })
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const data = await response.json();
        answerDiv.innerText = data.answer;
    } catch (err) {
        answerDiv.innerText = "Failed to get answer: " + err.message;
    }
});
