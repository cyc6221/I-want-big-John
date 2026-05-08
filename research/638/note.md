# Note

## 1. 問題類型

這個問題最適合視為：

> **固定大小集合預測問題**
> 或
> **帶有 cardinality constraint 的 multi-label prediction problem**

不是一般的多分類問題，因為下一次輸出不是單一類別，而是一個集合：

\[
S_{T+1} \subset \Omega,\qquad |S_{T+1}|=6
\]

轉成向量後，每次輸出是：

\[
y_t \in \{0,1\}^{38},\qquad \sum_{i=1}^{38} y_{t,i}=6
\]

所以它是 **multi-label classification**，但多了一個很強的限制：

\[
\text{exactly 6 labels must be active.}
\]

---

## 2. 資料表示方式

令

\[
\Omega=\{1,2,\dots,38\}.
\]

每次觀測集合 \(S_t\) 轉成 binary vector：

\[
y_t=(y_{t,1},y_{t,2},\dots,y_{t,38})\in\{0,1\}^{38}
\]

其中

\[
y_{t,i}=
\begin{cases}
1, & i\in S_t,\\
0, & i\notin S_t.
\end{cases}
\]

且一定滿足：

\[
\sum_{i=1}^{38} y_{t,i}=6.
\]

---

## 3. 目標機率模型

我們希望估計：

\[
P(y_{T+1,i}=1\mid y_1,y_2,\dots,y_T)
\]

也就是給定歷史序列後，每個元素 \(i\) 下一期被選中的條件機率。

可以定義：

\[
p_{T+1,i}=P(y_{T+1,i}=1\mid \mathcal{F}_T),
\]

其中

\[
\mathcal{F}_T=\sigma(y_1,\dots,y_T)
\]

表示由歷史資料產生的資訊集合。

最後預測集合為：

\[
\widehat{S}_{T+1} = \operatorname{TopK}_6(p_{T+1,1},p_{T+1,2},\dots,p_{T+1,38}).
\]

也就是選出機率最高的 6 個元素。

---

## 4. 最基本統計模型：歷史頻率模型

最簡單的估計方式是計算每個元素過去出現的頻率。

定義元素 \(i\) 在前 \(T\) 次中出現的次數：

\[
c_i=\sum_{t=1}^{T} y_{t,i}.
\]

則自然估計為：

\[
\widehat{p}_i=\frac{c_i}{T}.
\]

因為每期恰好有 6 個元素，所以：

\[
\sum_{i=1}^{38} c_i=6T.
\]

因此：

\[
\sum_{i=1}^{38}\widehat{p}_i = \sum_{i=1}^{38}\frac{c_i}{T} = 6.
\]

這代表所有元素的邊際機率加總剛好是 6，符合「每期選出 6 個」的邊際限制。

預測方式：

\[
\widehat{S}_{T+1} = \operatorname{TopK}_6(\widehat{p}_1,\dots,\widehat{p}_{38}).
\]

---

## 5. Bayesian smoothing 模型

如果資料量 \(T\) 不大，單純使用歷史頻率會很不穩定。

可以加入平滑項：

\[
\widehat{p}_i = 6\cdot
\frac{c_i+\alpha}{\sum_{j=1}^{38}(c_j+\alpha)}.
\]

由於

\[
\sum_{j=1}^{38}c_j=6T,
\]

所以：

\[
\widehat{p}_i = 6\cdot
\frac{c_i+\alpha}{6T+38\alpha}.
\]

這樣仍然滿足：

\[
\sum_{i=1}^{38}\widehat{p}_i=6.
\]

其中 \(\alpha>0\) 是平滑參數。

例如：

* \(\alpha=0\)：純歷史頻率。
* \(\alpha=1\)：Laplace smoothing。
* \(\alpha\) 越大，模型越接近均勻分布。

若完全沒有資訊，則每個元素的理論機率是：

\[
P(y_{t,i}=1)=\frac{6}{38}.
\]

---

## 6. 時間加權模型：近期資料較重要

如果懷疑近期觀測比早期觀測更有參考價值，可以使用時間衰減權重。

令

\[
0<\lambda\leq 1
\]

為衰減係數，定義加權出現次數：

