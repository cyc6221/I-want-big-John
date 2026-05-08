# Note 2

可以，這個方向可以整理成一類模型：

> **Gap-based / Mean-reversion model**
> 也就是根據「多久沒出現」與「目前出現次數是否低於平均」來調整每個數字的分數。

但要先提醒一件很重要的事：

## 1. 這個想法不是一定錯，但要避免賭徒謬誤

你說的概念是：

> 數字 1 很久沒出現，所以之後出現機率應該提高，因為長期分布會往平均靠近。

這個想法只有在資料產生機制有「均值回歸」或「平衡機制」時才成立。

如果每期真的是獨立隨機抽樣，那麼即使數字 1 已經很久沒出現，下期出現機率仍然是：

\[
P(y_{t+1,1}=1 \mid \text{數字 1 已經很久沒出現}) = \frac{6}{38}.
\]

也就是說，獨立隨機模型沒有記憶性。

但是，如果真實資料不是完全獨立隨機，而是存在某種「長期頻率修正」現象，那你的方向就可以建模。

---

## 2. Gap feature：距離上次出現多久

對每個數字 \(i\)，定義它在時間 \(t\) 的 gap：

\[
G_i(t)=t-\max\{s\leq t:y_{s,i}=1\}.
\]

如果數字 \(i\) 剛在第 \(t\) 期出現，則：

\[
G_i(t)=0.
\]

如果它已經連續 10 期沒出現，則：

\[
G_i(t)=10.
\]

你的直覺可以寫成：

\[
G_i(t)\text{ 越大}
\quad\Rightarrow\quad
P(y_{t+1,i}=1\mid \mathcal{F}_t)\text{ 越大}.
\]

這就是 **gap-based model**。

---

## 3. Gap hazard model

可以定義一個 hazard function：

\[
h(g)=P(y_{t+1,i}=1\mid G_i(t)=g).
\]

意思是：

> 如果某個數字已經 \(g\) 期沒出現，那它下一期出現的機率是多少？

如果資料真的有「久沒出現就更容易出現」的現象，那麼應該會看到：

\[
h(0)<h(1)<h(2)<\cdots
\]

或至少整體有上升趨勢。

### 估計方式

用歷史資料估計：

\[
\widehat{h}(g) = \frac{
\sum_{t,i}\mathbf{1}\{G_i(t)=g\}y_{t+1,i}
}{
\sum_{t,i}\mathbf{1}\{G_i(t)=g\}
}.
\]

分子是：

> gap 等於 \(g\) 時，下一期真的出現的次數。

分母是：

> gap 等於 \(g\) 的總觀測次數。

因為資料可能不多，可以加平滑：

\[
\widehat{h}(g) = \frac{
\alpha p_0+
\sum_{t,i}\mathbf{1}\{G_i(t)=g\}y_{t+1,i}
}{
\alpha+
\sum_{t,i}\mathbf{1}\{G_i(t)=g\}
},
\]

其中

\[
p_0=\frac{6}{38}.
\]

\(\alpha\) 越大，模型越保守，越靠近隨機基準。

---

## 4. Gap score model

實作上不一定要直接估機率，也可以先設計分數。

例如：

\[
s_i(t)=\beta_0+\beta_1\log(1+G_i(t)).
\]

如果：

\[
\beta_1>0,
\]

代表 gap 越大，數字 \(i\) 的分數越高。

最後預測：

\[
\widehat{S}_{t+1} = \operatorname{TopK}_6(s_1(t),\dots,s_{38}(t)).
\]

這就是最簡單的「久未出現優先」模型。

---

## 5. Frequency deficit：低於平均的程度

你說「分布會靠近平均分布」，這個概念其實比 gap 更接近 **frequency deficit**。

第 \(t\) 期以前，每個數字理論上期望出現次數是：

\[
\mu_t=\frac{6t}{38}.
\]

令數字 \(i\) 的累積出現次數為：

\[
c_i(t)=\sum_{s=1}^{t}y_{s,i}.
\]

定義 deficit：

\[
D_i(t)=\mu_t-c_i(t).
\]

如果：

\[
D_i(t)>0,
\]

表示數字 \(i\) 目前出現次數低於平均。

如果：

\[
D_i(t)<0,
\]

表示數字 \(i\) 目前出現次數高於平均。

你的均值回歸想法可以寫成：

