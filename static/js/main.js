document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("user-input");
    const submitBtn = document.getElementById("submit-btn");
    const loading = document.getElementById("loading");
    const resultsContainer = document.getElementById("results-container");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = input.value.trim();
        if (!message) return;

        // UI state: loading
        loading.classList.remove("hidden");
        submitBtn.disabled = true;
        input.value = "";

        try {
            const res = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || "Server error");
            }

            const data = await res.json();
            renderResultBlock(data);
        } catch (err) {
            alert(`Execution failed: ${err.message}`);
        } finally {
            loading.classList.add("hidden");
            submitBtn.disabled = false;
        }
    });

    function renderResultBlock(data) {
        const block = document.createElement("div");
        block.className = "interaction-block";

        const header = `
            <div class="query-header">
                <span class="user-query">Q: "${escapeHtml(data.query)}"</span>
                <span class="round-tag">${data.round_name}</span>
            </div>
        `;

        const cards = data.results.map((res) => `
            <div class="response-card ${res.is_error ? 'error' : ''}">
                <span class="param-badge">${res.param_name} = ${res.param_value}</span>
                <div class="response-text">${escapeHtml(res.text)}</div>
            </div>
        `).join("");

        block.innerHTML = `${header}<div class="card-grid">${cards}</div>`;
        resultsContainer.prepend(block);
    }

    function escapeHtml(string) {
        return string
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});