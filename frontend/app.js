document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatBox = document.getElementById("chat-box");
    const zoneSelect = document.getElementById("zone-select");
    const localitySelect = document.getElementById("locality-select");
    const backendStatus = document.getElementById("backend-status");
    const clearHistoryBtn = document.getElementById("clear-history-btn");

    // Locality Map by Zone
    const ZONE_LOCALITIES = {
        "Central Eastern Suburbs": ["Kanjurmarg", "Bhandup", "Mulund", "Vikhroli", "Nahur"],
        "Central Mumbai": ["Dadar", "Kurla", "Ghatkopar", "Chembur", "Govandi", "Mankhurd", "Tilak Nagar"],
        "Western Mumbai": ["Andheri", "Borivali", "Kandivali", "Malad", "Goregaon", "Dahisar", "Mira Road", "Bhayandar"],
        "South & Harbour Mumbai": ["Bandra", "Worli", "Lower Parel", "Parel", "Wadala", "Sion", "Matunga", "Mahim"],
        "Thane District": ["Thane West", "Thane East", "Kalyan", "Dombivli", "Ulhasnagar", "Bhiwandi", "Ambernath", "Badlapur"],
        "Navi Mumbai": ["Vashi", "Kharghar", "Panvel", "Airoli", "Nerul", "Belapur", "Sanpada", "Ghansoli", "Kopar Khairane"]
    };

    // --- Dynamic Two-Level Select List Filter ---
    const updateLocalityOptions = () => {
        const selectedZone = zoneSelect.value;
        localitySelect.innerHTML = "";

        const defaultOpt = document.createElement("option");
        defaultOpt.value = "all";
        defaultOpt.innerText = "All Localities";
        localitySelect.appendChild(defaultOpt);

        if (selectedZone === "all") {
            localitySelect.disabled = true;
        } else {
            localitySelect.disabled = false;
            const localities = ZONE_LOCALITIES[selectedZone];
            localities.forEach(loc => {
                const opt = document.createElement("option");
                opt.value = loc.toLowerCase();
                opt.innerText = loc;
                localitySelect.appendChild(opt);
            });
        }
    };

    // Bind zone change events
    zoneSelect.addEventListener("change", updateLocalityOptions);

    // --- Local Storage Chat History Persistence ---
    const HISTORY_KEY = "mre_rag_chat_history";

    const saveMessageToHistory = (sender, content, sources = []) => {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        history.push({ sender, content, sources });
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    };

    const loadChatHistory = () => {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        if (history.length > 0) {
            chatBox.innerHTML = "";
            history.forEach(msg => {
                appendMessage(msg.sender, msg.content, msg.sources, false);
            });
        }
    };

    const clearChatHistory = () => {
        localStorage.removeItem(HISTORY_KEY);
        // Reset to original welcome message
        chatBox.innerHTML = `
            <div class="message assistant-message">
                <div class="message-avatar">
                    <i class="fa-solid fa-robot"></i>
                </div>
                <div class="message-content">
                    <p>Hello! I am Hunter, your AI assistant specialized in the Mumbai Metropolitan Region's real estate markets. I can provide details on connectivity, upcoming infrastructure projects (Metro, MTHL, Coastal Road), key residential builds, and pricing ranges across all major zones.</p>
                    <p>What can I help you research today?</p>
                    <div class="suggestions">
                        <button class="suggest-btn" data-query="What is the average 2BHK price in Kanjurmarg?">2BHK in Kanjurmarg</button>
                        <button class="suggest-btn" data-query="Tell me about the Coastal Road impact on South Mumbai.">Coastal Road in Worli</button>
                        <button class="suggest-btn" data-query="What is driving real estate growth in Navi Mumbai?">Navi Mumbai Growth</button>
                    </div>
                </div>
            </div>
        `;
        zoneSelect.value = "all";
        updateLocalityOptions();
    };

    clearHistoryBtn.addEventListener("click", clearChatHistory);

    // --- Message Rendering Helpers ---
    const scrollToBottom = () => {
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const escapeHtml = (text) => {
        const div = document.createElement("div");
        div.innerText = text;
        return div.innerHTML;
    };

    const formatResponse = (text) => {
        let formatted = escapeHtml(text);
        formatted = formatted.replace(/\n/g, "<br>");
        formatted = formatted.replace(/\*\*(.*?)\*\"/g, "<strong>$1</strong>");
        // Support bolding ending in * as well
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        formatted = formatted.replace(/(?:^|<br>)(?:-|\*)\s+(.*?)(?=<br>|$)/g, "<br>• $1");
        return formatted;
    };

    const appendMessage = (sender, content, sources = [], shouldSave = true) => {
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

        if (shouldSave) {
            saveMessageToHistory(sender, content, sources);
        }
    };

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

    const removeTypingIndicator = () => {
        const indicator = document.getElementById("typing-indicator");
        if (indicator) {
            indicator.remove();
        }
    };

    // --- API & Submit Handlers ---
    const handleChatSubmit = async (queryText) => {
        if (!queryText.trim()) return;

        // 1. Append User Message
        appendMessage("user", queryText);
        chatInput.value = "";

        // 2. Auto-select zone filter if zone name is explicitly mentioned in query
        const lowerQuery = queryText.toLowerCase();
        let foundZone = null;
        Object.keys(ZONE_LOCALITIES).forEach(zone => {
            if (lowerQuery.includes(zone.toLowerCase())) {
                foundZone = zone;
            }
        });
        if (foundZone) {
            zoneSelect.value = foundZone;
            updateLocalityOptions();
        }

        // 3. Show Loading Spinner
        showTypingIndicator();

        const selectedZone = zoneSelect.value;
        const selectedLocality = localitySelect.value;

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: queryText,
                    zone: selectedZone,
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

    // Form submission
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        handleChatSubmit(chatInput.value);
    });

    // Suggestions buttons click handler
    chatBox.addEventListener("click", (e) => {
        if (e.target.classList.contains("suggest-btn")) {
            const query = e.target.getAttribute("data-query");
            handleChatSubmit(query);
        }
    });

    // Ping server connection status
    const checkServerConnection = async () => {
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: "ping", zone: "all", locality: "all" })
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

    // Initialize state
    checkServerConnection();
    loadChatHistory();
});