\[
D_i(t)\text{ 越大}
\quad\Rightarrow\quad
P(y_{t+1,i}=1\mid \mathcal{F}_t)\text{ 越大}.
\]

---

## 6. Gap + deficit 聯合模型

比較完整的模型可以同時使用：

1. 距離上次出現多久。
2. 累積出現次數是否低於平均。
3. 近期是否過熱或過冷。

定義分數：

\[
s_i(t) = \beta_0
+
\beta_1\log(1+G_i(t))
+
\beta_2D_i(t)
+
\beta_3R_i(t),
\]

其中：

\[
G_i(t)
\]

是 gap，

\[
D_i(t)=\frac{6t}{38}-c_i(t)
\]

是低於平均的程度，

\[
R_i(t)
\]

可以是近期頻率特徵，例如：

\[
R_i(t) = \frac{1}{w}\sum_{s=t-w+1}^{t}y_{s,i}.
\]

如果你相信「近期太常出現的數字會冷卻」，那可以設：

\[
\beta_3<0.
\]

如果你相信「近期熱號會延續」，那可以設：

\[
\beta_3>0.
\]

---

## 7. 更標準的固定大小集合模型

因為每次一定只能選 6 個，所以不要單獨把 38 個數字看成彼此獨立。

比較好的建模方式是：

\[
P(S_{t+1}=S\mid \mathcal{F}_t) = \frac{
\exp\left(\sum_{i\in S}s_i(t)\right)
}{
\sum_{A\subset\Omega,\ |A|=6}
\exp\left(\sum_{j\in A}s_j(t)\right)
},
\]

其中：

\[
|S|=6.
\]

這個模型會自動滿足：

\[
|S_{t+1}|=6.
\]

你的分數可以設成：

\[
s_i(t) = \beta_1\log(1+G_i(t))
+
\beta_2D_i(t)
+
\beta_3R_i(t).
\]

預測時：

\[
\widehat{S}_{t+1} = \arg\max_{|S|=6}
\sum_{i\in S}s_i(t).
\]

這等價於選分數最高的 6 個：

\[
\widehat{S}_{t+1} = \operatorname{TopK}_6(s_1(t),\dots,s_{38}(t)).
\]

---

## 8. 可以延伸成「均值回歸模型」

你現在的想法可以正式寫成：

\[
s_i(t) = \beta_1
\left(
\frac{6t}{38}-c_i(t)
\right).
\]

也就是：

\[
s_i(t)=\beta_1D_i(t).
\]

如果某個數字出現次數低於理論平均很多，它的分數就會上升。

若：

\[
\beta_1>0,
\]

代表模型相信：

> 出現次數落後平均越多，下一次越容易出現。

這就是最核心的 **mean-reversion model**。

---

## 9. 加入標準化 deficit

因為 \(D_i(t)\) 會隨著 \(t\) 變大而變大，最好做標準化。

在隨機模型下，對單一數字：

\[
c_i(t)\sim \text{Binomial}\left(t,\frac{6}{38}\right).
\]

其平均為：

\[
\mathbb{E}[c_i(t)] = \frac{6t}{38},
\]

變異數近似為：

\[
\operatorname{Var}(c_i(t)) = t\cdot \frac{6}{38}\left(1-\frac{6}{38}\right).
\]

所以可以定義標準化 deficit：

\[
Z_i(t) = \frac{
\frac{6t}{38}-c_i(t)
}{
\sqrt{
t\cdot \frac{6}{38}\left(1-\frac{6}{38}\right)
}
}.
\]

然後用：

\[
s_i(t) = \beta_1Z_i(t).
\]

這樣比直接用 \(D_i(t)\) 更穩定。

---

## 10. 完整推薦模型

我會建議你可以先實作這個版本：

\[
s_i(t) = \beta_1\log(1+G_i(t))
+
\beta_2Z_i(t)
+
\beta_3F_i^{(w)}(t),
\]

其中：

\[
F_i^{(w)}(t) = \frac{1}{w}\sum_{s=t-w+1}^{t}y_{s,i}.
\]

三個特徵分別代表：

| 特徵 | 意義 | 預期方向 |
| --- | --- | --- |
| \(\log(1+G_i(t))\) | 多久沒出現 | 若相信 overdue，係數 \(>0\) |
| \(Z_i(t)\) | 低於平均多少 | 若相信均值回歸，係數 \(>0\) |
| \(F_i^{(w)}(t)\) | 近期出現頻率 | 可正可負 |

