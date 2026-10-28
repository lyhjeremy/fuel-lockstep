/* Fuel Lockstep charts. Plain SVG, no libraries. Data: assets/data.json (scripts/export_web.py). */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var D, BR, dayCount, hkStart, perthByDate = {}, perthDates = [];

  function el(tag, attrs, parent, text) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function clear(svg) { while (svg.lastChild && svg.lastChild.tagName !== "title") svg.removeChild(svg.lastChild); }
  // Size the drawing to the rendered width so 12px labels stay 12px on a phone.
  function size(svg, h) {
    var w = Math.round(Math.max(340, Math.min(900, svg.parentNode.clientWidth || 900)));
    svg.setAttribute("viewBox", "0 0 " + w + " " + h);
    return w;
  }
  function lin(d0, d1, r0, r1) { return function (v) { return r0 + (v - d0) / (d1 - d0) * (r1 - r0); }; }
  function addDays(iso, n) { var t = new Date(iso + "T00:00:00Z"); t.setUTCDate(t.getUTCDate() + n); return t.toISOString().slice(0, 10); }
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function fmtDate(iso) { var p = iso.split("-"); return +p[2] + " " + MON[+p[1] - 1] + " " + p[0]; }
  function f2(v) { return v == null ? "n/a" : v.toFixed(2); }
  function niceTicks(lo, hi, n) {
    var span = hi - lo, step = Math.pow(10, Math.floor(Math.log10(span / n))), err = span / n / step;
    step *= err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1;
    var out = []; for (var v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(6));
    return out;
  }
  function yAxis(svg, y, ticks, x0, x1, fmt) {
    var g = el("g", { "class": "grid" }, svg);
    ticks.forEach(function (t) {
      el("line", { x1: x0, x2: x1, y1: y(t), y2: y(t) }, g);
      el("text", { x: x0 - 8, y: y(t) + 4, "text-anchor": "end", "font-size": 12 }, g, fmt ? fmt(t) : t);
    });
  }
  function price(brand, day) {
    var s = D.steps[brand], lo = 0, hi = s.length - 1;
    if (day < s[0][0]) return null;
    while (lo < hi) { var mid = (lo + hi + 1) >> 1; if (s[mid][0] <= day) lo = mid; else hi = mid - 1; }
    return s[lo][1];
  }
  function segButtons(host, labels, active, onPick) {
    host.innerHTML = "";
    labels.forEach(function (l) {
      var b = document.createElement("button");
      b.className = "btn seg-b"; b.textContent = l; b.setAttribute("aria-pressed", l === active ? "true" : "false");
      b.addEventListener("click", function () {
        host.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true"); onPick(l);
      });
      host.appendChild(b);
    });
  }
  // Pointer and arrow-key cursor for charts with an x index.
  function cursorize(svg, n, xOf, onMove) {
    var idx = n - 1;
    function set(i) { idx = Math.max(0, Math.min(n - 1, i)); onMove(idx); }
    svg.onmousemove = function (e) {
      var r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
      var x = (e.clientX - r.left) / r.width * vb.width, best = 0, bd = Infinity;
      for (var i = 0; i < n; i++) { var d = Math.abs(xOf(i) - x); if (d < bd) { bd = d; best = i; } }
      set(best);
    };
    svg.onkeydown = function (e) {
      if (e.key === "ArrowLeft") { set(idx - (e.shiftKey ? 10 : 1)); e.preventDefault(); }
      if (e.key === "ArrowRight") { set(idx + (e.shiftKey ? 10 : 1)); e.preventDefault(); }
    };
    set(idx);
  }

  /* ---------- Day board ---------- */
  var board = { day: 0 };
  function initBoard() {
    var input = document.getElementById("day");
    input.max = dayCount - 1;
    var lastPerth = perthDates[perthDates.length - 1];
    var start = Math.min(dayCount - 1, Math.round((Date.parse(lastPerth) - Date.parse(hkStart)) / 864e5));
    input.value = start;
    input.addEventListener("input", function () { drawBoard(+input.value); });
    drawBoard(start);
  }
  function drawBoard(day) {
    board.day = day;
    var iso = addDays(hkStart, day);
    document.getElementById("day-out").textContent = fmtDate(iso);
    var prices = BR.map(function (b) { return price(b, day); });
    var counts = {}; prices.forEach(function (p) { counts[p] = (counts[p] || 0) + 1; });
    var mode = +Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; })[0];
    var tb = document.getElementById("hk-board"); tb.innerHTML = "";
    BR.forEach(function (b, i) {
      var tr = document.createElement("tr"); if (prices[i] !== mode) tr.className = "off";
      tr.innerHTML = "<td>" + b + "</td><td class=\"num\">" + f2(prices[i]) + "</td>";
      tb.appendChild(tr);
    });
    var off = BR.filter(function (b, i) { return prices[i] !== mode; });
    document.getElementById("hk-note").textContent = off.length === 0
      ? "All five brands posted the same price."
      : off.join(" and ") + (off.length === 1 ? " was" : " were") + " off the common price of HK$" + f2(mode) + " (shown in oxide).";
    drawStrip(iso);
    drawPerth(iso);
  }
  function drawStrip(iso) {
    var svg = document.getElementById("perth-strip"); clear(svg);
    var p = perthByDate[iso], note = document.getElementById("perth-note");
    if (!p) { note.textContent = "No Perth data for this day (FuelWatch series runs to " + fmtDate(perthDates[perthDates.length - 1]) + ")."; return; }
    var n = p[1], mn = p[2], p10 = p[3], p25 = p[4], med = p[5], p75 = p[6], p90 = p[7], mx = p[8];
    var lo = Math.floor((mn - 4) / 10) * 10, hi = Math.ceil((mx + 4) / 10) * 10;
    var W = size(svg, 150), x = lin(lo, hi, 20, W - 20), y = 70;
    niceTicks(lo, hi, 5).forEach(function (t) {
      el("line", { x1: x(t), x2: x(t), y1: 40, y2: 104, "class": "base", opacity: .35 }, svg);
      el("text", { x: x(t), y: 124, "text-anchor": "middle", "font-size": 12 }, svg, t);
    });
    el("line", { x1: x(mn), x2: x(mx), y1: y, y2: y, "class": "base" }, svg);
    el("rect", { x: x(p10), y: y - 14, width: x(p90) - x(p10), height: 28, "class": "f-band" }, svg);
    el("rect", { x: x(p25), y: y - 14, width: Math.max(2, x(p75) - x(p25)), height: 28, "class": "f-gray", opacity: .55 }, svg);
    el("rect", { x: x(med) - 1.5, y: y - 20, width: 3, height: 40, "class": "f-oxide" }, svg);
    el("text", { x: x(med), y: y - 26, "text-anchor": "middle", "class": "lab" }, svg, "median " + med.toFixed(1));
    el("text", { x: x(mn), y: y + 34, "text-anchor": "start", "font-size": 12 }, svg, "cheapest " + mn.toFixed(1));
    el("text", { x: x(mx), y: y + 34, "text-anchor": "end", "font-size": 12 }, svg, "dearest " + mx.toFixed(1));
    note.textContent = n + " stations. Cheapest to dearest: " + (mx - mn).toFixed(1) + " cents. Middle half of stations within " + (p75 - p25).toFixed(1) + " cents.";
  }

  /* ---------- Steps chart ---------- */
  function initSteps() {
    var years = []; for (var y = +hkStart.slice(0, 4); y <= +addDays(hkStart, dayCount - 1).slice(0, 4); y++) years.push(String(y));
    var labels = years.concat(["All"]);
    segButtons(document.getElementById("year-seg"), labels, "2026", drawSteps);
    drawSteps("2026");
  }
  function drawSteps(which) {
    var svg = document.getElementById("steps"); clear(svg);
    var d0, d1;
    if (which === "All") { d0 = 0; d1 = dayCount - 1; }
    else {
      d0 = Math.max(0, Math.round((Date.parse(which + "-01-01") - Date.parse(hkStart)) / 864e5));
      d1 = Math.min(dayCount - 1, Math.round((Date.parse(which + "-12-31") - Date.parse(hkStart)) / 864e5));
    }
    var lo = Infinity, hi = -Infinity;
    for (var d = d0; d <= d1; d++) BR.forEach(function (b) { var v = price(b, d); if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); } });
    var pad = (hi - lo) * 0.08 || 0.2;
    var W = size(svg, 340), L = 48, R = W - 96, T = 16, B = 300;
    var x = lin(d0, d1, L, R), y = lin(lo - pad, hi + pad, B, T);
    yAxis(svg, y, niceTicks(lo - pad, hi + pad, 5), L, R, function (t) { return t.toFixed(1); });
    // month or year ticks
    var g = el("g", { "class": "axis" }, svg);
    for (d = d0; d <= d1; d++) {
      var iso = addDays(hkStart, d);
      var tick = which === "All" ? iso.slice(5) === "01-01" : iso.slice(8) === "01" && (+iso.slice(5, 7) % (W < 600 ? 3 : 2) === 1);
      if (tick) el("text", { x: x(d), y: B + 22, "text-anchor": "middle" }, g, which === "All" ? iso.slice(0, 4) : MON[+iso.slice(5, 7) - 1]);
    }
    function path(b) {
      var s = "", prev = null;
      for (var d = d0; d <= d1; d++) {
        var v = price(b, d); if (v == null) continue;
        if (prev === null) s += "M" + x(d).toFixed(1) + "," + y(v).toFixed(1);
        else if (v !== prev) s += "H" + x(d).toFixed(1) + "V" + y(v).toFixed(1);
        prev = v;
      }
      return s + "H" + x(d1).toFixed(1);
    }
    BR.filter(function (b) { return b !== "Shell"; }).forEach(function (b) { el("path", { d: path(b), "class": "s-gray" }, svg); });
    el("path", { d: path("Shell"), "class": "s-oxide" }, svg);
    el("text", { x: R + 8, y: y(price("Shell", d1)) - 6, "class": "lab" }, svg, "Shell");
    el("text", { x: R + 8, y: y(price("Caltex", d1)) + 14, "font-size": 12 }, svg, "other four");
    var cur = el("line", { y1: T, y2: B, "class": "cursor" }, svg);
    var read = document.getElementById("steps-read");
    cursorize(svg, d1 - d0 + 1, function (i) { return x(d0 + i); }, function (i) {
      var d = d0 + i; cur.setAttribute("x1", x(d)); cur.setAttribute("x2", x(d));
      read.textContent = fmtDate(addDays(hkStart, d)) + "   " + BR.map(function (b) { return b + " " + f2(price(b, d)); }).join("   ");
    });
  }

  /* ---------- Lag matrix ---------- */
  function drawLags() {
    var svg = document.getElementById("lags");
    var full = D.episodes.filter(function (e) { return e[4].every(function (v) { return v != null; }); });
    clear(svg);
    var W = size(svg, 330), L = W < 600 ? 104 : 150, R = W - 30, T = 30, B = 250, maxLag = 7;
    var x = lin(0, maxLag, L, R), y = lin(0, BR.length - 1, T, B);
    var counts = BR.map(function (b, bi) { var c = new Array(maxLag + 1).fill(0); full.forEach(function (e) { c[e[4][bi]]++; }); return c; });
    var mx = Math.max.apply(null, counts.map(function (c) { return Math.max.apply(null, c); }));
    for (var l = 0; l <= maxLag; l++) el("text", { x: x(l), y: B + 40, "text-anchor": "middle", "font-size": 12 }, svg, l === 0 ? "0 days" : l);
    el("text", { x: (L + R) / 2, y: B + 62, "text-anchor": "middle", "font-size": 12 }, svg, "days after the first brand moved");
    BR.forEach(function (b, bi) {
      el("line", { x1: L, x2: R, y1: y(bi), y2: y(bi), "class": "base", opacity: .3 }, svg);
      el("text", { x: L - 34, y: y(bi) + 4, "text-anchor": "end", "class": "lab" }, svg, b);
      counts[bi].forEach(function (c, l) {
        if (!c) return;
        var r = 3 + 19 * Math.sqrt(c / mx);
        var g = el("g", {}, svg);
        el("circle", { cx: x(l), cy: y(bi), r: r, "class": (l === 0 ? "f-oxide" : "f-gray") + " dot" }, g);
        el("title", {}, g, b + ": " + c + " episodes at a lag of " + l + (l === 1 ? " day" : " days"));
        if (W >= 600) el("text", { x: x(l) + r + 4, y: y(bi) + 4, "font-size": 11 }, svg, c);
      });
    });
  }

  /* ---------- Years ---------- */
  function drawYears() {
    var svg = document.getElementById("years"), rows = D.byYear;
    clear(svg);
    var W = size(svg, 250), L = 10, R = W - 10, T = 44, B = 210;
    var mx = Math.max.apply(null, rows.map(function (r) { return r.episodes_up; }));
    var y = lin(0, mx, B, T), band = (R - L) / rows.length, bw = Math.min(34, band / 3);
    el("line", { x1: L, x2: R, y1: B, y2: B, "class": "base" }, svg);
    rows.forEach(function (r, i) {
      var cx = L + band * (i + 0.5), up = r.episodes_up, dn = r.episodes - r.episodes_up;
      [[up, "f-oxide", -1], [dn, "f-pine", 1]].forEach(function (s) {
        var x0 = cx + (s[2] < 0 ? -bw - 2 : 2);
        if (s[0] > 0) el("rect", { x: x0, y: y(s[0]), width: bw, height: B - y(s[0]), "class": s[1] }, svg);
        el("text", { x: x0 + bw / 2, y: y(s[0]) - 6, "text-anchor": "middle", "font-size": 12, "class": "lab" }, svg, s[0]);
      });
      el("text", { x: cx, y: B + 20, "text-anchor": "middle", "font-size": 12 }, svg, r.year);
    });
    el("rect", { x: L, y: 0, width: 12, height: 12, "class": "f-oxide" }, svg);
    el("text", { x: L + 18, y: 11, "font-size": 12 }, svg, "increases");
    el("rect", { x: L + 100, y: 0, width: 12, height: 12, "class": "f-pine" }, svg);
    el("text", { x: L + 118, y: 11, "font-size": 12 }, svg, "cuts");
  }

  /* ---------- Margin ---------- */
  var marginMode = "posted";
  function drawMargin() {
    var svg = document.getElementById("margin"); clear(svg);
    var m = D.margin, n = m.length, W = size(svg, 340), L = 40, R = W - 96, T = 14, B = 300;
    var hi = Math.max.apply(null, m.map(function (r) { return r[1]; })) * 1.05;
    var x = lin(0, n - 1, L, R), y = lin(0, hi, B, T);
    yAxis(svg, y, niceTicks(0, hi, 6), L, R);
    var g = el("g", { "class": "axis" }, svg);
    m.forEach(function (r, i) { if (r[0].slice(5) === "01" && (W >= 600 || +r[0].slice(0, 4) % 2 === 0)) el("text", { x: x(i), y: B + 22, "text-anchor": "middle" }, g, r[0].slice(0, 4)); });
    function area(lowF, highF, cls, op) {
      var top = m.map(function (r, i) { return x(i).toFixed(1) + "," + y(highF(r)).toFixed(1); });
      var bot = m.map(function (r, i) { return x(i).toFixed(1) + "," + y(lowF(r)).toFixed(1); }).reverse();
      el("path", { d: "M" + top.join("L") + "L" + bot.join("L") + "Z", "class": cls, opacity: op }, svg);
    }
    var net = marginMode === "net", op = net ? 0.35 : 0.9;
    area(function () { return 0; }, function (r) { return r[2]; }, "f-pine", op);
    area(function (r) { return r[2]; }, function (r) { return r[2] + r[3]; }, "f-gray", op * 0.8);
    area(function (r) { return r[2] + r[3]; }, function (r) { return r[1]; }, "f-oxide", op);
    var last = m[n - 1];
    el("text", { x: R + 8, y: y(last[2] / 2) + 4, "class": "lab" }, svg, "import cost");
    el("text", { x: R + 8, y: y(last[2] + last[3] / 2) + 4, "class": "lab" }, svg, "duty");
    el("text", { x: R + 8, y: y((last[2] + last[3] + last[1]) / 2) + 4, "class": "lab" }, svg, "margin");
    var monthIdx = {}; m.forEach(function (r, i) { monthIdx[r[0]] = i; });
    var pts = [];
    if (net) {
      D.net.forEach(function (r) {
        var i = monthIdx[r[0].slice(0, 7)]; if (i == null) return;
        var frac = (+r[0].slice(8, 10) - 1) / 30, xi = x(Math.min(n - 1, i + frac));
        pts.push([xi, r]);
        el("circle", { cx: xi, cy: y(r[2]), r: 4, "class": "f-oxide dot" }, svg);
      });
      el("text", { x: L + 8, y: T + 12, "font-size": 12 }, svg, "dots: average price after walk-in discount, on archived days");
    }
    var cur = el("line", { y1: T, y2: B, "class": "cursor" }, svg), read = document.getElementById("margin-read");
    if (!net) {
      cursorize(svg, n, function (i) { return x(i); }, function (i) {
        var r = m[i]; cur.setAttribute("x1", x(i)); cur.setAttribute("x2", x(i));
        read.textContent = r[0] + "   posted " + f2(r[1]) + "   import " + f2(r[2]) + "   duty " + f2(r[3]) + "   margin " + f2(r[4]) + "  (HK$ per litre)";
      });
    } else {
      cursorize(svg, pts.length, function (i) { return pts[i][0]; }, function (i) {
        var r = pts[i][1]; cur.setAttribute("x1", pts[i][0]); cur.setAttribute("x2", pts[i][0]);
        read.textContent = fmtDate(r[0]) + "   posted " + f2(r[1]) + "   after walk-in discount " + f2(r[2]) + "   import " + f2(r[4]) + "   margin on that price " + f2(r[2] - 6.06 - r[4]);
      });
    }
    document.getElementById("margin-cap").textContent = net
      ? "Average net price across the five brands on the 119 days the Consumer Council comparison page was archived (Internet Archive). Card and loyalty discounts are not included."
      : "Import cost: Census and Statistics Department, monthly unit value of unleaded petrol imports. Duty: HK$6.06 a litre.";
  }
  function initMargin() {
    document.querySelectorAll("#s3 ~ .chart-head .seg-b, section[aria-labelledby=s3] .seg-b").forEach(function (b) {
      b.addEventListener("click", function () {
        document.querySelectorAll("section[aria-labelledby=s3] .seg-b").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true"); marginMode = b.getAttribute("data-mode"); drawMargin();
      });
    });
    drawMargin();
  }

  /* ---------- Pass-through ---------- */
  function drawPT(mk) {
    var svg = document.getElementById("pt"); clear(svg);
    var s = D.passthrough[mk], n = s.rise.length, W = size(svg, 320), L = 48, R = W - 80, T = 14, B = 280;
    var all = s.rise.concat(s.fall), hi = Math.max(1.2, Math.max.apply(null, all) + 0.1), lo = Math.min(0, Math.min.apply(null, all));
    var x = lin(0, n - 1, L, R), y = lin(lo, hi, B, T);
    yAxis(svg, y, niceTicks(lo, hi, 6), L, R, function (t) { return Math.round(t * 100) + "%"; });
    el("line", { x1: L, x2: R, y1: y(1), y2: y(1), "class": "base", "stroke-dasharray": "2 3" }, svg);
    el("text", { x: L + 6, y: y(1) - 6, "font-size": 12 }, svg, "full pass-through");
    for (var w = 0; w < n; w += 2) el("text", { x: x(w), y: B + 22, "text-anchor": "middle", "font-size": 12 }, svg, w === 0 ? "week 0" : w);
    function line(arr, cls) { el("path", { d: "M" + arr.map(function (v, i) { return x(i).toFixed(1) + "," + y(v).toFixed(1); }).join("L"), "class": cls }, svg); }
    line(s.fall, "s-pine"); line(s.rise, "s-oxide");
    var dy = s.rise[n - 1] > s.fall[n - 1] ? [-8, 16] : [16, -8];
    el("text", { x: R + 8, y: y(s.rise[n - 1]) + dy[0] + 4, "class": "lab" }, svg, "cost rise");
    el("text", { x: R + 8, y: y(s.fall[n - 1]) + dy[1] + 4, "class": "lab" }, svg, "cost fall");
    var ps = D.passthroughSummary[mk];
    document.getElementById("pt-stat").textContent = mk + ": week 0, " + Math.round(ps.week0_rise * 100) + "% of a rise against " + Math.round(ps.week0_fall * 100) +
      "% of a fall. Test that rises and falls pass through equally over weeks 0 and 1: p = " + ps.asym_weeks01_p.toFixed(3) + " (" + ps.n_weeks + " weeks).";
  }

  /* ---------- Perth band ---------- */
  function drawPerth(endIso) {
    var svg = document.getElementById("perth"); clear(svg);
    var end = perthDates.indexOf(endIso); if (end < 0) end = perthDates.length - 1;
    var start = Math.max(0, end - 119), rows = D.perth.slice(start, end + 1), n = rows.length;
    var W = size(svg, 320), L = 40, R = W - 70, T = 14, B = 280;
    var lo = Math.min.apply(null, rows.map(function (r) { return r[3]; })) - 5, hi = Math.max.apply(null, rows.map(function (r) { return r[7]; })) + 5;
    var x = lin(0, n - 1, L, R), y = lin(lo, hi, B, T);
    yAxis(svg, y, niceTicks(lo, hi, 5), L, R);
    rows.forEach(function (r, i) { if (r[0].slice(8) === "01") el("text", { x: x(i), y: B + 22, "text-anchor": "middle", "font-size": 12 }, svg, MON[+r[0].slice(5, 7) - 1] + " " + r[0].slice(2, 4)); });
    var top = rows.map(function (r, i) { return x(i).toFixed(1) + "," + y(r[7]).toFixed(1); });
    var bot = rows.map(function (r, i) { return x(i).toFixed(1) + "," + y(r[3]).toFixed(1); }).reverse();
    el("path", { d: "M" + top.join("L") + "L" + bot.join("L") + "Z", "class": "f-band" }, svg);
    el("path", { d: "M" + rows.map(function (r, i) { return x(i).toFixed(1) + "," + y(r[5]).toFixed(1); }).join("L"), "class": "s-oxide" }, svg);
    el("text", { x: R + 8, y: y(rows[n - 1][5]) + 4, "class": "lab" }, svg, "median");
    el("text", { x: R + 8, y: y(rows[n - 1][7]) + 4, "font-size": 12 }, svg, "90th pct");
    el("text", { x: R + 8, y: y(rows[n - 1][3]) + 4, "font-size": 12 }, svg, "10th pct");
    var cur = el("line", { y1: T, y2: B, "class": "cursor" }, svg), read = document.getElementById("perth-read");
    cursorize(svg, n, function (i) { return x(i); }, function (i) {
      var r = rows[i]; cur.setAttribute("x1", x(i)); cur.setAttribute("x2", x(i));
      var wd = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][new Date(r[0] + "T00:00:00Z").getUTCDay()];
      read.textContent = wd + " " + fmtDate(r[0]) + "   median " + r[5].toFixed(1) + "   10th to 90th pct " + r[3].toFixed(1) + " to " + r[7].toFixed(1) + "   cheapest " + r[2].toFixed(1) + "   dearest " + r[8].toFixed(1) + "  (cents per litre)";
    });
  }

  fetch("assets/data.json").then(function (r) { return r.json(); }).then(function (data) {
    D = data; BR = D.brands; dayCount = D.hkDays; hkStart = D.hkStart;
    D.perth.forEach(function (r) { perthByDate[r[0]] = r; perthDates.push(r[0]); });
    initBoard(); initSteps(); drawLags(); drawYears(); initMargin();
    var mk = Object.keys(D.passthrough);
    var curPT = mk[0];
    segButtons(document.getElementById("pt-seg"), mk, mk[0], function (m) { curPT = m; drawPT(m); }); drawPT(mk[0]);
    var lastW = window.innerWidth, t;
    window.addEventListener("resize", function () {
      clearTimeout(t);
      t = setTimeout(function () {
        if (Math.abs(window.innerWidth - lastW) < 20) return;
        lastW = window.innerWidth;
        drawBoard(board.day); drawLags(); drawYears(); drawMargin(); drawPT(curPT);
        var on = document.querySelector("#year-seg [aria-pressed=true]"); drawSteps(on ? on.textContent : "2026");
      }, 150);
    });
  });
})();
