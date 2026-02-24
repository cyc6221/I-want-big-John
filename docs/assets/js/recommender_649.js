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

  function runLengthMax(nums) {
    // 環狀連號：38 與 1 視為相連
    // nums 可為排序或未排序都沒差
    const set = new Set(nums);
    if (set.size === 0) return 0;

    let best = 1;

    for (const n of set) {
        const prev = (n === MIN) ? MAX : (n - 1);
        // 只有「前一個不在集合」才當作一段連號的起點，避免重複計算
        if (set.has(prev)) continue;

        let cur = n;
        let len = 1;

        while (true) {
        const nxt = (cur === MAX) ? MIN : (cur + 1);
        if (!set.has(nxt)) break;
        len++;
        cur = nxt;
        // 保護：最多不會超過集合大小
        if (len >= set.size) break;
        }

        if (len > best) best = len;
    }

    return best;
  }

  // 讀取 runGrid 每一列目前選到的 mode：any / must / ban
  function readRunRules($runGrid) {
    const rules = {};
    const rows = $runGrid.querySelectorAll(".run-row");
    rows.forEach(row => {
      const n = Number(row.dataset.run);
      const active = row.querySelector(".seg-btn.is-active");
      rules[n] = active ? active.dataset.mode : "any";
    });
    return rules;
  }

  function isContradictoryRunRules(rules) {
    // must 要求 maxRun >= mustMin
    // ban  要求 maxRun <= banMaxAllowed (banN - 1)
    const mustNs = Object.entries(rules).filter(([,m])=>m==="must").map(([n])=>Number(n));
    const banNs  = Object.entries(rules).filter(([,m])=>m==="ban").map(([n])=>Number(n));

    const mustMin = mustNs.length ? Math.max(...mustNs) : 0;
    const banMaxAllowed = banNs.length ? (Math.min(...banNs) - 1) : 999;

    return mustMin > banMaxAllowed;
  }

  function passRunRules(combo, runRules) {
    const mx = runLengthMax(combo);

    // ban：禁止 N 連號以上 => mx < N
    for (const [nStr, mode] of Object.entries(runRules)) {
      const n = Number(nStr);
      if (mode === "ban" && mx >= n) return false;
    }

    // must：至少要有 N 連號 => mx >= N
    for (const [nStr, mode] of Object.entries(runRules)) {
      const n = Number(nStr);
      if (mode === "must" && mx < n) return false;
    }

    return true;
  }

  // ---------- state ----------
  const mustSet = new Set();
  const excludeSet = new Set();

  // ---------- dom ----------
  const $mustRow = document.getElementById("mustRow");
  const $excludeRow = document.getElementById("excludeRow");
  const $mustInput = document.getElementById("mustNums");
  const $excludeInput = document.getElementById("excludeNums");
  const $btn = document.getElementById("drawBtn");
  const $resultRow = document.getElementById("result");
  const $error = document.getElementById("error");
  const $clearMust = document.getElementById("clearMust");
  const $clearExclude = document.getElementById("clearExclude");
  const $runGrid = document.getElementById("runGrid"); // 新：連號按鈕區

  // 基本防呆
  if (!$mustRow || !$excludeRow) {
    if ($error) $error.textContent = "找不到 mustRow / excludeRow，請確認 HTML 有 <div id='mustRow'> 與 <div id='excludeRow'>。";
    return;
  }
  if (!$resultRow) {
    if ($error) $error.textContent = "找不到 result 容器，請確認 HTML 有 <div id='result'>。";
    return;
  }
  if (!$runGrid) {
    if ($error) $error.textContent = "找不到 runGrid（連號按鈕區），請把 HTML 的連號區改成按鈕版並包含 <div id='runGrid'>。";
    return;
  }

  // ---------- runGrid button behavior ----------
  // 同一列只允許一個 is-active
  $runGrid.addEventListener("click", (e) => {
    const btn = e.target.closest(".seg-btn");
    if (!btn) return;
    const row = btn.closest(".run-row");
    if (!row) return;

    row.querySelectorAll(".seg-btn").forEach(b => b.classList.remove("is-active"));
    btn.classList.add("is-active");
  });

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

    // 必選：用 ball--pick（你可在 SCSS 改成更明顯的藍/紫）
    mb.classList.toggle("ball--pick", isMust);
    mb.setAttribute("aria-pressed", String(isMust));

    // 排除：紅色
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
  function drawWithConstraints({ runRules }) {
    if (mustSet.size > PICK) throw new Error(`必選 ${mustSet.size} 個，但只抽 ${PICK} 個`);

    // 如果「一定要 6 連號」，直接生成（環狀）
    if (runRules[6] === "must") {
        const candidates = [];

        // 環狀：起點可以是 1..38
        for (let start = MIN; start <= MAX; start++) {
        const combo = [];
        for (let k = 0; k < PICK; k++) {
            const val = ((start - 1 + k) % MAX) + 1; // wrap
            combo.push(val);
        }

        // 必選必須全部包含
        let ok = true;
        for (const m of mustSet) {
            if (!combo.includes(m)) { ok = false; break; }
        }
        if (!ok) continue;

        // 排除不得出現
        for (const x of excludeSet) {
            if (combo.includes(x)) { ok = false; break; }
        }
        if (!ok) continue;

        // 其他 runRules（2~5）也要過
        if (!passRunRules(combo, runRules)) continue;

        candidates.push(combo);
        }

        if (candidates.length === 0) {
        throw new Error("你選了『一定要 6 連號』，但必選/排除/其他連號限制讓它無解（請調整條件）。");
        }

        // 從可行候選中隨機挑一組
        const pick = candidates[Math.floor(Math.random() * candidates.length)];

        // 顯示用排序（不影響環狀連號判定，因為 runLengthMax 用 set 算）
        return pick.slice().sort((a,b)=>a-b);
    }

    // ---- 其他情況：原本的隨機抽 + 過濾 ----
    const available = [];
    for (let n = MIN; n <= MAX; n++) {
        if (!excludeSet.has(n)) available.push(n);
    }
    if (available.length < PICK) throw new Error(`排除太多：剩下 ${available.length} 個，不足以抽 ${PICK} 個`);

    const base = Array.from(mustSet);
    const pool = available.filter(n => !mustSet.has(n));
    const MAX_TRIES = 8000;

    for (let t = 0; t < MAX_TRIES; t++) {
        const chosen = new Set(base);
        while (chosen.size < PICK) {
        const n = pool[Math.floor(Math.random() * pool.length)];
        chosen.add(n);
        }
        const combo = Array.from(chosen).sort((a,b)=>a-b);

        if (!passRunRules(combo, runRules)) continue;
        return combo;
    }

    throw new Error("條件太嚴格，抽不到符合規則的組合（放寬連號限制或減少排除/必選）。");
  }

  function renderResultBalls(nums) {
    $resultRow.innerHTML = "";
    for (const n of nums) {
      const b = document.createElement("span");
      b.className = "ball";
      b.textContent = pad2(n);
      $resultRow.appendChild(b);
    }
  }

  $btn.addEventListener("click", () => {
    $error.textContent = "";
    $resultRow.innerHTML = "";

    try {
      const runRules = readRunRules($runGrid);

      if (isContradictoryRunRules(runRules)) {
        throw new Error("連號限制互相矛盾：『一定要』與『一定不要』設定導致無解，請調整。");
      }

      const combo = drawWithConstraints({ runRules });
      renderResultBalls(combo);
      
      if ($wish) $wish.textContent = "祝你中大獎 🎉";
    } catch (e) {
      $error.textContent = e.message || String(e);
    }
  });

  // init
  syncInputs();
  refreshAllBalls();
})();
