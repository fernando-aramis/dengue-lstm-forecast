/*
 * a11y: react-select (dcc.Dropdown) renders a focusable <input> inside a
 * container marked aria-hidden="true". axe-core flags this as
 * "aria-hidden-focus" (WCAG 4.1.2): focusable content must not sit inside an
 * aria-hidden subtree. Dash 4.5.0 still bundles the affected react-select, so
 * we neutralise it from the client: any focusable element inside an
 * aria-hidden="true" node (scoped to the dropdowns) is made non-focusable
 * (tabindex=-1, and disabled for form inputs). We never touch the visible
 * combobox input, which is not inside an aria-hidden subtree.
 */
(function () {
  "use strict";

  var SCOPE = ".dash-dropdown, .Select";
  var FOCUSABLE =
    'a[href], button, input, select, textarea, [tabindex]';

  function fix(root) {
    if (!root || typeof root.querySelectorAll !== "function") return;
    var hidden = root.querySelectorAll('[aria-hidden="true"]');
    for (var i = 0; i < hidden.length; i++) {
      var container = hidden[i];
      // only care about hidden containers that live in a dropdown
      if (!container.closest || !container.closest(SCOPE)) continue;
      var focusables = container.querySelectorAll(FOCUSABLE);
      for (var j = 0; j < focusables.length; j++) {
        var el = focusables[j];
        if (!el) continue;
        var ti = el.getAttribute("tabindex");
        if (ti === null || parseInt(ti, 10) >= 0) {
          el.setAttribute("tabindex", "-1");
        }
        // belt-and-braces: a hidden text input should not be a tab stop
        var tag = (el.tagName || "").toLowerCase();
        if (tag === "input" && el.type !== "hidden" && !el.disabled) {
          try { el.setAttribute("aria-hidden", "true"); } catch (e) {}
        }
      }
    }
  }

  function scan() {
    try {
      var scopes = document.querySelectorAll(SCOPE);
      for (var i = 0; i < scopes.length; i++) fix(scopes[i]);
    } catch (e) {}
  }

  function start() {
    scan();
    if (!("MutationObserver" in window)) return;
    var obs = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var m = mutations[i];
        var t = m.target;
        if (t && t.closest && t.closest(SCOPE)) {
          fix(t.closest(SCOPE));
        } else if (m.addedNodes && m.addedNodes.length) {
          scan();
          break;
        }
      }
    });
    try {
      obs.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["aria-hidden", "tabindex", "class"]
      });
    } catch (e) {}
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