\[
c_i^{(\lambda)} = \sum_{t=1}^{T}\lambda^{T-t}y_{t,i}.
\]

越接近 \(T\) 的資料權重越高。

加權機率估計為：

\[
\widehat{p}_i = 6\cdot
\frac{c_i^{(\lambda)}+\alpha}
{\sum_{j=1}^{38}(c_j^{(\lambda)}+\alpha)}.
\]

如果 \(\lambda=1\)，就退化成一般歷史頻率模型。

---

## 7. Logistic regression / one-vs-rest 模型

可以把問題切成 38 個二元預測問題：

\[
P(y_{t+1,i}=1\mid x_t) = \sigma(w_i^\top x_t+b_i),
\]

其中：

\[
\sigma(z)=\frac{1}{1+e^{-z}}.
\]

這裡 \(x_t\) 是由歷史資料 \(y_1,\dots,y_t\) 設計出的特徵向量。

對每個元素 \(i\)，都訓練一個二元分類器：

\[
y_{t+1,i}\in\{0,1\}.
\]

訓練目標可以使用 binary cross entropy：

\[
\mathcal{L} = -\sum_{t}\sum_{i=1}^{38}
\left[
y_{t+1,i}\log p_{t+1,i}
+
(1-y_{t+1,i})\log(1-p_{t+1,i})
\right].
\]

最後預測時，取機率最高的 6 個：

\[
\widehat{S}_{t+1} = \operatorname{TopK}_6(p_{t+1,1},\dots,p_{t+1,38}).
\]

這個方法簡單、可解釋，但缺點是它本身沒有直接保證：

\[
\sum_{i=1}^{38}p_{t+1,i}=6.
\]

所以通常需要後處理，用 top-6 強制滿足集合大小限制。

---

## 8. 更嚴謹的固定大小集合模型

更自然的模型是直接定義整個集合 \(S\) 的機率，而不是只分別預測 38 個元素。

令模型對每個元素輸出一個分數：

\[
s_i(x_T)\in\mathbb{R}.
\]

對任意大小為 6 的集合 \(S\subset\Omega\)，定義：

\[
P(S\mid x_T) = \frac{
\exp\left(\sum_{i\in S}s_i(x_T)\right)
}{
\sum_{A\subset\Omega,\ |A|=6}
\exp\left(\sum_{j\in A}s_j(x_T)\right)
}.
\]

其中分母只對所有大小為 6 的集合加總：

\[
A\subset\Omega,\qquad |A|=6.
\]

這個模型的好處是它直接保證：

\[
|S|=6.
\]

預測時要找：

\[
\widehat{S} = \arg\max_{S\subset\Omega,\ |S|=6}
P(S\mid x_T).
\]

因為 log probability 中與 \(S\) 有關的部分是：

\[
\sum_{i\in S}s_i(x_T),
\]

所以最佳集合就是分數最高的 6 個元素：

\[
\widehat{S} = \operatorname{TopK}_6(s_1(x_T),\dots,s_{38}(x_T)).
\]

這是比較乾淨的數學建模方式。

---

## 9. 可以使用的模型類型

### 9.1 統計模型

#### 歷史頻率模型

\[
\widehat{p}_i=\frac{c_i}{T}.
\]

適合做 baseline。

---

#### Bayesian smoothing

\[
\widehat{p}_i = 6\cdot
\frac{c_i+\alpha}{6T+38\alpha}.
\]

適合資料少時避免極端估計。

---

#### 時間衰減模型

\[
\widehat{p}_i = 6\cdot
\frac{
\sum_{t=1}^{T}\lambda^{T-t}y_{t,i}+\alpha
}{
\sum_{j=1}^{38}
\left(
\sum_{t=1}^{T}\lambda^{T-t}y_{t,j}+\alpha
\right)
}.
\]

適合假設近期資料更重要的情況。

---

#### Markov transition model

可以估計：

\[
P(y_{t+1,i}=1\mid y_{t,j}=1).
\]

也就是元素 \(j\) 出現後，下一期元素 \(i\) 出現的機率。

例如定義轉移分數：

\[
s_i(t) = \sum_{j=1}^{38}A_{j,i}y_{t,j},
\]

其中 \(A_{j,i}\) 表示從元素 \(j\) 到元素 \(i\) 的轉移強度。

