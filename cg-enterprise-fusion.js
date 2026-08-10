/* ClearGlassInc enterprise fusion controller.
   Progressive enhancement only. No backend, analytics, auth, form, or route contracts are changed. */
(function(){
  "use strict";
  if(window.__cgEnterpriseFusion)return;
  window.__cgEnterpriseFusion=true;

  var root=document.documentElement;
  root.setAttribute("data-cg-enterprise","true");

  var siteIndex=[
    {title:"ClearGlass Inc.",url:"/",summary:"Governed AI, cybersecurity, digital governance, operational intelligence, and strategic technology systems.",terms:"home company governed ai cyber strategy digital trust enterprise"},
    {title:"AI Automation Architecture",url:"#services",summary:"Governed agent workflows, evaluations, tool boundaries, human approval gates, and production deployment strategy.",terms:"ai automation agents workflows orchestration evals human gates"},
    {title:"Cybersecurity & Risk",url:"#services",summary:"Security architecture, exposure reduction, control assurance, incident readiness, and executive risk clarity.",terms:"cybersecurity security risk zero trust incident readiness assessment"},
    {title:"Artemis",url:"/artemis.html",summary:"ClearGlass governed AI and operational-intelligence ecosystem.",terms:"artemis ai automation intelligence operating system agents"},
    {title:"BlueDesk",url:"/bluedesk.html",summary:"CISO risk and blue-team operating surface.",terms:"bluedesk blue team ciso security cyber risk"},
    {title:"Flowsint",url:"/flowsint.html",summary:"OSINT investigation and intelligence-graph capability.",terms:"osint investigations intelligence research graph provenance"},
    {title:"Government Solutions",url:"/government.html",summary:"Public-sector strategy, governance, procurement, security, and operational systems.",terms:"government public sector digital governance procurement compliance"},
    {title:"Procurement Legal Tech",url:"/procurement-legal-tech.html",summary:"Public-sector legal operations and procurement workflow systems.",terms:"legal tech procurement legal operations compliance"},
    {title:"Web Design & Development",url:"/web-design.html",summary:"Accessible, secure, high-performance digital systems and application experiences.",terms:"website web application portal performance accessibility development"},
    {title:"Strategic Brief",url:"#contact",summary:"Start a scoped conversation with ClearGlass about a strategic technology, cyber, governance, or automation requirement.",terms:"contact strategic brief consultation assessment project"},
    {title:"Services & Engagements",url:"/offers/index.html",summary:"Published ClearGlass services and engagement pathways.",terms:"services offers engagements advisory consulting"},
    {title:"Pricing",url:"/pricing.html",summary:"Published pricing and payment-method information where available.",terms:"pricing price cost budget payment"},
    {title:"ClearGlass Intelligence",url:"/blog/",summary:"Field notes and essays on governed AI, cyber defense, OSINT, automation, and digital strategy.",terms:"blog insights articles research cyber ai osint"},
    {title:"ClearGlass NEXUS",url:"/clearglass-nexus.html",summary:"ClearGlass command-platform experience.",terms:"nexus command platform operations intelligence"},
    {title:"ClearPulse",url:"/clearpulse.html",summary:"Signal and healthcare-intelligence capability within the ClearGlass ecosystem.",terms:"clearpulse signal healthcare intelligence"}
  ];

  function createEl(tag,className,text){
    var el=document.createElement(tag);
    if(className)el.className=className;
    if(text!=null)el.textContent=text;
    return el;
  }

  function isTypingTarget(target){
    if(!target)return false;
    var tag=(target.tagName||"").toLowerCase();
    return tag==="input"||tag==="textarea"||tag==="select"||target.isContentEditable;
  }

  function resolveSiteHref(href){
    if(!href)return "/";
    if(href.charAt(0)==="#"){
      try{if(document.querySelector(href))return href;}catch(error){}
      return "/"+href;
    }
    return href;
  }

  /* ---------- Existing desktop products menu: capability layer + keyboard traversal ---------- */
  function enhanceDesktopMenu(){
    var dropdown=document.getElementById("navDropdown");
    var button=document.getElementById("dropBtn");
    if(!dropdown||!button||dropdown.querySelector(".cg-capability-quick"))return;

    button.setAttribute("aria-label","Products and capabilities");
    dropdown.setAttribute("aria-label","Products and ClearGlass capability navigation");

    var group=createEl("div","cg-capability-quick");
    group.setAttribute("role","group");
    group.setAttribute("aria-label","Capability index");
    var capabilities=[
      ["Governed AI","Agent systems","#services"],
      ["Cybersecurity","Risk + readiness","/bluedesk.html"],
      ["Digital Governance","Public-sector systems","/government.html"],
      ["OSINT","Investigation workflows","/flowsint.html"],
      ["Strategic Brief","Human scoping","#contact"]
    ];
    capabilities.forEach(function(item){
      var link=createEl("a","");
      link.href=resolveSiteHref(item[2]);
      link.setAttribute("role","menuitem");
      var strong=createEl("strong","",item[0]);
      var small=createEl("small","",item[1]);
      link.append(strong,small);
      group.appendChild(link);
    });
    dropdown.insertBefore(group,dropdown.firstChild);

    dropdown.addEventListener("keydown",function(event){
      var items=Array.prototype.slice.call(dropdown.querySelectorAll('[role="menuitem"]')).filter(function(item){return !item.hidden&&item.offsetParent!==null;});
      if(!items.length)return;
      var index=items.indexOf(document.activeElement);
      if(event.key==="ArrowDown"){
        event.preventDefault();
        items[(index+1+items.length)%items.length].focus();
      }else if(event.key==="ArrowUp"){
        event.preventDefault();
        items[(index-1+items.length)%items.length].focus();
      }else if(event.key==="Home"){
        event.preventDefault();items[0].focus();
      }else if(event.key==="End"){
        event.preventDefault();items[items.length-1].focus();
      }else if(event.key==="Escape"){
        event.preventDefault();button.focus();
      }
    });
  }

  /* ---------- Search overlay: static site-content index, explicitly not a live/AI search ---------- */
  var searchState={overlay:null,input:null,results:null,status:null,trigger:null,previousFocus:null};

  function renderSearch(query){
    if(!searchState.results||!searchState.status)return;
    searchState.results.replaceChildren(searchState.status);
    var normalized=String(query||"").trim().toLowerCase();
    var tokens=normalized.split(/\s+/).filter(Boolean);
    var results=siteIndex.map(function(item){
      var haystack=(item.title+" "+item.summary+" "+item.terms).toLowerCase();
      var score=tokens.reduce(function(total,token){
        if(item.title.toLowerCase().indexOf(token)!==-1)total+=4;
        if(item.terms.indexOf(token)!==-1)total+=3;
        if(haystack.indexOf(token)!==-1)total+=1;
        return total;
      },0);
      return {item:item,score:score};
    }).filter(function(row){return !tokens.length||row.score>0;}).sort(function(a,b){return b.score-a.score||a.item.title.localeCompare(b.item.title);}).slice(0,8);

    searchState.status.textContent=tokens.length?(results.length+" matching site result"+(results.length===1?"":"s")):"Suggested ClearGlass destinations";
    if(!results.length){
      var empty=createEl("p","cg-search-status","No matching page is in this local site-content index. Try AI automation, cybersecurity, governance, OSINT, pricing, or contact.");
      searchState.results.appendChild(empty);
      return;
    }
    results.forEach(function(row){
      var link=createEl("a","cg-search-result");
      link.href=resolveSiteHref(row.item.url);
      var wrap=createEl("div","");
      var title=createEl("strong","",row.item.title);
      var desc=createEl("p","",row.item.summary);
      var arrow=createEl("span","","→");
      arrow.setAttribute("aria-hidden","true");
      wrap.append(title,desc);
      link.append(wrap,arrow);
      searchState.results.appendChild(link);
    });
  }

  function closeSearch(){
    var overlay=searchState.overlay;
    if(!overlay||overlay.hidden)return;
    overlay.hidden=true;
    document.body.classList.remove("cg-search-open");
    if(searchState.trigger)searchState.trigger.setAttribute("aria-expanded","false");
    if(searchState.previousFocus&&typeof searchState.previousFocus.focus==="function")searchState.previousFocus.focus();
  }

  function openSearch(prefill){
    var overlay=searchState.overlay;
    if(!overlay)return;
    if(typeof window.closeMob==="function")window.closeMob();
    searchState.previousFocus=document.activeElement;
    overlay.hidden=false;
    document.body.classList.add("cg-search-open");
    if(searchState.trigger)searchState.trigger.setAttribute("aria-expanded","true");
    if(typeof prefill==="string")searchState.input.value=prefill;
    renderSearch(searchState.input.value);
    window.setTimeout(function(){searchState.input.focus();searchState.input.select();},0);
  }

  function buildSearch(){
    if(document.getElementById("cgSiteSearch"))return;
    var nav=document.getElementById("navbar");
    if(!nav)return;

    var trigger=createEl("button","cg-enterprise-search-trigger");
    trigger.type="button";
    trigger.id="cgSearchTrigger";
    trigger.setAttribute("aria-label","Search ClearGlass site content");
    trigger.setAttribute("aria-haspopup","dialog");
    trigger.setAttribute("aria-expanded","false");
    trigger.setAttribute("aria-controls","cgSiteSearch");
    trigger.setAttribute("aria-keyshortcuts","/");
    var triggerIcon=document.createElementNS("http://www.w3.org/2000/svg","svg");
    triggerIcon.setAttribute("viewBox","0 0 24 24");
    triggerIcon.setAttribute("aria-hidden","true");
    var triggerCircle=document.createElementNS("http://www.w3.org/2000/svg","circle");
    triggerCircle.setAttribute("cx","11");triggerCircle.setAttribute("cy","11");triggerCircle.setAttribute("r","6.5");
    var triggerLine=document.createElementNS("http://www.w3.org/2000/svg","path");
    triggerLine.setAttribute("d","m16 16 4 4");
    triggerIcon.append(triggerCircle,triggerLine);
    trigger.appendChild(triggerIcon);
    trigger.appendChild(createEl("span","cg-search-label","Search"));
    var navToggle=document.getElementById("navToggle");
    nav.insertBefore(trigger,navToggle||null);

    var overlay=createEl("div","cg-search-overlay");
    overlay.id="cgSiteSearch";
    overlay.hidden=true;
    overlay.setAttribute("role","dialog");
    overlay.setAttribute("aria-modal","true");
    overlay.setAttribute("aria-labelledby","cgSearchTitle");
    overlay.setAttribute("data-cg-site-search","local-index");

    var panel=createEl("section","cg-search-panel");
    var head=createEl("header","cg-search-head");
    var headingWrap=createEl("div","");
    headingWrap.append(createEl("small","","Site-content search"));
    var heading=createEl("strong","","Find a ClearGlass capability");
    heading.id="cgSearchTitle";
    headingWrap.appendChild(heading);
    var close=createEl("button","cg-search-close","×");
    close.type="button";
    close.setAttribute("aria-label","Close search");
    head.append(headingWrap,close);

    var form=createEl("div","cg-search-form");
    var label=createEl("label","","Search published ClearGlass pages");
    label.htmlFor="cgSearchInput";
    var inputWrap=createEl("div","cg-search-input-wrap");
    var icon=document.createElementNS("http://www.w3.org/2000/svg","svg");
    icon.setAttribute("viewBox","0 0 24 24");icon.setAttribute("aria-hidden","true");
    var circle=document.createElementNS("http://www.w3.org/2000/svg","circle");circle.setAttribute("cx","11");circle.setAttribute("cy","11");circle.setAttribute("r","6.5");
    var line=document.createElementNS("http://www.w3.org/2000/svg","path");line.setAttribute("d","m16 16 4 4");
    icon.append(circle,line);
    var input=createEl("input","cg-search-input");
    input.id="cgSearchInput";
    input.type="search";
    input.autocomplete="off";
    input.spellcheck=false;
    input.placeholder="AI automation, cybersecurity, governance, OSINT…";
    inputWrap.append(icon,input);
    var suggestions=createEl("div","cg-search-suggestions");
    suggestions.setAttribute("aria-label","Suggested searches");
    ["AI automation","Cybersecurity","Digital governance","OSINT","Pricing","Strategic brief"].forEach(function(text){
      var button=createEl("button","",text);button.type="button";
      button.addEventListener("click",function(){input.value=text;renderSearch(text);input.focus();});
      suggestions.appendChild(button);
    });
    form.append(label,inputWrap,suggestions);

    var results=createEl("div","cg-search-results");
    results.setAttribute("aria-label","Search results");
    var status=createEl("div","cg-search-status","");
    status.setAttribute("role","status");
    status.setAttribute("aria-live","polite");
    results.appendChild(status);
    var foot=createEl("div","cg-search-foot","Search is a local, editable index of published site destinations. It does not claim live indexing, enterprise search, or AI retrieval.");

    panel.append(head,form,results,foot);
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    searchState={overlay:overlay,input:input,results:results,status:status,trigger:trigger,previousFocus:null};
    renderSearch("");

    trigger.addEventListener("click",function(){openSearch("");});
    close.addEventListener("click",closeSearch);
    overlay.addEventListener("mousedown",function(event){if(event.target===overlay)closeSearch();});
    input.addEventListener("input",function(){renderSearch(input.value);});
    results.addEventListener("click",function(event){var link=event.target.closest&&event.target.closest("a");if(link)closeSearch();});

    overlay.addEventListener("keydown",function(event){
      if(event.key==="Escape"){event.preventDefault();closeSearch();return;}
      if(event.key!=="Tab")return;
      var focusable=Array.prototype.slice.call(overlay.querySelectorAll('button,a[href],input,[tabindex]:not([tabindex="-1"])')).filter(function(el){return !el.disabled&&el.offsetParent!==null;});
      if(!focusable.length)return;
      var first=focusable[0],last=focusable[focusable.length-1];
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
    });

    document.addEventListener("keydown",function(event){
      if(event.key==="/"&&!event.ctrlKey&&!event.metaKey&&!event.altKey&&!isTypingTarget(event.target)&&overlay.hidden){event.preventDefault();openSearch("");}
    });

    var mobileMenu=document.getElementById("mobileMenu");
    if(mobileMenu&&!mobileMenu.querySelector(".cg-mobile-search-action")){
      var mobileSearch=createEl("button","cg-mobile-search-action");
      mobileSearch.type="button";
      mobileSearch.append(createEl("span","","Search ClearGlass"),createEl("span","","⌕"));
      mobileSearch.addEventListener("click",function(){openSearch("");});
      var insertAfter=mobileMenu.querySelectorAll("a")[1];
      if(insertAfter&&insertAfter.nextSibling)mobileMenu.insertBefore(mobileSearch,insertAfter.nextSibling);else mobileMenu.insertBefore(mobileSearch,mobileMenu.firstChild);
    }
  }

  /* ---------- Existing mobile menu: modal-quality focus/scroll behavior without replacing its controller ---------- */
  function enhanceMobileMenu(){
    var menu=document.getElementById("mobileMenu");
    var toggle=document.getElementById("navToggle");
    if(!menu||!toggle)return;

    var backdrop=createEl("div","cg-mobile-backdrop");
    backdrop.setAttribute("aria-hidden","true");
    document.body.appendChild(backdrop);
    var backgroundState=[];

    function setBackgroundInert(active){
      if(active){
        if(backgroundState.length)return;
        Array.prototype.forEach.call(document.body.children,function(el){
          if(el===menu||el===backdrop||el.id==="navbar"||el.tagName==="SCRIPT"||el.tagName==="STYLE")return;
          backgroundState.push({el:el,hadInert:el.hasAttribute("inert")});
          el.setAttribute("inert","");
        });
      }else{
        backgroundState.forEach(function(record){if(!record.hadInert)record.el.removeAttribute("inert");});
        backgroundState=[];
      }
    }

    function sync(){
      var open=menu.classList.contains("open");
      document.body.toggleAttribute("data-cg-mobile-modal",open);
      setBackgroundInert(open);
    }
    var observer=new MutationObserver(sync);
    observer.observe(menu,{attributes:true,attributeFilter:["class"]});
    sync();

    backdrop.addEventListener("click",function(){
      if(typeof window.closeMob==="function")window.closeMob();
      else toggle.click();
    });

    menu.addEventListener("keydown",function(event){
      if(event.key!=="Tab"||!menu.classList.contains("open"))return;
      var focusable=Array.prototype.slice.call(menu.querySelectorAll('a[href],button:not([disabled]),[tabindex]:not([tabindex="-1"])')).filter(function(el){return el.offsetParent!==null;});
      if(!focusable.length)return;
      var first=focusable[0],last=focusable[focusable.length-1];
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
    });
  }

  /* ---------- Executive trust/governance layer ---------- */
  function buildTrustLayer(){
    if(document.getElementById("cg-trust-governance"))return;
    var doctrine=document.getElementById("doctrine");
    if(!doctrine)return;

    var section=createEl("section","cg-enterprise-trust");
    section.id="cg-trust-governance";
    section.setAttribute("aria-labelledby","cgTrustTitle");
    var shell=createEl("div","cg-enterprise-shell");
    shell.appendChild(createEl("div","cg-enterprise-eyebrow","Trust & governance methodology"));
    var title=createEl("h2","","Control before scale. Evidence before claims.");
    title.id="cgTrustTitle";
    shell.appendChild(title);
    shell.appendChild(createEl("p","cg-enterprise-intro","ClearGlass structures technology work around explicit ownership, bounded execution, privacy-aware handling, reviewable evidence, and human authority for consequential decisions. These are operating principles, not certification claims."));
    var grid=createEl("div","cg-trust-grid");
    var cards=[
      ["01","Security by Design","Security requirements are treated as architecture inputs, not a final-stage cosmetic check."],
      ["02","Human Oversight","Consequential automation is designed around named decision owners, approval boundaries, and escalation paths."],
      ["03","Least Privilege","Tools, identities, data access, and workflow permissions are constrained to the smallest practical operating scope."],
      ["04","Auditability","Important actions should be attributable, reviewable, and supported by evidence appropriate to the system and engagement."],
      ["05","Privacy-Aware Operations","Data collection and handling should remain proportionate to the service being delivered and its documented purpose."],
      ["06","Controlled Automation","Automation is introduced with explicit boundaries, safe failure behavior, and rollback considerations."],
      ["07","Reversible Execution","Where practical, changes are structured so operators can stop, inspect, recover, or reverse them without hidden state."],
      ["08","Operational Clarity","Interfaces and procedures should make system state, responsibility, uncertainty, and next actions understandable."]
    ];
    cards.forEach(function(item){
      var card=createEl("article","cg-trust-card");
      card.append(createEl("span","",item[0]),createEl("h3","",item[1]),createEl("p","",item[2]));
      grid.appendChild(card);
    });
    shell.appendChild(grid);
    section.appendChild(shell);
    doctrine.insertAdjacentElement("afterend",section);
  }

  /* ---------- Illustrative portal preview: no real client data or live-state claim ---------- */
  function buildPortalPreview(){
    if(document.getElementById("cg-portal-preview"))return;
    var main=document.getElementById("main-content")||document.querySelector("main");
    if(!main)return;
    var contact=document.getElementById("contact");

    var section=createEl("section","cg-portal-preview");
    section.id="cg-portal-preview";
    section.setAttribute("aria-labelledby","cgPortalTitle");
    var shell=createEl("div","cg-enterprise-shell");
    shell.appendChild(createEl("div","cg-enterprise-eyebrow","Client operations concept"));
    var title=createEl("h2","","A client view designed around decisions, controls, and evidence.");
    title.id="cgPortalTitle";
    shell.appendChild(title);
    shell.appendChild(createEl("p","cg-enterprise-intro","This is an illustrative portal view only. It contains no client records, credentials, production identifiers, private infrastructure data, or verified live integration."));
    shell.appendChild(createEl("span","cg-demo-badge","Illustrative portal view · Demo only"));
    var grid=createEl("div","cg-portal-grid");
    var modules=[
      ["MISSION STATUS","Example workflow","Demonstrates how scoped work could be presented without implying a live mission feed."],
      ["RISK POSTURE","Demonstration only","Shows a possible decision surface; no real organization or risk score is represented."],
      ["OPEN ACTIONS","Sample queue","Illustrates owner, review, and next-action visibility without exposing operational tasks."],
      ["AUDIT EVENTS","Sample trail","Represents the concept of reviewable evidence rather than a connected production ledger."],
      ["GOVERNANCE CONTROLS","Example controls","Shows where approvals and policy boundaries could be surfaced to authorized users."],
      ["SYSTEM HEALTH","No live telemetry","The website does not claim an authenticated monitoring or infrastructure connection."],
      ["STRATEGIC BRIEF","Illustrative record","Demonstrates structured advisory context without using customer information."],
      ["COMMUNICATIONS","Human-governed","Represents an authorized communication area; no messaging backend is implied."]
    ];
    modules.forEach(function(item){
      var card=createEl("article","cg-portal-card");
      card.append(createEl("small","",item[0]),createEl("strong","",item[1]),createEl("p","",item[2]));
      grid.appendChild(card);
    });
    shell.appendChild(grid);
    var actions=createEl("div","cg-portal-actions");
    var brief=createEl("a","","Request Strategic Brief →");brief.href=resolveSiteHref("#contact");
    var capabilities=createEl("a","","View Capabilities");capabilities.href=resolveSiteHref("#services");
    actions.append(brief,capabilities);
    shell.appendChild(actions);
    section.appendChild(shell);
    if(contact&&contact.parentNode)contact.parentNode.insertBefore(section,contact);else main.appendChild(section);
  }

  /* ---------- Capability cards: additive links only ---------- */
  function enhanceCapabilityCards(){
    var cards=document.querySelectorAll("#services .tech-card");
    var destinations=["/artemis.html","/bluedesk.html","/procurement-legal-tech.html"];
    Array.prototype.forEach.call(cards,function(card,index){
      if(card.querySelector(".cg-capability-link")||!destinations[index])return;
      var link=createEl("a","btn btn-glass cg-capability-link","Explore capability →");
      link.href=destinations[index];
      link.style.marginTop="18px";
      card.appendChild(link);
    });
  }

  /* ---------- Active navigation semantics ---------- */
  function syncActiveNavigation(){
    var links=document.querySelectorAll("#navLinks a");
    Array.prototype.forEach.call(links,function(link){
      if(link.classList.contains("is-active"))link.setAttribute("aria-current","location");
      else if(link.getAttribute("aria-current")==="location")link.removeAttribute("aria-current");
    });
  }
  function watchActiveNavigation(){
    var nav=document.getElementById("navLinks");
    if(!nav)return;
    syncActiveNavigation();
    new MutationObserver(syncActiveNavigation).observe(nav,{subtree:true,attributes:true,attributeFilter:["class"]});
  }

  function init(){
    enhanceDesktopMenu();
    buildSearch();
    enhanceMobileMenu();
    buildTrustLayer();
    buildPortalPreview();
    enhanceCapabilityCards();
    watchActiveNavigation();
  }

  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});
  else init();
})();