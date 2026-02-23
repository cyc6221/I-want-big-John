---
layout: page
title: 威力彩第一區抽號
permalink: /recommender_638/
---

<div class="card" style="padding:1rem;">
  <h2 style="margin-top:0;">威力彩第一區：1–38 抽 6</h2>

  <div style="display:grid; gap: .9rem; max-width: 760px;">
    <!-- 必選 -->
    <section>
      <div style="display:flex; align-items:end; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
        <div>
          <h3 style="margin:.2rem 0;">必選號碼</h3>
          <div style="opacity:.8; font-size:.9rem;">點球加入/取消必選（最多 6 個）</div>
        </div>
        <button type="button" class="btn" id="clearMust" style="height: fit-content;">清空必選</button>
      </div>

      <div id="mustRow" class="ball-row" aria-label="必選號碼球"></div>

      <input id="mustNums" type="text" placeholder="例如：3, 8, 17"
        style="width:100%; padding:.55rem; margin-top:.25rem;">
    </section>

    <!-- 排除 -->
    <section>
      <div style="display:flex; align-items:end; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
        <div>
          <h3 style="margin:.2rem 0;">排除號碼</h3>
          <div style="opacity:.8; font-size:.9rem;">點球加入/取消排除（與必選互斥）</div>
        </div>
        <button type="button" class="btn" id="clearExclude" style="height: fit-content;">清空排除</button>
      </div>

      <div id="excludeRow" class="ball-row" aria-label="排除號碼球"></div>

      <input id="excludeNums" type="text" placeholder="例如：1, 2, 38"
        style="width:100%; padding:.55rem; margin-top:.25rem;">
    </section>

    <!-- 連號限制 -->
    <section>
      <h3 style="margin:.2rem 0;">連號限制（最大允許連號長度）</h3>
      <select id="maxRun" style="width:100%; padding:.55rem; margin-top:.25rem;">
        <option value="6">允許到 6 連號（不限制）</option>
        <option value="5">不允許 6 連號</option>
        <option value="4">不允許 5–6 連號</option>
        <option value="3">不允許 4–6 連號</option>
        <option value="2">不允許 3–6 連號（最多只允許 2 連號）</option>
        <option value="1">不允許 2–6 連號（完全不允許連號）</option>
      </select>
      <div style="font-size:.9rem; opacity:.8; margin-top:.35rem;">
        例：最多允許 2 連號 → 允許 7,8 但不允許 7,8,9
      </div>
    </section>

    <div style="display:flex; gap:.6rem; flex-wrap:wrap; align-items:center;">
      <button id="drawBtn" class="btn btn--primary">抽一組</button>
      <div id="result" style="font-size:1.25rem; font-weight:700;"></div>
    </div>

    <div id="error" style="color:#c00;"></div>
  </div>
</div>