---

### 9.2 機器學習模型

#### Logistic regression

適合做可解釋模型。

---

#### Random forest / Gradient boosting

可以處理非線性特徵，例如：

* 近期出現次數
* 距離上次出現多久
* pairwise co-occurrence
* moving average
* trend features

---

#### Neural network

可以輸入歷史窗口：

\[
(y_{t-m+1},y_{t-m+2},\dots,y_t)
\]

然後輸出：

\[
p_{t+1}\in[0,1]^{38}.
\]

可以使用：

* MLP
* RNN
* LSTM
* GRU
* Transformer encoder

但如果資料接近隨機，神經網路通常只會過度擬合。

---

## 10. 特徵設計

對每個時間點 \(t\)，建立特徵：

\[
x_t=\phi(y_1,\dots,y_t).
\]

常見特徵如下。

---

### 10.1 長期頻率特徵

\[
f_i^{\text{all}}(t) = \frac{1}{t}\sum_{\tau=1}^{t}y_{\tau,i}.
\]

表示元素 \(i\) 從一開始到目前為止的出現比例。

---

### 10.2 近期窗口頻率

給定窗口長度 \(w\)，例如 \(w=10,20,50\)：

\[
f_i^{(w)}(t) = \frac{1}{w}\sum_{\tau=t-w+1}^{t}y_{\tau,i}.
\]

表示元素 \(i\) 在最近 \(w\) 期的活躍程度。

---

### 10.3 距離上次出現時間

定義元素 \(i\) 上次出現的時間：

\[
\ell_i(t)=\max\{\tau\leq t:y_{\tau,i}=1\}.
\]

則 gap feature 為：

\[
g_i(t)=t-\ell_i(t).
\]

如果元素 \(i\) 很久沒出現，則 \(g_i(t)\) 會比較大。

---

### 10.4 指數移動平均

\[
m_i(t) = \lambda m_i(t-1)+(1-\lambda)y_{t,i}.
\]

這可以看成元素 \(i\) 的近期動量。

---

### 10.5 共現特徵

估計元素 \(i,j\) 同時出現的頻率：

\[
C_{i,j} = \sum_{t=1}^{T}y_{t,i}y_{t,j}.
\]

也可以估計條件共現：

\[
P(y_{t,i}=1\mid y_{t,j}=1).
\]

這類特徵可以捕捉元素之間是否常一起出現。

不過在真隨機資料中，這些共現關係多半只是雜訊。

---

### 10.6 前一期集合特徵

直接使用上一期向量：

\[
y_t
\]

作為特徵，預測：

\[
y_{t+1}.
\]

也可以使用最近 \(m\) 期：

\[
x_t=(y_{t-m+1},\dots,y_t).
\]

這會形成一個長度為：

\[
38m
\]

的特徵向量。

---

## 11. 如何處理「必須剛好選出 6 個元素」

這是此問題的核心限制。

### 方法一：先估計機率，再取 top-6

模型輸出：

\[
p_i=P(y_{T+1,i}=1\mid \mathcal{F}_T).
\]

然後：

\[
\widehat{S}_{T+1} = \operatorname{TopK}_6(p_1,\dots,p_{38}).
\]

這是最簡單、最實用的做法。

---

### 方法二：讓機率總和等於 6

要求模型輸出滿足：

\[
\sum_{i=1}^{38}p_i=6.
\]

例如先算出 raw score \(r_i>0\)，再正規化：

\[
p_i = 6\cdot
\frac{r_i}{\sum_{j=1}^{38}r_j}.
\]

這可以保證：

\[
\sum_{i=1}^{38}p_i=6.
\]

但仍不代表每次抽樣一定剛好選 6 個，所以最後還是常搭配 top-6。

---

### 方法三：直接建模大小為 6 的集合分布

使用：

\[
P(S\mid x) = \frac{
\exp\left(\sum_{i\in S}s_i(x)\right)
}{
\sum_{A\subset\Omega,\ |A|=6}
\exp\left(\sum_{j\in A}s_j(x)\right)
}.
\]

這是最符合問題限制的模型，因為它的樣本空間本來就是：

\[
\{S\subset\Omega:|S|=6\}.
\]

---

