(function(){
  'use strict';
  var statuses=['MISSION ACTIVE','SYSTEMS NOMINAL','SECURE LINK','INTELLIGENCE ONLINE'];
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var compact=window.matchMedia&&window.matchMedia('(max-width: 760px)').matches;
  function setPaused(){document.documentElement.classList.toggle('mission-core-paused',document.hidden);}
  document.addEventListener('visibilitychange',setPaused,{passive:true});
  setPaused();
  if(reduce||compact)return;
  function init(core){
    var text=core.querySelector('.mission-core__status-text');
    if(!text)return;
    var i=0;
    window.setInterval(function(){
      i=(i+1)%statuses.length;
      text.classList.add('is-fading');
      window.setTimeout(function(){text.textContent=statuses[i];text.classList.remove('is-fading');},280);
    },5000);
  }
  function boot(){Array.prototype.forEach.call(document.querySelectorAll('[data-mission-core]'),init);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
