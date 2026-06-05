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

    // --- 3D Scene Initialization (Three.js & GSAP) ---
    const clusters = {
        "Central Eastern Suburbs": { x: -8, z: 6, color: 0x3b82f6, name: "Central Eastern Suburbs", desc: "Active development along Eastern Express Highway. Premium high-rise towers in Bhandup & Mulund." },
        "Central Mumbai": { x: 0, z: 12, color: 0x8b5cf6, name: "Central Mumbai", desc: "Residential micro-markets and commercial hubs. Powdered by Powai and JVLR connectivity." },
        "Western Mumbai": { x: -14, z: -6, color: 0x06b6d4, name: "Western Mumbai", desc: "Vast residential expansion (Andheri to Borivali). Premium media hubs and Metro Line 2A/7." },
        "South & Harbour Mumbai": { x: 6, z: 18, color: 0x60a5fa, name: "South & Harbour Mumbai", desc: "Ultra-luxury residential markets. Coastal Road & MTHL bridge connectivity to central points." },
        "Thane District": { x: -4, z: -20, color: 0xd946ef, name: "Thane District", desc: "Self-sustaining townships, affordable housing, and excellent green coverage along Ghodbunder Road." },
        "Navi Mumbai": { x: 18, z: 4, color: 0x10b981, name: "Navi Mumbai", desc: "CIDCO planned nodes. Accelerated growth driven by the upcoming International Airport and MTHL." }
    };

    let threeSceneInstance = null;

    const init3DScene = () => {
        const container = document.getElementById("three-canvas-container");
        if (!container) return null;

        // Scene & Fog
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x070a13, 0.025);

        // Camera
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(0, 26, 32);
        camera.lookAt(0, 0, 0);

        // Renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);

        // Lights
        const ambientLight = new THREE.AmbientLight(0x0f172a, 2.0);
        scene.add(ambientLight);

        const dirLight1 = new THREE.DirectionalLight(0x3b82f6, 2.5);
        dirLight1.position.set(10, 25, 10);
        scene.add(dirLight1);

        const dirLight2 = new THREE.DirectionalLight(0x8b5cf6, 3.0);
        dirLight2.position.set(-10, 25, -10);
        scene.add(dirLight2);

        // Glowing Grid Floor
        const gridHelper = new THREE.GridHelper(60, 30, 0x3b82f6, 0x1e293b);
        gridHelper.position.y = -0.1;
        scene.add(gridHelper);

        const buildingGroups = {};

        // Generate clusters of procedural buildings
        Object.entries(clusters).forEach(([zoneName, target]) => {
            const group = new THREE.Group();
            group.position.set(target.x, 0, target.z);
            scene.add(group);
            buildingGroups[zoneName] = group;

            const numBuildings = 8 + Math.floor(Math.random() * 5);
            for (let i = 0; i < numBuildings; i++) {
                const width = 0.8 + Math.random() * 0.8;
                const height = 4 + Math.random() * 8;
                const depth = 0.8 + Math.random() * 0.8;

                const geometry = new THREE.BoxGeometry(width, height, depth);
                const material = new THREE.MeshPhongMaterial({
                    color: target.color,
                    emissive: target.color,
                    emissiveIntensity: 0.18,
                    shininess: 100,
                    specular: 0xffffff,
                    transparent: true,
                    opacity: 0.8
                });

                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.set(
                    (Math.random() - 0.5) * 4.5,
                    height / 2,
                    (Math.random() - 0.5) * 4.5
                );
                group.add(mesh);

                // Wireframe Edge Highlight
                const geoWire = new THREE.EdgesGeometry(geometry);
                const matWire = new THREE.LineBasicMaterial({ color: target.color, linewidth: 1 });
                const wireframe = new THREE.LineSegments(geoWire, matWire);
                mesh.add(wireframe);
            }
        });

        // Background Star Particles
        const starGeometry = new THREE.BufferGeometry();
        const starCount = 200;
        const starPositions = new Float32Array(starCount * 3);

        for (let i = 0; i < starCount * 3; i++) {
            starPositions[i] = (Math.random() - 0.5) * 80;
        }

        starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
        const starMaterial = new THREE.PointsMaterial({
            size: 0.08,
            color: 0xffffff,
            transparent: true,
            opacity: 0.4
        });
        const stars = new THREE.Points(starGeometry, starMaterial);
        scene.add(stars);

        let targetLookAt = new THREE.Vector3(0, 0, 0);
        let currentLookAt = new THREE.Vector3(0, 0, 0);

        const animate = () => {
            requestAnimationFrame(animate);
            
            // Slowly rotate stars background
            stars.rotation.y += 0.0004;

            // Smooth camera lookAt interpolation
            currentLookAt.lerp(targetLookAt, 0.06);
            camera.lookAt(currentLookAt);

            renderer.render(scene, camera);
        };

        animate();

        // Resize handler
        window.addEventListener("resize", () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });

        // Zoom Fly-To Transition
        const focusZone = (zoneName) => {
            const overlay = document.getElementById("market-overlay");

            if (zoneName === "all" || !clusters[zoneName]) {
                // Return to Bird's-Eye Overview
                gsap.to(camera.position, { x: 0, y: 26, z: 32, duration: 1.8, ease: "power2.inOut" });
                targetLookAt.set(0, 0, 0);

                // Reset building glows
                Object.keys(buildingGroups).forEach(name => {
                    buildingGroups[name].children.forEach(mesh => {
                        if (mesh.material) {
                            gsap.to(mesh.material, { emissiveIntensity: 0.18, duration: 0.6 });
                        }
                    });
                });

                if (overlay) overlay.style.display = "none";
            } else {
                const target = clusters[zoneName];
                // Pan and zoom camera to cluster coordinates
                gsap.to(camera.position, {
                    x: target.x + 8,
                    y: 11,
                    z: target.z + 9,
                    duration: 1.8,
                    ease: "power2.inOut"
                });
                targetLookAt.set(target.x, 2, target.z);

                // Focus glow highlights
                Object.keys(buildingGroups).forEach(name => {
                    const isSelected = name === zoneName;
                    buildingGroups[name].children.forEach(mesh => {
                        if (mesh.material) {
                            gsap.to(mesh.material, {
                                emissiveIntensity: isSelected ? 0.8 : 0.05,
                                duration: 0.6
                            });
                        }
                    });
                });

                // Display detail overlay
                if (overlay) {
                    overlay.style.display = "block";
                    overlay.innerHTML = `
                        <h4>${target.name}</h4>
                        <p>${target.desc}</p>
                    `;
                }
            }
        };

        return { focusZone };
    };

    // Initialize 3D Visualizer
    threeSceneInstance = init3DScene();

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
    zoneSelect.addEventListener("change", () => {
        updateLocalityOptions();
        if (threeSceneInstance) {
            threeSceneInstance.focusZone(zoneSelect.value);
        }
    });

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
                    <p>Hello! I am your AI assistant specialized in the Mumbai Metropolitan Region's real estate markets. I can provide details on connectivity, upcoming infrastructure projects (Metro, MTHL, Coastal Road), key residential builds, and pricing ranges across all major zones.</p>
                    <p>What can I help you research today?</p>
                    <div class="suggestions">
                        <button class="suggest-btn" data-query="What is the average 2BHK price in Kanjurmarg?">2BHK in Kanjurmarg</button>
                        <button class="suggest-btn" data-query="Tell me about the Coastal Road impact on South Mumbai.">Coastal Road in Worli</button>
                        <button class="suggest-btn" data-query="What is driving real estate growth in Navi Mumbai?">Navi Mumbai Growth</button>
                    </div>
                </div>
            </div>
        `;
        // Reset visualizer zoom
        zoneSelect.value = "all";
        updateLocalityOptions();
        if (threeSceneInstance) {
            threeSceneInstance.focusZone("all");
        }
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

        // 2. Fly camera automatically if zone is mentioned in chat
        const lowerQuery = queryText.toLowerCase();
        let foundZone = null;
        Object.keys(clusters).forEach(zone => {
            if (lowerQuery.includes(zone.toLowerCase())) {
                foundZone = zone;
            }
        });
        if (foundZone) {
            zoneSelect.value = foundZone;
            updateLocalityOptions();
            if (threeSceneInstance) {
                threeSceneInstance.focusZone(foundZone);
            }
        }

        // 3. Show Loading Spinner
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

    // Initialize state
    checkServerConnection();
    loadChatHistory();
});