## 12. 評估模型表現

對於測試資料：

\[
S_{T+1},S_{T+2},\dots,S_{T+n}
\]

每期模型預測：

\[
\widehat{S}_t.
\]

---

### 12.1 命中數

最直觀的指標是：

\[
\text{Hit}_t = |\widehat{S}_t\cap S_t|.
\]

平均命中數：

\[
\frac{1}{n}\sum_{t=1}^{n}|\widehat{S}_t\cap S_t|.
\]

這是最適合這個問題的主要評估方式。

---

### 12.2 Precision@6

因為每次都預測 6 個，所以：

\[
\text{Precision@6} = \frac{|\widehat{S}_t\cap S_t|}{6}.
\]

---

### 12.3 Hamming loss

用 binary vector 評估：

\[
\text{HammingLoss}_t = \frac{1}{38}
\sum_{i=1}^{38}
\mathbf{1}\{\widehat{y}_{t,i}\neq y_{t,i}\}.
\]

如果預測集合和真實集合有 \(h\) 個重疊，則錯誤數是：

\[
(6-h)+(6-h)=12-2h.
\]

所以：

\[
\text{HammingLoss}_t = \frac{12-2h}{38}.
\]

---

### 12.4 Log loss / Brier score

如果模型輸出機率 \(p_i\)，可以評估機率品質。

Brier score：

\[
\text{Brier}_t = \frac{1}{38}
\sum_{i=1}^{38}(p_{t,i}-y_{t,i})^2.
\]

Binary log loss：

\[
\text{LogLoss}_t = -\sum_{i=1}^{38}
\left[
y_{t,i}\log p_{t,i}
+
(1-y_{t,i})\log(1-p_{t,i})
\right].
\]

不過要注意：因為 \(y_t\) 有固定 6 個 1，所以如果模型沒有處理 cardinality constraint，log loss 的解讀會比較粗糙。

---

### 12.5 與 baseline 比較

一定要跟以下 baseline 比較：

#### 均勻隨機模型

\[
P(y_{t,i}=1)=\frac{6}{38}.
\]

#### 歷史頻率模型

\[
\widehat{p}_i=\frac{c_i}{T}.
\]

#### 近期頻率模型

\[
\widehat{p}_i = 6\cdot
\frac{c_i^{(w)}+\alpha}
{\sum_{j=1}^{38}(c_j^{(w)}+\alpha)}.
\]

如果複雜模型無法穩定超過這些 baseline，就代表歷史資料中可能沒有可學習結構。

---

## 13. 若資料接近獨立隨機，模型的理論限制

這是最重要的部分。

假設每一期都是從所有大小為 6 的子集合中均勻隨機抽出：

\[
S_t\sim \text{Uniform}\{S\subset\Omega:|S|=6\}.
\]

且各期獨立：

\[
S_1,S_2,\dots,S_T
\quad\text{i.i.d.}
\]

那麼對任意元素 \(i\)：

\[
P(y_{T+1,i}=1\mid y_1,\dots,y_T) = P(y_{T+1,i}=1) = \frac{6}{38}.
\]

也就是說，歷史資料不提供任何預測資訊。

因此所有元素的條件機率都相同：

\[
p_{T+1,1}=p_{T+1,2}=\cdots=p_{T+1,38}=\frac{6}{38}.
\]

這時候所謂的 top-6 沒有真正意義，因為 38 個元素完全平手。

---

### 13.1 任意預測集合的期望命中數

假設你預測任意固定集合：

\[
\widehat{S},\qquad |\widehat{S}|=6.
\]

真實集合 \(S\) 也是從 38 個元素中均勻選 6 個。

則期望命中數為：

\[
\mathbb{E}[|\widehat{S}\cap S|] = \sum_{i\in \widehat{S}}P(i\in S) = 6\cdot \frac{6}{38} = \frac{36}{38}
\approx 0.947.
\]

也就是說，若資料真的是獨立均勻隨機，平均命中數不到 1 個。

---

### 13.2 命中數分布

命中數

\[
H=|\widehat{S}\cap S|
\]

服從超幾何分布：

\[
H\sim \text{Hypergeometric}(N=38,K=6,n=6).
\]

因此：

