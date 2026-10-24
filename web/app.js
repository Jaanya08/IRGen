/**
 * IRGen — Clean, Student-Friendly Playground Client
 */

(function () {
  "use strict";

  // State
  const state = {
    examples: [],
    compilation: null,
    activeTab: "tac",
    tacMode: "optimized", // 'optimized', 'raw', 'compare'
  };

  // DOM Elements
  const el = {
    sourceEditor: document.getElementById("sourceEditor"),
    lineNumbers: document.getElementById("lineNumbers"),
    compileBtn: document.getElementById("compileBtn"),
    resetBtn: document.getElementById("resetBtn"),
    exampleSelect: document.getElementById("exampleSelect"),

    // Help & Formatting
    formatBtn: document.getElementById("formatBtn"),
    syntaxHelpBtn: document.getElementById("syntaxHelpBtn"),
    syntaxHelpDrawer: document.getElementById("syntaxHelpDrawer"),

    // Error Banner
    errorBanner: document.getElementById("errorBanner"),
    errorStage: document.getElementById("errorStage"),
    errorMessage: document.getElementById("errorMessage"),
    dismissErrorBtn: document.getElementById("dismissErrorBtn"),

    // Tabs & Actions
    tabButtons: document.querySelectorAll(".tab-item"),
    tabContents: document.querySelectorAll(".tab-content"),
    copyOutputBtn: document.getElementById("copyOutputBtn"),

    // TAC View
    tacModePills: document.querySelectorAll(".pill[data-tac-mode]"),
    tacStatsBadge: document.getElementById("tacStatsBadge"),
    tacSingleView: document.getElementById("tacSingleView"),
    tacCompareView: document.getElementById("tacCompareView"),
    tacDisplay: document.getElementById("tacDisplay"),
    tacRawDisplay: document.getElementById("tacRawDisplay"),
    tacOptDisplay: document.getElementById("tacOptDisplay"),

    // Output & Variables
    execSummaryText: document.getElementById("execSummaryText"),
    varsTableBody: document.getElementById("varsTableBody"),

    // Assembly
    asmDisplay: document.getElementById("asmDisplay"),

    // Optimizations
    optPassesContainer: document.getElementById("optPassesContainer"),

    // AST
    astDisplay: document.getElementById("astDisplay"),

    // Tokens
    tokensTableBody: document.getElementById("tokensTableBody"),
  };

  // ==========================================================================
  // Initialization
  // ==========================================================================

  function init() {
    bindEditorEvents();
    bindTabEvents();
    bindActionEvents();
    bindTacModeEvents();
    fetchExamples();
  }

  // ==========================================================================
  // Editor Events & Line Numbers
  // ==========================================================================

  function bindEditorEvents() {
    el.sourceEditor.addEventListener("input", updateLineNumbers);
    el.sourceEditor.addEventListener("scroll", () => {
      el.lineNumbers.scrollTop = el.sourceEditor.scrollTop;
    });

    el.sourceEditor.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        const start = el.sourceEditor.selectionStart;
        const end = el.sourceEditor.selectionEnd;
        el.sourceEditor.value =
          el.sourceEditor.value.substring(0, start) + "    " + el.sourceEditor.value.substring(end);
        el.sourceEditor.selectionStart = el.sourceEditor.selectionEnd = start + 4;
        updateLineNumbers();
      }

      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        compileCode();
      }
    });
  }

  function updateLineNumbers() {
    const lines = el.sourceEditor.value.split("\n").length;
    let text = "";
    for (let i = 1; i <= lines; i++) {
      text += i + "\n";
    }
    el.lineNumbers.textContent = text;
  }

  // ==========================================================================
  // Tab Navigation
  // ==========================================================================

  function bindTabEvents() {
    el.tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-tab");
        switchTab(tab);
      });
    });
  }

  function switchTab(tabId) {
    state.activeTab = tabId;

    el.tabButtons.forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
    });

    el.tabContents.forEach((content) => {
      content.classList.toggle("active", content.id === `tab-${tabId}`);
    });
  }

  // ==========================================================================
  // TAC Mode (Optimized vs Raw vs Compare)
  // ==========================================================================

  function bindTacModeEvents() {
    el.tacModePills.forEach((pill) => {
      pill.addEventListener("click", () => {
        el.tacModePills.forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        state.tacMode = pill.getAttribute("data-tac-mode");
        renderTacView();
      });
    });
  }

  function renderTacView() {
    if (!state.compilation) return;

    const data = state.compilation;
    const rawLines = data.tac || [];
    const optLines = data.optimized_tac || [];

    if (state.tacMode === "compare") {
      el.tacSingleView.style.display = "none";
      el.tacCompareView.style.display = "grid";
      el.tacRawDisplay.textContent = rawLines.join("\n") || "// Empty";
      el.tacOptDisplay.textContent = optLines.join("\n") || "// Empty";
    } else {
      el.tacSingleView.style.display = "flex";
      el.tacCompareView.style.display = "none";
      if (state.tacMode === "raw") {
        el.tacDisplay.textContent = rawLines.join("\n") || "// Empty";
      } else {
        el.tacDisplay.textContent = optLines.join("\n") || "// Empty";
      }
    }
  }

  // ==========================================================================
  // Actions
  // ==========================================================================

  function bindActionEvents() {
    el.compileBtn.addEventListener("click", () => compileCode());

    el.resetBtn.addEventListener("click", () => {
      el.sourceEditor.value = "";
      updateLineNumbers();
      hideError();
    });

    el.formatBtn.addEventListener("click", () => {
      const lines = el.sourceEditor.value.split("\n");
      let depth = 0;
      const formatted = lines.map((line) => {
        const trimmed = line.trim();
        if (!trimmed) return "";
        if (trimmed.startsWith("}")) depth = Math.max(0, depth - 1);
        const res = "    ".repeat(depth) + trimmed;
        if (trimmed.endsWith("{")) depth++;
        return res;
      });
      el.sourceEditor.value = formatted.join("\n");
      updateLineNumbers();
    });

    el.syntaxHelpBtn.addEventListener("click", () => {
      const isVisible = el.syntaxHelpDrawer.style.display !== "none";
      el.syntaxHelpDrawer.style.display = isVisible ? "none" : "block";
    });

    el.dismissErrorBtn.addEventListener("click", hideError);

    el.copyOutputBtn.addEventListener("click", () => {
      let text = "";
      if (state.activeTab === "tac") {
        text = state.tacMode === "raw"
          ? (state.compilation?.tac || []).join("\n")
          : (state.compilation?.optimized_tac || []).join("\n");
      } else if (state.activeTab === "asm") {
        text = (state.compilation?.assembly || []).join("\n");
      } else if (state.activeTab === "ast") {
        text = state.compilation?.ast_outline || "";
      } else if (state.activeTab === "output") {
        text = JSON.stringify(state.compilation?.execution?.variables || {}, null, 2);
      }
      if (text) {
        navigator.clipboard.writeText(text).then(() => {
          el.copyOutputBtn.textContent = "Copied!";
          setTimeout(() => {
            el.copyOutputBtn.textContent = "Copy";
          }, 1500);
        });
      }
    });
  }

  // ==========================================================================
  // Example Loader
  // ==========================================================================

  function fetchExamples() {
    fetch("/api/examples")
      .then((res) => res.json())
      .then((data) => {
        state.examples = data.examples || [];
        el.exampleSelect.innerHTML = "";

        state.examples.forEach((ex) => {
          const opt = document.createElement("option");
          opt.value = ex.id;
          opt.textContent = ex.title;
          el.exampleSelect.appendChild(opt);
        });

        el.exampleSelect.addEventListener("change", (e) => {
          const ex = state.examples.find((x) => x.id === e.target.value);
          if (ex) {
            el.sourceEditor.value = ex.code;
            updateLineNumbers();
            compileCode(ex.initial_env || {});
          }
        });

        // Load first example
        if (state.examples.length > 0) {
          el.sourceEditor.value = state.examples[0].code;
          updateLineNumbers();
          compileCode(state.examples[0].initial_env || {});
        }
      })
      .catch((err) => {
        console.error("Could not load examples:", err);
      });
  }

  // ==========================================================================
  // Compilation
  // ==========================================================================

  function compileCode(customEnv = null) {
    const code = el.sourceEditor.value;
    const env = customEnv || {};

    el.compileBtn.disabled = true;
    el.compileBtn.querySelector("span").textContent = "Running...";

    fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, env }),
    })
      .then((res) => res.json())
      .then((data) => {
        el.compileBtn.disabled = false;
        el.compileBtn.querySelector("span").textContent = "Run Code";

        if (!data.success) {
          showError(data.stage, data.error);
        } else {
          hideError();
          state.compilation = data;
          renderOutputs(data);
        }
      })
      .catch((err) => {
        el.compileBtn.disabled = false;
        el.compileBtn.querySelector("span").textContent = "Run Code";
        showError("Server Error", "Could not reach compiler backend: " + err.message);
      });
  }

  // ==========================================================================
  // Render Outputs
  // ==========================================================================

  function renderOutputs(data) {
    const stats = data.stats || {};
    const before = stats.tac_before || 0;
    const after = stats.tac_after || 0;
    const removed = stats.removed || 0;

    if (removed > 0) {
      el.tacStatsBadge.textContent = `${after} instructions (${removed} optimized)`;
    } else {
      el.tacStatsBadge.textContent = `${after} instructions`;
    }

    // 1. TAC View
    renderTacView();

    // 2. Output & Variables
    renderExecution(data.execution || {});

    // 3. Assembly
    el.asmDisplay.textContent = (data.assembly || []).join("\n") || "// No assembly generated";

    // 4. Optimizations
    renderOptimizations(data.optimization_log || []);

    // 5. AST
    el.astDisplay.textContent = data.ast_outline || "// No AST available";

    // 6. Tokens
    renderTokens(data.tokens || []);
  }

  function renderExecution(exec) {
    const tbody = el.varsTableBody;
    tbody.innerHTML = "";

    if (!exec.success) {
      el.execSummaryText.textContent = `Execution halted: ${exec.error || "Unknown error"}`;
      tbody.innerHTML = `<tr><td colspan="2" class="empty-row" style="color: var(--red);">${escapeHtml(exec.error || "")}</td></tr>`;
      return;
    }

    el.execSummaryText.textContent = "Program executed successfully.";
    const vars = exec.variables || {};
    const entries = Object.entries(vars);

    if (entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="2" class="empty-row">No variables assigned.</td></tr>`;
      return;
    }

    entries.forEach(([name, val]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong style="color: var(--primary); font-family: var(--font-mono);">${escapeHtml(name)}</strong></td>
        <td><code style="font-family: var(--font-mono); font-size: 14px; font-weight: 600;">${val}</code></td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderOptimizations(log) {
    const container = el.optPassesContainer;
    container.innerHTML = "";

    if (!log || log.length === 0) {
      container.innerHTML = `<div class="empty-state">No optimizations applied. The code is already optimal.</div>`;
      return;
    }

    const passNames = {
      constant_folding: "Constant Folding",
      algebraic_simplification: "Algebraic Simplification",
      propagation: "Constant & Copy Propagation",
      cse: "Common Subexpression Elimination",
      copy_fusion: "Copy Fusion",
      dead_temp_elimination: "Dead Temp Elimination",
    };

    log.forEach((entry, idx) => {
      const card = document.createElement("div");
      card.className = "opt-card";
      const title = passNames[entry.pass] || entry.pass;

      card.innerHTML = `
        <div class="opt-card-header">
          <span class="opt-card-title">${escapeHtml(title)}</span>
          <span class="opt-badge">Pass ${idx + 1}</span>
        </div>
        <div class="opt-card-body">
          <div style="color: var(--text-muted); font-size: 11px; margin-bottom: 2px;">Before:</div>
          <div>${escapeHtml(entry.before.join("\n"))}</div>
          <div style="color: var(--green); font-size: 11px; margin-top: 6px; margin-bottom: 2px;">After:</div>
          <div>${escapeHtml(entry.after.join("\n"))}</div>
        </div>
      `;
      container.appendChild(card);
    });
  }

  function renderTokens(tokens) {
    const tbody = el.tokensTableBody;
    tbody.innerHTML = "";

    if (!tokens || tokens.length === 0) {
      tbody.innerHTML = `<tr><td colspan="3" class="empty-row">No tokens found.</td></tr>`;
      return;
    }

    tokens.forEach((tok) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="color: var(--text-dim); font-family: var(--font-mono);">${tok.index}</td>
        <td><span style="font-family: var(--font-mono); font-weight: 600; font-size: 11px; background: var(--bg-subtle); padding: 2px 6px; border-radius: 4px;">${escapeHtml(tok.type)}</span></td>
        <td><code style="font-family: var(--font-mono); font-weight: 600;">${escapeHtml(String(tok.value))}</code></td>
      `;
      tbody.appendChild(tr);
    });
  }

  // ==========================================================================
  // Error Banner
  // ==========================================================================

  function showError(stage, msg) {
    el.errorBanner.style.display = "flex";
    el.errorStage.textContent = `${stage}:`;
    el.errorMessage.textContent = msg;
  }

  function hideError() {
    el.errorBanner.style.display = "none";
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  document.addEventListener("DOMContentLoaded", init);
})();
