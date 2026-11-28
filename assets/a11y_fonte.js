// Radiogroup "Fonte dos dados": setas movem foco+seleção (WAI-ARIA radio group); Espaço/Enter já
// ativam o botão. O botão "Atual" desabilitado (aria-disabled) é ignorado. Delegação: sobrevive ao
// rebuild do conteúdo ao trocar de idioma/fonte.
document.addEventListener('keydown', function (e) {
  var alvo = e.target && e.target.closest ? e.target.closest('.fonte-opt') : null;
  if (!alvo) { return; }
  var passo = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
  if (!passo) { return; }
  var opts = Array.prototype.slice.call(alvo.parentNode.querySelectorAll('.fonte-opt'))
    .filter(function (b) { return b.getAttribute('aria-disabled') !== 'true'; });
  var i = opts.indexOf(alvo);
  if (i < 0 || opts.length < 2) { return; }
  var prox = opts[(i + passo + opts.length) % opts.length];
  e.preventDefault();
  prox.focus();
  prox.click();
  // A troca de fonte reconstrói o conteúdo (o foco cairia no body): devolve o foco à opção marcada.
  [150, 500, 1200].forEach(function (ms) {
    setTimeout(function () {
      if (document.activeElement && document.activeElement.closest &&
          document.activeElement.closest('.fonte-opt')) { return; }
      var marcada = document.querySelector('.fonte-opt[aria-checked="true"]');
      if (marcada) { marcada.focus(); }
    }, ms);
  });
});
