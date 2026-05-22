document.addEventListener('DOMContentLoaded',function(){
  var cfg=window.ClearGlassConfig||{};
  var plan=cfg.subscriptionName||'ClearGlass Premium Access';
  var price=cfg.priceLabel||'$20/month';
  var provider=cfg.checkoutProvider||'Bitcoin checkout';
  var support=cfg.supportEmail||'support@clearglassinc.com';
  var checkoutUrl=cfg.checkoutUrl||'#';
  var manual=!!cfg.manualBitcoinEnabled;
  var manualAddress=cfg.manualBitcoinAddress||'';
  function all(s){return Array.prototype.slice.call(document.querySelectorAll(s));}
  function one(s){return document.querySelector(s);}
  function logEvent(name,data){console.info('[ClearGlass audit]',{event:name,data:data||{},time:new Date().toISOString(),page:location.pathname});}
  all('.js-plan-name').forEach(function(n){n.textContent=plan;});
  all('.js-price').forEach(function(n){n.textContent=price;});
  all('.js-provider').forEach(function(n){n.textContent=provider;});
  all('.js-year').forEach(function(n){n.textContent=String(new Date().getFullYear());});
  all('.js-support-email').forEach(function(n){n.textContent=support;if(n.tagName.toLowerCase()==='a')n.href='mailto:'+support;});
  all('.js-subscribe').forEach(function(btn){
    btn.addEventListener('click',function(){
      logEvent('checkout_click',{plan:plan,price:price,provider:provider});
      if(!checkoutUrl||checkoutUrl==='#'||checkoutUrl.indexOf('YOUR-BTCPAY-SERVER')!==-1){
        var modal=one('#checkoutUnavailable');
        if(modal&&typeof modal.showModal==='function')modal.showModal();
        else alert('Bitcoin checkout is being configured. Please contact support for payment instructions.');
        return;
      }
      var target=new URL(checkoutUrl,window.location.href);
      target.searchParams.set('plan','clearglass-premium-access');
      target.searchParams.set('price','20-monthly');
      target.searchParams.set('returnUrl',window.location.origin+'/success.html');
      window.location.href=target.toString();
    });
  });
  var fallback=one('#manualFallback');
  var addr=one('#manualBitcoinAddress');
  if(fallback&&addr){fallback.hidden=!manual;addr.textContent=String(manualAddress).replace(/[<>]/g,'');}
  all('.faq-question').forEach(function(button){
    button.addEventListener('click',function(){
      var expanded=button.getAttribute('aria-expanded')==='true';
      var answer=document.getElementById(button.getAttribute('aria-controls'));
      button.setAttribute('aria-expanded',String(!expanded));
      if(answer)answer.hidden=expanded;
    });
  });
  var toggle=one('.nav-toggle');
  var nav=one('#primaryNav');
  if(toggle&&nav){
    toggle.addEventListener('click',function(){
      var expanded=toggle.getAttribute('aria-expanded')==='true';
      toggle.setAttribute('aria-expanded',String(!expanded));
      nav.dataset.open=String(!expanded);
    });
  }
  if(one('#successPage')){
    var params=new URLSearchParams(window.location.search);
    var orderId=params.get('orderId')||params.get('invoiceId')||params.get('id')||'Pending provider confirmation';
    var orderNode=one('#orderReference');
    if(orderNode)orderNode.textContent=String(orderId).replace(/[<>]/g,'');
    logEvent('payment_success_page_view',{plan:plan,provider:provider,orderReference:orderId});
  }
  logEvent('page_view',{plan:plan});
});