\[
P(H=h) = \frac{
\binom{6}{h}\binom{32}{6-h}
}{
\binom{38}{6}
},
\qquad h=0,1,\dots,6.
\]

其中：

* \(N=38\)：總元素數。
* \(K=6\)：預測集合大小。
* \(n=6\)：真實集合大小。
* \(h\)：命中數。

---

### 13.3 完全命中的機率

完全命中代表：

\[
\widehat{S}=S.
\]

如果是均勻隨機，則：

\[
P(\widehat{S}=S) = \frac{1}{\binom{38}{6}}.
\]

而

\[
\binom{38}{6}=2,760,681.
\]

所以：

\[
P(\widehat{S}=S) = \frac{1}{2,760,681}.
\]

這代表如果資料真的接近獨立隨機，任何模型都無法在理論上穩定提高預測能力。

---

## 14. 核心限制：可學習性取決於資料是否有結構

如果存在某種非隨機結構，例如：

\[
P(y_{t+1,i}=1\mid y_1,\dots,y_t)
\neq
\frac{6}{38},
\]

或是存在時間依賴：

\[
P(y_{t+1}\mid y_t)\neq P(y_{t+1}),
\]

那模型才可能學到東西。

但如果：

\[
S_t \overset{i.i.d.}{\sim}
\text{Uniform}\{S\subset\Omega:|S|=6\},
\]

則對任何模型 \(f\)，都有：

\[
P(S_{T+1}\mid S_1,\dots,S_T) = P(S_{T+1}).
\]

因此歷史資料不含有關下一期的資訊。

此時複雜模型，例如 neural network、random forest、gradient boosting，可能只是在學習歷史雜訊，而不是學習真正規律。

---

## 15. 建議的完整建模流程

### Step 1：資料轉換

將每一期集合轉成：

\[
y_t\in\{0,1\}^{38}.
\]

---

### Step 2：建立 rolling training samples

對每個時間點 \(t\)，建立：

\[
x_t=\phi(y_1,\dots,y_t),
\]

目標為：

\[
y_{t+1}.
\]

所以訓練資料是：

\[
(x_1,y_2),(x_2,y_3),\dots,(x_{T-1},y_T).
\]

---

### Step 3：訓練機率模型

例如：

\[
p_{t+1,i} = P(y_{t+1,i}=1\mid x_t).
\]

可以從簡到複依序嘗試：

1. 均勻模型。
2. 歷史頻率模型。
3. 近期頻率模型。
4. Logistic regression。
5. Gradient boosting。
6. Neural network。

---

### Step 4：強制 top-6 輸出

\[
\widehat{S}_{t+1} = \operatorname{TopK}_6(p_{t+1,1},\dots,p_{t+1,38}).
\]

---

### Step 5：rolling validation

不能隨機切 train/test，因為這是序列資料。

應該使用時間順序驗證：

\[
\text{train: }1,\dots,t
\]

\[
\text{test: }t+1
\]

然後往後滾動。

---

### Step 6：比較 baseline

主要看模型是否能穩定超過：

\[
\mathbb{E}[H]=\frac{36}{38}\approx 0.947.
\]

如果沒有明顯超過這個水準，表示資料很可能接近隨機，模型沒有實質預測能力。

---

## 16. 總結

這個問題可以形式化為：

\[
\text{multi-label prediction with fixed cardinality } 6.
\]

最基本的模型是：

\[
\widehat{p}_i=P(y_{T+1,i}=1\mid y_1,\dots,y_T).
\]

再用：

\[
\widehat{S}_{T+1} = \operatorname{TopK}_6(\widehat{p}_1,\dots,\widehat{p}_{38})
\]

產生預測集合。

可用模型包含：

* 歷史頻率模型
* Bayesian smoothing
* 時間衰減模型
* Markov transition model
* Logistic regression
* Random forest / Gradient boosting
* RNN / LSTM / Transformer
* 固定大小集合分布模型

但若資料本質上是獨立均勻隨機，則：

\[
P(y_{T+1,i}=1\mid y_1,\dots,y_T) = \frac{6}{38}
\]

對所有 \(i\) 都成立。

因此沒有任何模型能從歷史資料中穩定預測下一期集合。這時候模型最多只能描述歷史頻率，不能真正提高預測能力。
