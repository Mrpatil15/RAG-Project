document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatBox = document.getElementById("chat-box");
    const localitySelect = document.getElementById("locality-select");
    const backendStatus = document.getElementById("backend-status");

    // Helper: Scroll chat to bottom
    const scrollToBottom = () => {
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    // Helper: Escape HTML to prevent injection
    const escapeHtml = (text) => {
        const div = document.createElement("div");
        div.innerText = text;
        return div.innerHTML;
    };

    // Format text with simple bolding and lists
    const formatResponse = (text) => {
        let formatted = escapeHtml(text);
        // Replace newlines with breaks
        formatted = formatted.replace(/\n/g, "<br>");
        // Bold formatting **text**
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        // Bullet formatting * text or - text
        formatted = formatted.replace(/(?:^|<br>)(?:-|\*)\s+(.*?)(?=<br>|$)/g, "<br>• $1");
        return formatted;
    };

    // Append a message to the chat window
    const appendMessage = (sender, content, sources = []) => {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", `${sender}-message`);

        const avatarIcon = sender === "assistant" ? "fa-robot" : "fa-user";
        
        let sourcesHtml = "";
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="sources-card">
                    <div class="sources-toggle" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'flex' : 'none'">
                        <i class="fa-solid fa-folder-open"></i> Sources cited (${sources.length}) <i class="fa-solid fa-chevron-down" style="font-size:10px"></i>
                    </div>
                    <div class="sources-list" style="display: none;">
                        ${sources.map(src => `<span class="source-item"><i class="fa-solid fa-file-lines"></i> ${escapeHtml(src)}</span>`).join("")}
                    </div>
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fa-solid ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <p>${sender === "assistant" ? formatResponse(content) : escapeHtml(content)}</p>
                ${sourcesHtml}
            </div>
        `;

        chatBox.appendChild(messageDiv);
        scrollToBottom();
    };

    // Display typing loading indicator
    const showTypingIndicator = () => {
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("message", "assistant-message", "typing-container");
        loadingDiv.id = "typing-indicator";
        loadingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        chatBox.appendChild(loadingDiv);
        scrollToBottom();
    };

    // Remove typing loading indicator
    const removeTypingIndicator = () => {
        const indicator = document.getElementById("typing-indicator");
        if (indicator) {
            indicator.remove();
        }
    };

    // Send chat request to API
    const handleChatSubmit = async (queryText) => {
        if (!queryText.trim()) return;

        // 1. Show user message
        appendMessage("user", queryText);
        chatInput.value = "";

        // 2. Show typing loading state
        showTypingIndicator();

        const selectedLocality = localitySelect.value;

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: queryText,
                    locality: selectedLocality
                })
            });

            removeTypingIndicator();

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Server error occurred");
            }

            const data = await response.json();
            appendMessage("assistant", data.answer, data.sources);

        } catch (error) {
            removeTypingIndicator();
            appendMessage("assistant", `⚠️ Error: ${error.message}. Please make sure server.py is running and database ingestion is complete.`);
            console.error("Fetch error:", error);
        }
    };

    // Handle Form Submit
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        handleChatSubmit(chatInput.value);
    });

    // Handle click on suggestions buttons
    chatBox.addEventListener("click", (e) => {
        if (e.target.classList.contains("suggest-btn")) {
            const query = e.target.getAttribute("data-query");
            handleChatSubmit(query);
        }
    });

    // Simple backend ping to verify connection
    const checkServerConnection = async () => {
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: "ping", locality: "all" })
            });
            if (res.ok) {
                backendStatus.innerText = "Connected to Local Engine";
                backendStatus.style.color = "#10b981";
            }
        } catch (e) {
            backendStatus.innerText = "Offline - Run server.py";
            backendStatus.style.color = "#f43f5e";
        }
    };

    // Check connection initially
    checkServerConnection();
});