<script>
(() => {
  const MIN = 1, MAX = 38, PICK = 6;

  // ---------- utils ----------
  const pad2 = n => String(n).padStart(2, "0");

  function parseNums(input) {
    if (!input.trim()) return [];
    const arr = input.split(",")
      .map(s => Number(s.trim()))
      .filter(n => Number.isInteger(n) && n >= MIN && n <= MAX);
    return Array.from(new Set(arr)).sort((a,b)=>a-b);
  }

  function setToCsv(set) {
    return Array.from(set).sort((a,b)=>a-b).join(", ");
  }

  function runLengthMax(sortedArr) {
    if (sortedArr.length === 0) return 0;
    let best = 1, cur = 1;
    for (let i = 1; i < sortedArr.length; i++) {
      if (sortedArr[i] === sortedArr[i-1] + 1) cur++;
      else cur = 1;
      if (cur > best) best = cur;
    }
    return best;
  }

  // ---------- state ----------
  const mustSet = new Set();
  const excludeSet = new Set();

  // ---------- dom ----------
  const $mustRow = document.getElementById("mustRow");
  const $excludeRow = document.getElementById("excludeRow");
  const $mustInput = document.getElementById("mustNums");
  const $excludeInput = document.getElementById("excludeNums");
  const $maxRun = document.getElementById("maxRun");
  const $btn = document.getElementById("drawBtn");
  const $result = document.getElementById("result");
  const $error = document.getElementById("error");
  const $clearMust = document.getElementById("clearMust");
  const $clearExclude = document.getElementById("clearExclude");

  // 重要：若抓不到容器，直接報錯（避免默默失敗）
  if (!$mustRow || !$excludeRow) {
    if ($error) $error.textContent = "找不到 mustRow / excludeRow，請確認 HTML 有 <div id='mustRow'> 與 <div id='excludeRow'>。";
    return;
  }

  // ---------- render balls ----------
  function makeBall(n) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "ball";
    b.textContent = pad2(n);
    b.dataset.n = String(n);
    b.setAttribute("aria-pressed", "false");
    return b;
  }

  const mustBalls = new Map();
  const excludeBalls = new Map();

  for (let n = MIN; n <= MAX; n++) {
    const mb = makeBall(n);
    const eb = makeBall(n);

    // click: toggle must
    mb.addEventListener("click", () => {
      $error.textContent = "";

      // 互斥：若在排除，先移除排除
      if (excludeSet.has(n)) {
        excludeSet.delete(n);
        updateBallState(n);
      }

      if (mustSet.has(n)) {
        mustSet.delete(n);
      } else {
        if (mustSet.size >= PICK) {
          $error.textContent = `必選最多只能 ${PICK} 個。`;
          return;
        }
        mustSet.add(n);
      }

      syncInputs();
      updateBallState(n);
    });

    // click: toggle exclude
    eb.addEventListener("click", () => {
      $error.textContent = "";

      // 互斥：若在必選，先移除必選
      if (mustSet.has(n)) {
        mustSet.delete(n);
        updateBallState(n);
      }

      if (excludeSet.has(n)) excludeSet.delete(n);
      else excludeSet.add(n);

      syncInputs();
      updateBallState(n);
    });

    $mustRow.appendChild(mb);
    $excludeRow.appendChild(eb);
    mustBalls.set(n, mb);
    excludeBalls.set(n, eb);
  }

  function updateBallState(n) {
    const mb = mustBalls.get(n);
    const eb = excludeBalls.get(n);
    if (!mb || !eb) return;

    const isMust = mustSet.has(n);
    const isEx = excludeSet.has(n);

    mb.classList.toggle("ball--pick", isMust);
    mb.setAttribute("aria-pressed", String(isMust));

    eb.classList.toggle("ball--red", isEx);
    eb.setAttribute("aria-pressed", String(isEx));

    // 互斥視覺：另一區淡掉
    eb.style.opacity = isMust ? "0.35" : "1";
    mb.style.opacity = isEx ? "0.35" : "1";
  }

  function syncInputs() {
    $mustInput.value = setToCsv(mustSet);
    $excludeInput.value = setToCsv(excludeSet);
  }

  function refreshAllBalls() {
    for (let n = MIN; n <= MAX; n++) updateBallState(n);
  }

  // input 手動改：change 時同步回球（維持互斥 + 必選最多 6）
  $mustInput.addEventListener("change", () => {
    const arr = parseNums($mustInput.value);
    mustSet.clear();
    for (const n of arr.slice(0, PICK)) {
      if (!excludeSet.has(n)) mustSet.add(n);
    }
    syncInputs();
    refreshAllBalls();
  });

  $excludeInput.addEventListener("change", () => {
    const arr = parseNums($excludeInput.value);
    excludeSet.clear();
    for (const n of arr) {
      if (!mustSet.has(n)) excludeSet.add(n);
    }
    syncInputs();
    refreshAllBalls();
  });

  $clearMust.addEventListener("click", () => {
    mustSet.clear();
    syncInputs();
    refreshAllBalls();
  });

  $clearExclude.addEventListener("click", () => {
    excludeSet.clear();
    syncInputs();
    refreshAllBalls();
  });

  // ---------- draw logic ----------
  function drawWithConstraints({ maxRunAllowed }) {
    if (mustSet.size > PICK) throw new Error(`必選 ${mustSet.size} 個，但只抽 ${PICK} 個`);

    const available = [];
    for (let n = MIN; n <= MAX; n++) {
      if (!excludeSet.has(n)) available.push(n);
    }
    if (available.length < PICK) throw new Error(`排除太多：剩下 ${available.length} 個，不足以抽 ${PICK} 個`);

    const base = Array.from(mustSet);
    const pool = available.filter(n => !mustSet.has(n));
    const MAX_TRIES = 6000;

    for (let t = 0; t < MAX_TRIES; t++) {
      const chosen = new Set(base);
      while (chosen.size < PICK) {
        const n = pool[Math.floor(Math.random() * pool.length)];
        chosen.add(n);
      }
      const combo = Array.from(chosen).sort((a,b)=>a-b);
      if (runLengthMax(combo) > maxRunAllowed) continue;
      return combo;
    }
    throw new Error("條件太嚴格，抽不到符合規則的組合（放寬連號或減少排除/必選）。");
  }

  $btn.addEventListener("click", () => {
    $error.textContent = "";
    $result.textContent = "";
    try {
      const maxRunAllowed = Number($maxRun.value);
      const combo = drawWithConstraints({ maxRunAllowed });
      $result.textContent = "🎲 " + combo.map(pad2).join("  ");
    } catch (e) {
      $error.textContent = e.message || String(e);
    }
  });

  // init
  syncInputs();
  refreshAllBalls();
})();
</script>