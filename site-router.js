document.addEventListener("DOMContentLoaded", () => {
    // ALL PAGES CONNECTED HERE
    const pages = [
        { name: "Home", file: "index.html" },
        { name: "Artemis", file: "artemis.html" },
        { name: "Artemis IV", file: "artemis-iv.html" },
        { name: "Attack Core", file: "attack-prompt-core.html" },
        { name: "Banking Advisor", file: "banking-law-advisor.html" },
        { name: "Guardian", file: "guardian.html" },
        { name: "Revenue Engine", file: "revenue-engine.html" }
    ];
    // CREATE NAVBAR
    const nav = document.createElement("nav");
    nav.style.position = "fixed";
    nav.style.top = "0";
    nav.style.left = "0";
    nav.style.width = "100%";
    nav.style.background = "#000";
    nav.style.padding = "15px";
    nav.style.zIndex = "9999";
    nav.style.display = "flex";
    nav.style.flexWrap = "wrap";
    nav.style.gap = "15px";
    nav.style.justifyContent = "center";
    nav.style.boxShadow = "0 2px 10px rgba(0,0,0,0.5)";
    pages.forEach(page => {
        const link = document.createElement("a");
        link.href = page.file;
        link.textContent = page.name;
        link.style.color = "#00ffcc";
        link.style.textDecoration = "none";
        link.style.fontWeight = "bold";
        link.style.fontFamily = "Arial";
        link.style.transition = "0.3s";
        link.addEventListener("mouseover", () => {
            link.style.color = "#ffffff";
        });
        link.addEventListener("mouseout", () => {
            link.style.color = "#00ffcc";
        });
        nav.appendChild(link);
    });
    document.body.prepend(nav);
    // BODY SPACING
    document.body.style.paddingTop = "80px";
});