最後：

\[
\widehat{S}_{t+1} = \operatorname{TopK}_6(s_1(t),\dots,s_{38}(t)).
\]

---

## 11. 不要直接假設 gap 越大越好，要先檢查

你可以先做一個診斷。

對所有歷史資料，統計：

\[
\widehat{h}(g) = P(y_{t+1,i}=1\mid G_i(t)=g).
\]

然後比較它和隨機基準：

\[
p_0=\frac{6}{38}\approx 0.1579.
\]

如果你發現：

\[
\widehat{h}(g)\approx 0.1579
\]

對所有 \(g\) 都差不多，那代表 gap 沒有用。

如果你發現：

\[
\widehat{h}(g)
\]

隨著 \(g\) 增加而上升，那你的想法就有數據支持。

---

## 12. 一個簡單實作流程

### Step 1：每期計算每個數字的特徵

對每個 \(t\) 和 \(i\)，計算：

\[
G_i(t),\quad Z_i(t),\quad F_i^{(w)}(t).
\]

---

### Step 2：建立訓練資料

每個樣本是：

\[
x_{t,i} = \left[
\log(1+G_i(t)),
Z_i(t),
F_i^{(w)}(t)
\right].
\]

目標是：

\[
y_{t+1,i}.
\]

所以資料會有：

\[
(T-1)\times 38
\]

筆 binary classification samples。

---

### Step 3：訓練 logistic regression

\[
P(y_{t+1,i}=1\mid x_{t,i}) = \sigma(\beta^\top x_{t,i}).
\]

也就是：

\[
p_{t+1,i} = \sigma
\left(
\beta_0
+
\beta_1\log(1+G_i(t))
+
\beta_2Z_i(t)
+
\beta_3F_i^{(w)}(t)
\right).
\]

---

### Step 4：每期取 top-6

\[
\widehat{S}_{t+1} = \operatorname{TopK}_6(p_{t+1,1},\dots,p_{t+1,38}).
\]

---

## 13. 但是要注意：這個模型可能還是輸給隨機

如果真實資料接近獨立隨機，那麼理論上：

\[
P(y_{t+1,i}=1\mid G_i(t),D_i(t),Z_i(t)) = \frac{6}{38}.
\]

也就是：

\[
\beta_1=\beta_2=\beta_3=0
\]

才是最好的模型。

這代表：

* gap 沒有用。
* deficit 沒有用。
* 熱號冷號沒有用。
* 神經網路也沒有用。
* 複雜模型只會 overfit。

所以這個方向可以試，但你應該把它當成一個 **假設檢定問題**：

> 歷史 gap 或 deficit 是否真的能讓下一期出現機率偏離 \(\frac{6}{38}\)？

---

## 14. 最值得測的三個模型

我建議你照這個順序測。

### Model A：純 gap model

\[
s_i(t)=\log(1+G_i(t)).
\]

預測 gap 最大的 6 個數字。

---

### Model B：純 deficit model

\[
s_i(t)=Z_i(t).
\]

預測目前最「低於平均」的 6 個數字。

---

### Model C：gap + deficit model

\[
s_i(t)=
\beta_1\log(1+G_i(t))
+
\beta_2Z_i(t).
\]

用 logistic regression 學 \(\beta_1,\beta_2\)。

---

## 15. 我會推薦的最終形式

比較乾淨的數學模型是：

\[
s_i(t) = \beta_1\log(1+G_i(t))
+
\beta_2
\frac{
\frac{6t}{38}-c_i(t)
}{
\sqrt{
t\cdot \frac{6}{38}\left(1-\frac{6}{38}\right)
}
}
+
\beta_3
\frac{1}{w}\sum_{s=t-w+1}^{t}y_{s,i}.
\]

然後：

\[
\widehat{S}_{t+1} = \operatorname{TopK}_6(s_1(t),\dots,s_{38}(t)).
\]

這個模型的解釋很清楚：

* 第一項：久沒出現是否增加機率。
* 第二項：是否會往長期平均回歸。
* 第三項：近期熱度是否有幫助。

如果測出來：

\[
\beta_1>0,\quad \beta_2>0,
\]

才表示你的「久沒出現、低於平均，所以較可能出現」想法在資料中真的有支持。

如果係數接近 0，或 out-of-sample 仍然輸給隨機，那就代表資料大概率沒有這種可學習結構。
