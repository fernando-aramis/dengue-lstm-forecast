/*
 * a11y fix for Dash 4.5 dcc.Dropdown (WCAG 4.1.2 "aria-hidden-focus").
 *
 * Dash 4.5 renders each dropdown as:
 *   <button class="dash-dropdown" tabindex="-1" aria-haspopup="listbox" …>   <- real control, has all the ARIA, but NOT a tab stop
 *   <input  class="dash-dropdown-focus-target" tabindex="0" aria-hidden="true" readonly>  <- focus shim: a tab stop, but hidden from AT
 * axe flags the shim: a focusable element inside/own an aria-hidden subtree.
 *
 * Remediation (verified to keep keyboard operation working): make the shim
 * fully inert (tabindex=-1, keep aria-hidden) and promote the real <button>
 * to the keyboard tab stop (tabindex=0). The button already carries
 * aria-haspopup/aria-expanded/aria-labelledby and its own keydown handlers, so
 * Tab lands on it and Enter/Space/ArrowDown open the listbox as before — now
 * exposed to assistive tech. Dash re-renders these nodes on value changes, so a
 * MutationObserver re-applies the fix. Idempotent: it only writes an attribute
 * when the value actually differs, so it never triggers its own observer loop.
 */
(function () {
  "use strict";

  function setAttr(el, name, value) {
    if (el.getAttribute(name) !== value) el.setAttribute(name, value);
  }

  function fix() {
    try {
      // 1) real control becomes the tab stop
      var buttons = document.querySelectorAll("button.dash-dropdown");
      for (var i = 0; i < buttons.length; i++) {
        if (buttons[i].getAttribute("tabindex") === "-1") {
          setAttr(buttons[i], "tabindex", "0");
        }
      }
      // 2) focus shim becomes inert (stays aria-hidden, leaves the tab order)
      var shims = document.querySelectorAll("input.dash-dropdown-focus-target");
      for (var j = 0; j < shims.length; j++) {
        if (shims[j].getAttribute("tabindex") !== "-1") {
          setAttr(shims[j], "tabindex", "-1");
        }
      }
    } catch (e) {}
  }

  function start() {
    fix();
    if (!("MutationObserver" in window)) return;
    var scheduled = false;
    var obs = new MutationObserver(function () {
      if (scheduled) return;
      scheduled = true;
      // coalesce bursts of Dash re-renders into one pass on the next frame
      (window.requestAnimationFrame || window.setTimeout)(function () {
        scheduled = false;
        fix();
      });
    });
    try {
      obs.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["tabindex"]
      });
    } catch (e) {}
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
