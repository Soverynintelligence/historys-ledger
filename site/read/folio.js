/* Folio behaviour: the scale, the page turn, the before/after readout.
   Shared by every entry. Generated pages differ only in content. */
(function(){
  var before = null, after = null;
  var quiet = window.matchMedia &&
              window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var leaves = 1;

  /* ── the scale ─────────────────────────────────────────────────────────── */
  function wire(host, onPick){
    if(!host) return;
    host.addEventListener('click', function(e){
      var b = e.target.closest('.opt');
      if(!b) return;
      Array.prototype.forEach.call(host.children, function(c){
        c.setAttribute('aria-pressed', 'false');
      });
      b.setAttribute('aria-pressed', 'true');
      onPick(+b.dataset.i);
    });
  }

  wire(document.getElementById('opts0'), function(i){
    before = i;
    var go = document.getElementById('go0');
    if(go) go.disabled = false;
    var hint = document.getElementById('hint0');
    if(hint) hint.textContent = 'Nothing is scored';
  });

  wire(document.getElementById('opts1'), function(i){
    after = i;
    var r = document.getElementById('readout');
    if(!r || before === null) return;
    r.hidden = false;
    document.getElementById('pipA').style.left = (before / 4 * 100) + '%';
    document.getElementById('pipB').style.left = (after / 4 * 100) + '%';
    var d = after - before, m = document.getElementById('moved');
    if(d === 0){
      m.textContent = 'You landed where you started. The record didn’t move ' +
                      'you — which is a result, not a failure.';
    } else {
      m.textContent = 'You moved ' + Math.abs(d) + ' ' +
        (Math.abs(d) === 1 ? 'step' : 'steps') + ' toward ' +
        (d > 0 ? 'the cost' : 'the achievement') + '. The documents did that, not us.';
    }
  });

  /* ── turning the page ──────────────────────────────────────────────────── */
  function foliate(){
    var el = document.getElementById('foliomark');
    if(!el) return;
    el.textContent = 'fol. ' + (Math.floor(leaves / 2) + 1) + ' · ' +
                     (leaves % 2 ? 'verso' : 'recto');
  }

  function turn(toId){
    var next = document.getElementById(toId);
    if(!next) return;

    next.hidden = false;
    leaves++; foliate();
    /* Instant, not smooth: a smooth scroll and a page turn are two motions
       competing to mean the same thing, and the turn loses — it plays while
       the viewport is still travelling. */
    next.scrollIntoView({behavior:'auto', block:'start'});

    /* No turn when the tab is not being looked at. A CSS animation attached to
       a hidden document does not wait — it STARTS and freezes at frame zero,
       pinning the from-state (rotated, opacity 0) until the tab comes back.
       fill-mode does not help: it governs before-start and after-end, and a
       frozen animation is neither. The reader would return to a blank page. */
    if(quiet || document.hidden) return;

    next.classList.add('turning-in');
    next.addEventListener('animationend', function h(){
      next.removeEventListener('animationend', h);
      next.classList.remove('turning-in');
    });
  }

  /* If the tab is hidden PART WAY through a turn the animation freezes where it
     got to. Strip it, and the sheet falls back to its resting style: upright
     and readable. Motion never gates content. */
  document.addEventListener('visibilitychange', function(){
    if(!document.hidden) return;
    document.querySelectorAll('.leaf.turning-in').forEach(function(el){
      el.classList.remove('turning-in');
    });
  });

  var go0 = document.getElementById('go0');
  if(go0) go0.addEventListener('click', function(){
    var first = document.querySelector('.stage[hidden]');
    if(first) turn(first.id);
  });

  document.querySelectorAll('[data-next]').forEach(function(b){
    b.addEventListener('click', function(){ turn(b.dataset.next); });
  });
})();
