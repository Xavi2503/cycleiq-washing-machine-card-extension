/**
 * CycleIQ — Predictor Extension for Washing Machine Animated Card
 * Version 0.1.0
 *
 * Optional companion extension for:
 * https://github.com/sionetta/wm_animated_ha_card
 *
 * CycleIQ does not replace the original card. It extends the already loaded
 * custom:washing-machine-card when predictor-specific entities are configured.
 */
(() => {
  "use strict";

  const VERSION = "0.1.0";
  const CARD_TAG = "washing-machine-card";
  const PATCHED = Symbol.for("cycleiq.wm-card.patched");

  const LABELS = {
    en: { start: "START", expected: "EXPECTED", remaining: "REMAINING", end: "END", duration: "DURATION" },
    nl: { start: "START", expected: "VERWACHT", remaining: "RESTEREND", end: "EINDE", duration: "DUUR" },
    de: { start: "START", expected: "ERWARTET", remaining: "RESTZEIT", end: "ENDE", duration: "DAUER" },
    fr: { start: "DÉBUT", expected: "PRÉVU", remaining: "RESTANT", end: "FIN", duration: "DURÉE" },
    ru: { start: "СТАРТ", expected: "ОЖИДАЕТСЯ", remaining: "ОСТАЛОСЬ", end: "КОНЕЦ", duration: "ДЛИТЕЛЬН." },
    pt: { start: "INÍCIO", expected: "PREVISTO", remaining: "RESTANTE", end: "FIM", duration: "DURAÇÃO" },
    el: { start: "ΕΝΑΡΞΗ", expected: "ΑΝΑΜΕΝΕΤΑΙ", remaining: "ΑΠΟΜΕΝΕΙ", end: "ΤΕΛΟΣ", duration: "ΔΙΑΡΚΕΙΑ" }
  };

  function lang(card) {
    const cfg = String(card?._config?.language || "auto").toLowerCase();
    if (cfg !== "auto" && LABELS[cfg]) return cfg;
    const ha = String(card?._hass?.locale?.language || card?._hass?.language || "en").toLowerCase();
    if (LABELS[ha]) return ha;
    const short = ha.split(/[-_]/)[0];
    return LABELS[short] ? short : "en";
  }

  function labels(card) {
    return LABELS[lang(card)] || LABELS.en;
  }

  function activeFor(card) {
    const c = card?._config || {};
    return Boolean(c.expected_end_entity || c.last_end_entity);
  }

  function state(card, id) {
    return id && card?._hass?.states ? card._hass.states[id] : undefined;
  }

  function valid(entity) {
    if (!entity) return false;
    const value = String(entity.state ?? "").trim();
    return value !== "" && !["unknown", "unavailable", "none", "null"].includes(value.toLowerCase());
  }

  function cycleActive(card) {
    try {
      return typeof card._cycleIsActive === "function" ? !!card._cycleIsActive() : false;
    } catch (_) {
      return false;
    }
  }

  function dateParts(card, raw) {
    if (!raw) return null;
    try {
      if (typeof card._fmtDateTime === "function") {
        const p = card._fmtDateTime(raw);
        if (p?.time) return p;
      }
    } catch (_) {}

    const d = new Date(String(raw).replace(" ", "T"));
    if (Number.isNaN(d.getTime())) return null;
    return {
      day: "",
      time: d.toLocaleTimeString(card?._hass?.locale?.language || undefined, {
        hour: "2-digit",
        minute: "2-digit"
      })
    };
  }

  function renderDate(card, id) {
    const e = state(card, id);
    if (!valid(e)) return "—";
    const p = dateParts(card, e.state);
    if (!p) return escapeHtml(String(e.state));
    return (p.day ? '<span class="cycleiq-day">' + escapeHtml(p.day) + '</span>' : "") +
      '<span class="cycleiq-time">' + escapeHtml(p.time) + '</span>';
  }

  function renderExpected(card, id) {
    const e = state(card, id);
    if (!valid(e)) return "—";
    const raw = String(e.state).trim();

    const human = raw.match(/^(Vandaag|Morgen|Today|Tomorrow|\+\d+\s+dagen?)\s+(\d{1,2}:\d{2})$/i);
    if (human) {
      return '<span class="cycleiq-day">' + escapeHtml(human[1]) + '</span>' +
        '<span class="cycleiq-time">' + escapeHtml(human[2]) + '</span>';
    }

    const p = dateParts(card, raw);
    if (p) {
      return (p.day ? '<span class="cycleiq-day">' + escapeHtml(p.day) + '</span>' : "") +
        '<span class="cycleiq-time">' + escapeHtml(p.time) + '</span>';
    }

    return escapeHtml(raw);
  }

  function renderRemaining(card) {
    try {
      if (typeof card._remainingMinutes === "function" && typeof card._fmtRemaining === "function") {
        const formatted = card._fmtRemaining(card._remainingMinutes());
        if (formatted !== null && formatted !== undefined) return escapeHtml(String(formatted));
      }
    } catch (_) {}

    const e = state(card, card?._config?.remaining_entity);
    return valid(e) ? escapeHtml(String(e.state)) : "—";
  }

  function renderDuration(card) {
    let minutes = null;

    if (cycleActive(card)) {
      try {
        const start = typeof card._startDate === "function" ? card._startDate() : null;
        if (start) minutes = Math.max(0, Math.floor((Date.now() - start.getTime()) / 60000));
      } catch (_) {}
    } else {
      const e = state(card, card?._config?.duration_entity);
      if (valid(e)) {
        const n = Number(String(e.state).replace(",", "."));
        if (Number.isFinite(n)) minutes = n;
      }
    }

    if (minutes === null) return "—";

    const total = Math.max(0, Math.round(minutes));
    if (total >= 60) {
      const h = Math.floor(total / 60);
      const m = total % 60;
      return escapeHtml(h + ":" + String(m).padStart(2, "0")) + ' <span class="cycleiq-unit">uur</span>';
    }
    return escapeHtml(String(total)) + ' <span class="cycleiq-unit">min</span>';
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function cell(key, label) {
    const el = document.createElement("div");
    el.className = "cycleiq-item";
    el.id = "cycleiq-" + key;
    el.innerHTML =
      '<div class="cycleiq-label">' + escapeHtml(label) + '</div>' +
      '<div class="cycleiq-value" id="cycleiq-' + key + '-value">—</div>';
    return el;
  }

  function moreInfo(card, element, entityId) {
    if (!element || !entityId || typeof card._moreInfo !== "function") return;
    element.addEventListener("click", () => card._moreInfo(entityId));
  }

  function install(card) {
    if (!activeFor(card)) return;

    const root = card.shadowRoot;
    if (!root || root.getElementById("cycleiq-panel")) return;

    const officialLastCycle = root.getElementById("lastCycle");
    if (!officialLastCycle) {
      console.warn("[CycleIQ] Compatible insertion point not found. Original card left untouched.");
      return;
    }

    const l = labels(card);

    const style = document.createElement("style");
    style.id = "cycleiq-style";
    style.textContent = [
      "#cycleiq-panel{display:block;}",
      ".cycleiq-grid{display:grid;grid-template-columns:1fr 1.25fr 1fr 1fr .9fr;}",
      ".cycleiq-item{padding:0 12px;border-left:1px solid var(--wm-divider);min-width:0;cursor:pointer;}",
      ".cycleiq-item:first-child{border-left:none;padding-left:0;}",
      ".cycleiq-label{font-size:9px;font-weight:700;letter-spacing:.65px;color:var(--wm-label);line-height:1.15;}",
      ".cycleiq-value{font-size:13.5px;font-weight:800;margin-top:5px;overflow-wrap:break-word;white-space:pre-line;line-height:1.15;}",
      ".cycleiq-day{display:block;font-weight:400;}",
      ".cycleiq-time{display:block;font-weight:800;}",
      ".cycleiq-unit{font-size:10px;font-weight:700;color:var(--wm-accent);}",
      ".narrow .cycleiq-item{padding:0 7px;}",
      ".narrow .cycleiq-label{font-size:8px;letter-spacing:.4px;}",
      ".narrow .cycleiq-value{font-size:12px;}",
      ".xnarrow .cycleiq-grid{grid-template-columns:repeat(5,minmax(0,1fr));}",
      ".xnarrow .cycleiq-item{padding:0 4px;}",
      ".xnarrow .cycleiq-label{font-size:7px;letter-spacing:.2px;}",
      ".xnarrow .cycleiq-value{font-size:10.5px;}"
    ].join("");

    const panel = document.createElement("div");
    panel.className = "panel";
    panel.id = "cycleiq-panel";

    const grid = document.createElement("div");
    grid.className = "cycleiq-grid";
    grid.append(
      cell("start", l.start),
      cell("expected", l.expected),
      cell("remaining", l.remaining),
      cell("end", l.end),
      cell("duration", l.duration)
    );
    panel.appendChild(grid);

    officialLastCycle.insertAdjacentElement("afterend", panel);
    root.appendChild(style);

    const c = card._config || {};
    moreInfo(card, root.getElementById("cycleiq-start"), c.last_wash_entity);
    moreInfo(card, root.getElementById("cycleiq-expected"), c.expected_end_entity);
    moreInfo(card, root.getElementById("cycleiq-remaining"), c.remaining_entity);
    moreInfo(card, root.getElementById("cycleiq-end"), c.last_end_entity);
    moreInfo(card, root.getElementById("cycleiq-duration"), c.duration_entity);
  }

  function setHtml(root, id, html) {
    const el = root?.getElementById(id);
    if (el) el.innerHTML = html;
  }

  function update(card) {
    if (!activeFor(card)) return;
    install(card);

    const root = card.shadowRoot;
    const panel = root?.getElementById("cycleiq-panel");
    if (!panel) return;

    // Replace the official last-cycle stats visually only while CycleIQ is active.
    // The original element stays in the DOM and the original card logic is untouched.
    const officialLastCycle = root.getElementById("lastCycle");
    if (officialLastCycle) officialLastCycle.style.display = "none";

    const c = card._config || {};
    setHtml(root, "cycleiq-start-value", c.last_wash_entity ? renderDate(card, c.last_wash_entity) : "—");
    setHtml(root, "cycleiq-expected-value",
      cycleActive(card) && c.expected_end_entity ? renderExpected(card, c.expected_end_entity) : "—");
    setHtml(root, "cycleiq-remaining-value",
      cycleActive(card) && c.remaining_entity ? renderRemaining(card) : "—");
    setHtml(root, "cycleiq-end-value",
      !cycleActive(card) && c.last_end_entity ? renderDate(card, c.last_end_entity) : "—");
    setHtml(root, "cycleiq-duration-value", c.duration_entity ? renderDuration(card) : "—");
  }

  async function patch() {
    await customElements.whenDefined(CARD_TAG);

    const Card = customElements.get(CARD_TAG);
    const proto = Card?.prototype;
    if (!proto || proto[PATCHED]) return;

    if (typeof proto._build !== "function" || typeof proto._update !== "function") {
      console.warn("[CycleIQ] Unsupported Washing Machine Animated Card version. Original card left untouched.");
      return;
    }

    const originalBuild = proto._build;
    const originalUpdate = proto._update;

    proto._build = function (...args) {
      const result = originalBuild.apply(this, args);
      try { install(this); }
      catch (error) { console.warn("[CycleIQ] Extension build failed. Original card remains active.", error); }
      return result;
    };

    proto._update = function (...args) {
      const result = originalUpdate.apply(this, args);
      try { update(this); }
      catch (error) { console.warn("[CycleIQ] Extension update failed. Original card remains active.", error); }
      return result;
    };

    Object.defineProperty(proto, PATCHED, { value: true });

    window.CycleIQ = {
      version: VERSION,
      target: CARD_TAG,
      active: true
    };

    console.info("[CycleIQ] v" + VERSION + " loaded.");
  }

  patch().catch((error) => {
    console.warn("[CycleIQ] Could not initialize. Original card remains untouched.", error);
  });
})();
