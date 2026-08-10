/* ClearGlassInc enterprise compatibility shim.
   Additive fallback for homepage variants that no longer expose the historical #doctrine anchor. */
(function(){
  "use strict";
  if(document.getElementById("cg-trust-governance"))return;
  var anchor=document.getElementById("doctrine")||document.getElementById("vision");
  if(!anchor)return;

  function el(tag,className,text){
    var node=document.createElement(tag);
    if(className)node.className=className;
    if(text!=null)node.textContent=text;
    return node;
  }

  var section=el("section","cg-enterprise-trust");
  section.id="cg-trust-governance";
  section.setAttribute("aria-labelledby","cgTrustTitle");
  var shell=el("div","cg-enterprise-shell");
  shell.appendChild(el("div","cg-enterprise-eyebrow","Trust & governance methodology"));
  var title=el("h2","","Control before scale. Evidence before claims.");
  title.id="cgTrustTitle";
  shell.appendChild(title);
  shell.appendChild(el("p","cg-enterprise-intro","ClearGlass structures technology work around explicit ownership, bounded execution, privacy-aware handling, reviewable evidence, and human authority for consequential decisions. These are operating principles, not certification claims."));

  var grid=el("div","cg-trust-grid");
  [
    ["01","Security by Design","Security requirements are treated as architecture inputs, not a final-stage cosmetic check."],
    ["02","Human Oversight","Consequential automation is designed around named decision owners, approval boundaries, and escalation paths."],
    ["03","Least Privilege","Tools, identities, data access, and workflow permissions are constrained to the smallest practical operating scope."],
    ["04","Auditability","Important actions should be attributable, reviewable, and supported by evidence appropriate to the system and engagement."],
    ["05","Privacy-Aware Operations","Data collection and handling should remain proportionate to the service being delivered and its documented purpose."],
    ["06","Controlled Automation","Automation is introduced with explicit boundaries, safe failure behavior, and rollback considerations."],
    ["07","Reversible Execution","Where practical, changes are structured so operators can stop, inspect, recover, or reverse them without hidden state."],
    ["08","Operational Clarity","Interfaces and procedures should make system state, responsibility, uncertainty, and next actions understandable."]
  ].forEach(function(item){
    var card=el("article","cg-trust-card");
    card.append(el("span","",item[0]),el("h3","",item[1]),el("p","",item[2]));
    grid.appendChild(card);
  });
  shell.appendChild(grid);
  section.appendChild(shell);
  anchor.insertAdjacentElement("afterend",section);
})();