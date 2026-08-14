/* Minimal privacy-aware lead attribution for static forms.

   Only campaign fields and a random lead ID are persisted in sessionStorage.
   Names, email addresses, phone numbers, free-text concerns and form values are
   never copied into browser storage or analytics. */
(function () {
  "use strict";
  var ATTRIBUTION_KEY = "cg.attribution";
  var LEAD_KEY = "cg.lead.id";
  var ALLOWED = ["source", "medium", "campaign", "term", "content"];

  function read(key) {
    try { return sessionStorage.getItem(key); } catch (error) { return null; }
  }

  function write(key, value) {
    try { sessionStorage.setItem(key, value); } catch (error) { /* unavailable */ }
  }

  function leadId() {
    var current = read(LEAD_KEY);
    if (current) return current;
    var value = "lead-";
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      value += window.crypto.randomUUID();
    } else {
      value += Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
    }
    write(LEAD_KEY, value);
    return value;
  }

  function attribution() {
    var stored = read(ATTRIBUTION_KEY);
    if (stored) {
      try { return JSON.parse(stored); } catch (error) { /* rebuild */ }
    }
    var params = new URLSearchParams(location.search);
    var result = {};
    ALLOWED.forEach(function (key) {
      result[key] = String(params.get("utm_" + key) || "").slice(0, 100);
    });
    write(ATTRIBUTION_KEY, JSON.stringify(result));
    return result;
  }

  function hidden(form, name, value) {
    var input = form.querySelector('input[name="' + name + '"]');
    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }
    input.value = value;
  }

  document.querySelectorAll("[data-cg-lead-form]").forEach(function (form) {
    var campaign = attribution();
    hidden(form, "lead_id", leadId());
    hidden(form, "page_path", location.pathname);
    ALLOWED.forEach(function (key) { hidden(form, "utm_" + key, campaign[key] || ""); });
  });
})();
