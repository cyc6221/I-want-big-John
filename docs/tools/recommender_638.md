---
layout: page
title: 威力彩第一區抽號
permalink: /recommender_638/
---

<div class="card" style="padding:1rem;">
  <h2 style="margin-top:0;">威力彩第一區：1–38 抽 6</h2>

  <div style="display:grid; gap: .75rem; max-width: 560px;">
    <label>
      必選號碼（逗號分隔，例如：3, 8, 17）
      <input id="mustNums" type="text" placeholder="例如：3, 8, 17"
        style="width:100%; padding:.55rem; margin-top:.25rem;">
    </label>
    <!--  -->
    <label>
      排除號碼（逗號分隔，例如：1, 2, 38）
      <input id="excludeNums" type="text" placeholder="例如：1, 2, 38"
        style="width:100%; padding:.55rem; margin-top:.25rem;">
    </label>
    <!--  -->
    <label>
      連號限制（最大允許連號長度）
      <select id="maxRun" style="width:100%; padding:.55rem; margin-top:.25rem;">
        <option value="6">允許到 6 連號（不限制）</option>
        <option value="5">不允許 6 連號</option>
        <option value="4">不允許 5–6 連號</option>
        <option value="3">不允許 4–6 連號</option>
        <option value="2">不允許 3–6 連號（最多只允許 2 連號）</option>
        <option value="1">不允許 2–6 連號（完全不允許連號）</option>
      </select>
      <div style="font-size:.9rem; opacity:.8; margin-top:.25rem;">
        例：選「最多只允許 2 連號」表示允許 7,8 但不允許 7,8,9。
      </div>
    </label>
    <!--  -->
    <button id="drawBtn" class="btn btn--primary" style="width: fit-content;">
      抽一組
    </button>
    <!--  -->
    <div id="result" style="font-size:1.25rem; font-weight:600;"></div>
    <div id="error" style="color:#c00;"></div>
  </div>
</div>

<script>
(() => {
  const MIN = 1, MAX = 38, PICK = 6;

  function parseNums(input) {
    if (!input.trim()) return [];
    const arr = input.split(",")
      .map(s => Number(s.trim()))
      .filter(n => Number.isInteger(n) && n >= MIN && n <= MAX);
    // 去重
    return Array.from(new Set(arr)).sort((a,b)=>a-b);
  }

  function runLengthMax(sortedArr) {
    // 回傳最大連號長度，例如 [2,3,4,9,12,13] => 最大=3（2,3,4）
    if (sortedArr.length === 0) return 0;
    let best = 1, cur = 1;
    for (let i = 1; i < sortedArr.length; i++) {
      if (sortedArr[i] === sortedArr[i-1] + 1) cur++;
      else cur = 1;
      if (cur > best) best = cur;
    }
    return best;
  }

  function drawWithConstraints({ must, exclude, maxRunAllowed }) {
    // 基本檢查
    const mustSet = new Set(must);
    const excludeSet = new Set(exclude);

    // 必選與排除衝突
    for (const n of mustSet) {
      if (excludeSet.has(n)) {
        throw new Error(`必選與排除衝突：${n} 同時被設定為必選與排除`);
      }
    }

    // 必選數量超過要抽的數量
    if (mustSet.size > PICK) {
      throw new Error(`必選號碼太多：必選 ${mustSet.size} 個，但只抽 ${PICK} 個`);
    }

    // 可用數量不足
    const available = [];
    for (let n = MIN; n <= MAX; n++) {
      if (!excludeSet.has(n)) available.push(n);
    }
    if (available.length < PICK) {
      throw new Error(`排除太多：剩下 ${available.length} 個可用，不足以抽 ${PICK} 個`);
    }

    // 先把必選放進去
    const base = Array.from(mustSet);
    const need = PICK - base.length;

    // 候選池：可用且不是必選
    const pool = available.filter(n => !mustSet.has(n));

    // 反覆嘗試直到符合連號規則
    const MAX_TRIES = 5000;
    for (let t = 0; t < MAX_TRIES; t++) {
      // 隨機抽 need 個（不重複）
      const chosen = new Set(base);
      while (chosen.size < PICK) {
        const n = pool[Math.floor(Math.random() * pool.length)];
        chosen.add(n);
      }
      const combo = Array.from(chosen).sort((a,b)=>a-b);

      // 檢查最大連號長度
      const mx = runLengthMax(combo);
      if (mx > maxRunAllowed) continue;

      return combo;
    }

    throw new Error("條件太嚴格，嘗試多次仍抽不到符合規則的組合（請放寬連號限制或減少排除/必選）。");
  }

  const $must = document.getElementById("mustNums");
  const $exclude = document.getElementById("excludeNums");
  const $maxRun = document.getElementById("maxRun");
  const $btn = document.getElementById("drawBtn");
  const $result = document.getElementById("result");
  const $error = document.getElementById("error");

  $btn.addEventListener("click", () => {
    $error.textContent = "";
    $result.textContent = "";

    try {
      const must = parseNums($must.value);
      const exclude = parseNums($exclude.value);
      const maxRunAllowed = Number($maxRun.value);

      const combo = drawWithConstraints({ must, exclude, maxRunAllowed });
      $result.textContent = "🎲 " + combo.map(n => String(n).padStart(2,"0")).join("  ");
    } catch (e) {
      $error.textContent = e.message || String(e);
    }
  });
})();
</script>
