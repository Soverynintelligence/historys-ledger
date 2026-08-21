/* History's Ledger — shell: tabs, source cards, floating Atticus, interactive hooks. */
(function () {
  "use strict";

  var ATTICUS_URL = "https://atticus.historysledger.com/chat";
  var WAITLIST_URL = "https://atticus.historysledger.com/waitlist";

  /* ── entry tabs ─────────────────────────────────────────────────────────── */
  function initTabs(root) {
    var tablist = root.querySelector('[role="tablist"]');
    if (!tablist) return;
    var tabs = Array.prototype.slice.call(tablist.querySelectorAll('[role="tab"]'));
    var panels = tabs.map(function (t) {
      return root.querySelector("#" + t.getAttribute("aria-controls"));
    });
    var seen = {};

    function paintProgress(activeId) {
      var rail = root.querySelector("[data-progress-rail]");
      if (!rail) return;
      var marks = rail.querySelectorAll("span");
      tabs.forEach(function (t, i) {
        if (!marks[i]) return;
        marks[i].classList.toggle("seen", !!seen[t.id]);
        marks[i].classList.toggle("current", t.id === activeId);
      });
    }

    function select(tab, focus) {
      seen[tab.id] = true;
      try {
        sessionStorage.setItem(
          "hl-tabs-" + (root.getAttribute("data-entry") || "x"),
          JSON.stringify(seen)
        );
      } catch (e) { /* ignore */ }
      tabs.forEach(function (t, i) {
        var on = t === tab;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        if (panels[i]) panels[i].classList.toggle("is-active", on);
      });
      paintProgress(tab.id);
      if (focus) tab.focus();
      try {
        history.replaceState(null, "", "#" + tab.id);
      } catch (e) { /* ignore */ }
    }

    try {
      var raw = sessionStorage.getItem(
        "hl-tabs-" + (root.getAttribute("data-entry") || "x")
      );
      if (raw) seen = JSON.parse(raw) || {};
    } catch (e) {
      seen = {};
    }

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        select(tab, false);
      });
      tab.addEventListener("keydown", function (e) {
        var i = tabs.indexOf(tab);
        var next = null;
        if (e.key === "ArrowRight" || e.key === "ArrowDown")
          next = tabs[(i + 1) % tabs.length];
        if (e.key === "ArrowLeft" || e.key === "ArrowUp")
          next = tabs[(i - 1 + tabs.length) % tabs.length];
        if (e.key === "Home") next = tabs[0];
        if (e.key === "End") next = tabs[tabs.length - 1];
        if (next) {
          e.preventDefault();
          select(next, true);
        }
      });
    });

    var hash = (location.hash || "").replace(/^#/, "");
    var initial =
      tabs.find(function (t) {
        return t.id === hash;
      }) || tabs[0];
    if (initial) select(initial, false);
  }

  document.querySelectorAll("[data-entry]").forEach(initTabs);

  /* ── optional weigh scale ───────────────────────────────────────────────── */
  var before = null;
  var after = null;

  function wireOpts(host, onPick) {
    if (!host) return;
    host.addEventListener("click", function (e) {
      var b = e.target.closest(".opt");
      if (!b) return;
      Array.prototype.forEach.call(host.children, function (c) {
        c.setAttribute("aria-pressed", "false");
      });
      b.setAttribute("aria-pressed", "true");
      onPick(+b.dataset.i);
    });
  }

  wireOpts(document.getElementById("opts0"), function (i) {
    before = i;
    var hint = document.getElementById("hint0");
    if (hint)
      hint.textContent =
        "Nothing is scored. Open Weigh again after reading if you want a before/after.";
  });

  wireOpts(document.getElementById("opts1"), function (i) {
    after = i;
    var r = document.getElementById("readout");
    if (!r) return;
    r.hidden = false;
    if (before === null) {
      var m0 = document.getElementById("moved");
      if (m0)
        m0.textContent =
          "You chose a position after reading. Set one under Weigh first if you want a before/after comparison.";
      return;
    }
    var pipA = document.getElementById("pipA");
    var pipB = document.getElementById("pipB");
    if (pipA) pipA.style.left = (before / 4) * 100 + "%";
    if (pipB) pipB.style.left = (after / 4) * 100 + "%";
    var d = after - before;
    var m = document.getElementById("moved");
    if (!m) return;
    if (d === 0) {
      m.textContent =
        "You landed where you started. The record didn’t move you — which is a result, not a failure.";
    } else {
      m.textContent =
        "You moved " +
        Math.abs(d) +
        " " +
        (Math.abs(d) === 1 ? "step" : "steps") +
        " toward " +
        (d > 0 ? "the cost" : "the achievement") +
        ". The documents did that, not us.";
    }
  });

  /* ── Stage 3: source card drawer ─────────────────────────────────────────── */
  var drawer = document.getElementById("source-drawer");
  var cardsData = {};
  try {
    var rawCards = document.getElementById("source-cards-data");
    if (rawCards && rawCards.textContent)
      cardsData = JSON.parse(rawCards.textContent);
  } catch (err) {
    cardsData = {};
  }

  function statusLabel(card) {
    if (!card) return "";
    if (card.kind === "gap") {
      if (card.status === "unverified") return "Cited, unchecked";
      return "Unverified";
    }
    if (card.status === "held") return "Held — text on record";
    if (card.status === "restricted")
      return "Restricted — we may not reproduce the full text";
    if (card.status === "citation-only")
      return "Citation only — document text not held here";
    return card.status || "";
  }

  function statusClass(card) {
    if (!card) return "unsourced";
    if (card.kind === "gap")
      return card.status === "unverified" ? "unverified" : "unsourced";
    if (card.status === "held") return "verified";
    if (card.status === "restricted") return "unverified";
    return "unsourced";
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fillCard(card) {
    if (!drawer || !card) return;
    document.getElementById("card-title").textContent = card.title || "Source";
    var meta = [];
    if (card.author) meta.push(card.author);
    if (card.date) meta.push(card.date);
    if (card.type && card.type !== "gap") meta.push(card.type);
    if (card.repository) meta.push(card.repository);
    if (card.id && card.kind !== "gap") meta.push("id " + card.id);
    document.getElementById("card-meta").textContent = meta.join(" · ");
    var st = document.getElementById("card-status");
    st.innerHTML =
      '<span class="prov ' +
      statusClass(card) +
      '">' +
      statusLabel(card) +
      "</span>";
    var co = document.getElementById("card-callout");
    if (card.callout) {
      co.hidden = false;
      co.textContent = card.callout;
    } else if (card.span) {
      co.hidden = false;
      co.textContent = "“" + card.span + "”";
    } else {
      co.hidden = true;
      co.textContent = "";
    }
    var pass = document.getElementById("card-passage");
    if (card.passages && card.passages.length) {
      var p = card.passages[0];
      pass.hidden = false;
      pass.innerHTML =
        "…" +
        escapeHtml(p.before.slice(-220)) +
        " <b>" +
        escapeHtml(p.quoted) +
        "</b> " +
        escapeHtml(p.after.slice(0, 220)) +
        "…";
    } else {
      pass.hidden = true;
      pass.innerHTML = "";
    }
    var reason = document.getElementById("card-reason");
    if (card.reason) {
      reason.hidden = false;
      reason.textContent = card.reason;
    } else if (card.status === "restricted") {
      reason.hidden = false;
      reason.textContent =
        "Rights are restricted. We cite this source but do not hold the full text here.";
    } else if (card.status === "citation-only") {
      reason.hidden = false;
      reason.textContent =
        "The citation is real; a clean full-text transcript is not held in this collection yet.";
    } else {
      reason.hidden = true;
      reason.textContent = "";
    }
    var actions = document.getElementById("card-actions");
    actions.innerHTML = "";
    if (card.url) {
      var a = document.createElement("a");
      a.className = "btn";
      a.href = card.url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent =
        card.status === "restricted"
          ? "Authorized copy →"
          : "Go to the document →";
      actions.appendChild(a);
    }
    var askAbout = document.createElement("button");
    askAbout.type = "button";
    askAbout.className = "btn quiet";
    askAbout.textContent = "Ask Atticus about this →";
    askAbout.addEventListener("click", function () {
      closeCard();
      openAtticus(
        "What does the record actually say about “" +
          (card.title || card.span || "this source") +
          "”? Cite it."
      );
    });
    actions.appendChild(askAbout);
    var closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "btn quiet";
    closeBtn.setAttribute("data-close-card", "");
    closeBtn.textContent = "Close";
    actions.appendChild(closeBtn);
  }

  function openCard(id) {
    var card = cardsData[id];
    if (!card || !drawer) return;
    fillCard(card);
    drawer.hidden = false;
    document.body.classList.add("card-open");
    var panel = drawer.querySelector(".card-drawer-panel");
    if (panel) panel.focus();
  }

  function closeCard() {
    if (!drawer) return;
    drawer.hidden = true;
    document.body.classList.remove("card-open");
  }

  document.addEventListener("click", function (e) {
    var open = e.target.closest("[data-open-card]");
    if (open) {
      e.preventDefault();
      open.classList.add("tap-ripple");
      setTimeout(function () {
        open.classList.remove("tap-ripple");
      }, 450);
      openCard(open.getAttribute("data-open-card"));
      return;
    }
    if (e.target.closest("[data-close-card]")) {
      e.preventDefault();
      closeCard();
    }
  });

  /* ── Floating Atticus (every page) ──────────────────────────────────────── */
  var entryEl = document.querySelector("[data-entry]");
  var entryId = entryEl ? entryEl.getAttribute("data-entry") || "" : "";
  var entryTitle = "";
  if (entryEl) {
    var h1 = entryEl.querySelector("h1");
    if (h1) entryTitle = h1.textContent.replace(/\s+/g, " ").trim();
  }

  var CHIPS = entryId
    ? [
        "Pull the primary source this entry rests on most.",
        "Show me one verified quotation from the held record.",
        "Where is the biggest gap in the sources for this entry?",
        "Is there a picture we hold for anything in this entry?",
      ]
    : [
        "Open the Declaration of Independence — what do we hold?",
        "Show me a picture of the Declaration if we have one.",
        "What shelves are open in this library?",
        "Try to invent a founding date that isn't in the record.",
      ];

  function ensureAtticusUI() {
    if (document.getElementById("atticus-float")) return;

    var fab = document.createElement("button");
    fab.type = "button";
    fab.className = "atticus-fab";
    fab.id = "atticus-fab";
    fab.setAttribute("aria-expanded", "false");
    fab.setAttribute("aria-controls", "atticus-float");
    fab.innerHTML =
      '<span class="dot-live" aria-hidden="true"></span><span>Ask Atticus</span>';
    document.body.appendChild(fab);

    var panel = document.createElement("div");
    panel.className = "atticus-float";
    panel.id = "atticus-float";
    panel.hidden = true;
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "Ask Atticus");
    var contextLine = entryTitle
      ? "Helper on this entry · pulls held sources"
      : "Helper · open shelves only · pulls sources & images";
    panel.innerHTML =
      '<div class="atticus-float-head">' +
      "<div><strong>Atticus</strong>" +
      '<div class="subline">' +
      escapeHtml(contextLine) +
      "</div></div>" +
      '<button type="button" class="atticus-float-close" id="atticus-float-close" aria-label="Close">×</button>' +
      "</div>" +
      '<div class="atticus-float-body" id="atticus-float-log" aria-live="polite">' +
      '<p class="note" style="margin:0">He opens documents and pictures from the open shelves only. A clean refusal is the product working.</p>' +
      "</div>" +
      '<div class="atticus-chips" id="atticus-chips"></div>' +
      '<form class="atticus-float-form" id="atticus-float-form">' +
      '<label for="atticus-q" class="visually-hidden" style="position:absolute;left:-9999px">Ask Atticus</label>' +
      '<input id="atticus-q" autocomplete="off" placeholder="Ask him to open a source…">' +
      '<button class="btn" type="submit" id="atticus-go">Ask</button>' +
      "</form>";
    document.body.appendChild(panel);

    var chips = document.getElementById("atticus-chips");
    CHIPS.forEach(function (q) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "atticus-chip";
      b.textContent = q;
      b.addEventListener("click", function () {
        openAtticus(q);
      });
      chips.appendChild(b);
    });

    fab.addEventListener("click", function () {
      if (panel.hidden) openAtticus();
      else closeAtticus();
    });
    document
      .getElementById("atticus-float-close")
      .addEventListener("click", closeAtticus);

    // Nav "Ask Atticus" links open the float
    document.querySelectorAll('a[href="#ask"], a[href*="ask-atticus"]').forEach(
      function (a) {
        a.addEventListener("click", function (e) {
          e.preventDefault();
          openAtticus();
        });
      }
    );
  }

  var sid = "hl-" + Math.random().toString(36).slice(2);
  var hist = [];

  function addTurn(who, text, cls, artifacts) {
    var log = document.getElementById("atticus-float-log");
    if (!log) return;
    // clear intro note once conversation starts
    var intro = log.querySelector(".note");
    if (intro && hist.length <= 1) intro.remove();
    var d = document.createElement("div");
    d.className = "turn";
    var a = document.createElement("p");
    a.className = "q";
    a.textContent = who;
    var b = document.createElement("p");
    b.className = "a " + (cls || "");
    b.textContent = text;
    d.appendChild(a);
    d.appendChild(b);
    if (artifacts && artifacts.length) {
      d.appendChild(renderArtifacts(artifacts));
    }
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  }

  function renderArtifacts(artifacts) {
    var wrap = document.createElement("div");
    wrap.className = "atticus-artifacts";
    artifacts.forEach(function (art) {
      if (!art || !art.type) return;
      if (art.type === "source") {
        var chip = document.createElement("button");
        chip.type = "button";
        chip.className = "atticus-artifact source";
        chip.textContent = art.label || art.title || art.id || "Source";
        chip.title = art.title || art.id || "";
        chip.addEventListener("click", function () {
          if (art.id && typeof openCard === "function" && cardsData[art.id]) {
            openCard(art.id);
          } else if (art.url) {
            window.open(art.url, "_blank", "noopener");
          } else {
            openAtticus(
              "Open the source “" +
                (art.label || art.title || art.id) +
                "” and tell me what we hold."
            );
          }
        });
        wrap.appendChild(chip);
      } else if (art.type === "media" && art.url) {
        var card = document.createElement("figure");
        card.className = "atticus-artifact media";
        var img = document.createElement("img");
        img.src = art.url;
        img.alt = art.caption || art.title || "Held image";
        img.loading = "lazy";
        img.referrerPolicy = "no-referrer-when-downgrade";
        var cap = document.createElement("figcaption");
        cap.textContent =
          (art.caption || art.title || "") +
          (art.credit ? " — " + art.credit : "");
        card.appendChild(img);
        card.appendChild(cap);
        if (art.source_id) {
          card.style.cursor = "pointer";
          card.addEventListener("click", function () {
            if (cardsData[art.source_id]) openCard(art.source_id);
          });
        }
        wrap.appendChild(card);
      }
    });
    return wrap;
  }

  function openAtticus(prefill) {
    ensureAtticusUI();
    var panel = document.getElementById("atticus-float");
    var fab = document.getElementById("atticus-fab");
    panel.hidden = false;
    fab.setAttribute("aria-expanded", "true");
    document.body.classList.add("atticus-open");
    var input = document.getElementById("atticus-q");
    if (prefill) {
      input.value = prefill;
      // auto-send challenge chips
      setTimeout(function () {
        document.getElementById("atticus-float-form").requestSubmit();
      }, 50);
    } else {
      input.focus();
    }
  }

  function closeAtticus() {
    var panel = document.getElementById("atticus-float");
    var fab = document.getElementById("atticus-fab");
    if (panel) panel.hidden = true;
    if (fab) fab.setAttribute("aria-expanded", "false");
    document.body.classList.remove("atticus-open");
  }

  function wireFloatForm() {
    var form = document.getElementById("atticus-float-form");
    if (!form || form._wired) return;
    form._wired = true;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var input = document.getElementById("atticus-q");
      var go = document.getElementById("atticus-go");
      var text = (input.value || "").trim();
      if (!text) return;
      addTurn("You", text, "you");
      input.value = "";
      go.disabled = true;
      go.textContent = "…";
      hist.push({ role: "user", content: text });
      var body = { session_id: sid, messages: hist };
      if (entryId) body.entry_id = entryId;
      fetch(ATTICUS_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (d) {
          var reply =
            (d && d.reply) ||
            "The reading room is quiet just now. Try again shortly.";
          var arts = (d && d.artifacts) || [];
          hist.push({ role: "assistant", content: reply });
          addTurn("Atticus", reply, "him", arts);
        })
        .catch(function () {
          addTurn(
            "Atticus",
            "The reading room is quiet just now. Try again shortly.",
            "him"
          );
        })
        .then(function () {
          go.disabled = false;
          go.textContent = "Ask";
          document.getElementById("atticus-q").focus();
        });
    });
  }

  // Cover landing is seal + Enter only — no floating Atticus until you open the book
  var isCover = document.body.classList.contains("is-cover");
  if (!isCover) {
    ensureAtticusUI();
    wireFloatForm();
  }

  // Re-wire after ensure (form exists)
  document.addEventListener("submit", function (e) {
    if (e.target && e.target.id === "atticus-float-form" && !e.target._wired) {
      wireFloatForm();
    }
  });

  // Homepage inline form → open float instead of dual UIs
  var legacyForm = document.getElementById("ask-form");
  if (legacyForm) {
    legacyForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var q = document.getElementById("q");
      openAtticus((q && q.value) || "");
      if (q) q.value = "";
    });
  }

  // Challenge chips / home hooks
  document.addEventListener("click", function (e) {
    var chip = e.target.closest("[data-ask-atticus]");
    if (chip) {
      e.preventDefault();
      openAtticus(chip.getAttribute("data-ask-atticus") || chip.textContent);
    }
    var openFloat = e.target.closest("[data-open-atticus]");
    if (openFloat) {
      e.preventDefault();
      openAtticus(openFloat.getAttribute("data-open-atticus") || "");
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeCard();
      closeAtticus();
    }
  });

  /* ── Family year waitlist ──────────────────────────────────────────────── */
  function wireWaitlist() {
    var form = document.getElementById("waitlist-form");
    if (!form || form._wired) return;
    form._wired = true;
    var status = document.getElementById("waitlist-status");
    var go = document.getElementById("waitlist-go");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var emailEl = document.getElementById("wl-email");
      var email = (emailEl && emailEl.value || "").trim();
      if (!email || email.indexOf("@") < 1) {
        if (status) {
          status.textContent = "A valid email is required.";
          status.className = "wait-status note is-err";
        }
        if (emailEl) emailEl.focus();
        return;
      }
      var priceEl = form.querySelector('input[name="price_interest"]:checked');
      var body = {
        email: email,
        name: (document.getElementById("wl-name") && document.getElementById("wl-name").value || "").trim(),
        note: (document.getElementById("wl-note") && document.getElementById("wl-note").value || "").trim(),
        price_interest: priceEl ? priceEl.value : "unsure",
        source: (form.querySelector('input[name="source"]') && form.querySelector('input[name="source"]').value) || "site",
      };
      if (go) {
        go.disabled = true;
        go.textContent = "…";
      }
      if (status) {
        status.textContent = "Saving…";
        status.className = "wait-status note";
      }
      fetch(WAITLIST_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
        .then(function (r) {
          return r.json().then(function (d) {
            return { ok: r.ok, d: d };
          });
        })
        .then(function (res) {
          if (res.ok && res.d && res.d.ok) {
            if (status) {
              status.textContent =
                res.d.message ||
                "You're on the list. We'll email when Family year opens.";
              status.className = "wait-status note is-ok";
            }
            form.reset();
            var def = form.querySelector('input[name="price_interest"][value="79"]');
            if (def) def.checked = true;
          } else {
            if (status) {
              status.textContent =
                (res.d && res.d.error) ||
                "Could not save just now. Try again in a moment.";
              status.className = "wait-status note is-err";
            }
          }
        })
        .catch(function () {
          if (status) {
            status.textContent =
              "Could not reach the reading room. Check your connection and try again.";
            status.className = "wait-status note is-err";
          }
        })
        .then(function () {
          if (go) {
            go.disabled = false;
            go.textContent = "Join the list";
          }
        });
    });
  }
  wireWaitlist();
})();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/sw.js").catch(function () {});
  });
}
