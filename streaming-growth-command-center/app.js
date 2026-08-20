const packages = {
  agents: {
    titles: [
      "I Built a Governed AI Agent Stack — Live Architecture Review",
      "AI Agents Under Pressure: How Leaders Prevent Silent Failure",
      "The Trust Boundary Most Agent Builders Miss",
      "From Prompt to Approval: A Live Agent Workflow",
      "7 Design Rules for Reliable Agents Without Runaway Autonomy"
    ],
    description: "Watch a live, evidence-led architecture review of governed AI agents for technical founders and engineering leaders. By the end, you will have a practical control-plane blueprint covering tool boundaries, human approval, evaluation, and rollback. Sources and diagrams will be linked after the briefing."
  },
  cyber: {
    titles: [
      "The Security Dashboard Says Green. The Evidence Says Otherwise.",
      "Zero Trust Under Pressure: A Live Architecture Review",
      "I Threat-Modeled an AI Platform — Here Is What Broke",
      "From Alert to Decision: A Live Cyber Defense Workflow",
      "5 Controls for AI Systems Without Security Theater"
    ],
    description: "Join a source-led cyber defense briefing for security architects, founders, and operators. We will map the trust boundaries, test the highest-impact failure paths, and produce a prioritized control plan—without fear-based claims or security theater."
  },
  osint: {
    titles: [
      "From Open Signal to Defensible Judgment — Live OSINT Workflow",
      "The Confidence Error Most OSINT Reports Hide",
      "I Built an Evidence-First OSINT Pipeline — Live Review",
      "OSINT Under Pressure: Corroboration Before Conclusion",
      "6 Rules for Faster Research Without Sacrificing Provenance"
    ],
    description: "Watch an ethical, evidence-first OSINT workflow built for analysts and decision-makers. We will move from collection to corroboration, confidence scoring, and a defensible intelligence product using public, authorized sources only."
  },
  executive: {
    titles: [
      "What Every COO Should Ask Before Approving an AI Agent",
      "From Technical Signal to Executive Decision — Live Briefing",
      "The AI Risk Most Leadership Teams Measure Too Late",
      "I Built an Executive Control Plane for AI Operations",
      "5 Architecture Decisions That Protect Speed and Accountability"
    ],
    description: "A technical executive briefing for founders, COOs, and architecture leaders translating AI system design into accountable decisions. Leave with a concise approval framework for value, risk, ownership, evidence, and rollback."
  }
};

const storageKey = "cg-signal-engine-progress-v1";
const protocols = [...document.querySelectorAll(".protocol")];
let completed = new Set(JSON.parse(localStorage.getItem(storageKey) || "[]"));

function updateProgress() {
  document.querySelector("#progressCount").textContent = `${completed.size}/6`;
  protocols.forEach((protocol) => {
    const done = completed.has(protocol.dataset.id);
    const state = protocol.querySelector(".protocol-state");
    state.textContent = done ? "COMPLETE" : "READY";
    state.style.color = done ? "var(--acid)" : "var(--green)";
  });
  localStorage.setItem(storageKey, JSON.stringify([...completed]));
}

protocols.forEach((protocol) => {
  const button = protocol.querySelector(".protocol-head");
  button.addEventListener("click", () => {
    const opening = !protocol.classList.contains("open");
    protocol.classList.toggle("open", opening);
    button.setAttribute("aria-expanded", String(opening));
    if (opening) completed.add(protocol.dataset.id);
    updateProgress();
  });
});

function renderPackage(topic) {
  const item = packages[topic];
  document.querySelector("#generatedTitle").textContent = item.titles[0];
  document.querySelector("#generatedDescription").textContent = item.description;
  document.querySelector("#titleList").innerHTML = item.titles.slice(1).map((title) => `<p>${title}</p>`).join("");
}

document.querySelectorAll(".topic").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".topic").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  renderPackage(button.dataset.topic);
}));

document.querySelector("#copyButton").addEventListener("click", async () => {
  const text = `${document.querySelector("#generatedTitle").textContent}\n\n${document.querySelector("#generatedDescription").textContent}`;
  const status = document.querySelector("#copyStatus");
  try {
    await navigator.clipboard.writeText(text);
    status.textContent = "Copied.";
  } catch {
    status.textContent = "Clipboard unavailable; select the text manually.";
  }
});

document.querySelector("#resetButton").addEventListener("click", () => {
  completed.clear();
  protocols.forEach((protocol, index) => {
    protocol.classList.toggle("open", index === 0);
    protocol.querySelector(".protocol-head").setAttribute("aria-expanded", String(index === 0));
  });
  updateProgress();
});

document.querySelector("#downloadButton").addEventListener("click", () => {
  const selected = document.querySelector(".topic.active").dataset.topic;
  const item = packages[selected];
  const runSheet = [
    "CLEARGLASSINC SIGNAL ENGINE — OPERATOR RUN SHEET",
    "",
    `Topic: ${selected}`,
    `Title: ${item.titles[0]}`,
    `Description: ${item.description}`,
    "",
    "D-3: Schedule canonical YouTube room; lock title, description, category, and thumbnail.",
    "D-2: Publish proof artifact; invite 10–20 high-fit peers personally.",
    "D-1: Publish contrarian question and source-led teaser.",
    "D0: Deliver outcome; mark clips; announce next briefing.",
    "D+1: Add chapters and sources; publish strongest short.",
    "D+3: Publish diagram clip and executive summary.",
    "D+5/7: Publish Q&A cut; inspect CTR, ACV, S→L, and returning qualified viewers.",
    "",
    `Protocols completed: ${completed.size}/6`
  ].join("\n");
  const url = URL.createObjectURL(new Blob([runSheet], { type: "text/plain;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "clearglassinc-signal-engine-run-sheet.txt";
  link.click();
  URL.revokeObjectURL(url);
});

renderPackage("agents");
updateProgress();
