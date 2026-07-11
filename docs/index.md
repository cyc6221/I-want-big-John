---
layout: home
title: IWBJ
---

<div class="card card--couplet">
  <div class="home-section-head">
    <div>
      <h2>最新一期開獎結果</h2>
    </div>
  </div>

  <div class="latest-draws-grid">
    {% for game in site.data.latest_draws.games %}
      {% include latest-draw-card-body.html game=game %}
    {% endfor %}
  </div>
</div>

<div class="card card--couplet">
  <div class="home-section-head">
    <div>
      <h2>快速入口</h2>
    </div>
  </div>

  <div class="hero-grid hero-grid--quick-links">
    <div class="hero">
      <h3 class="hero__title">🧧 威力彩 🧧</h3>
      <p>
        <a class="btn btn--primary" href="{{ '/recommender_638/' | relative_url }}">抽一組</a>
        <a class="btn btn--gold" href="{{ '/638/' | relative_url }}">研究方法</a>
      </p>
    </div>

    <div class="hero">
      <h3 class="hero__title">🧧 大樂透 🧧</h3>
      <p>
        <a class="btn btn--primary" href="{{ '/recommender_649/' | relative_url }}">抽一組</a>
        <a class="btn btn--gold" href="{{ '/649/' | relative_url }}">研究方法</a>
      </p>
    </div>

    <div class="hero">
      <h3 class="hero__title">🧧 今彩539 🧧</h3>
      <p>
        <a class="btn btn--primary" href="{{ '/recommender_539/' | relative_url }}">抽一組</a>
        <a class="btn btn--gold" href="{{ '/539/' | relative_url }}">研究方法</a>
      </p>
    </div>
  </div>
</div>

<div class="card card--couplet">
  <h2>最新文章</h2>

  <div class="post-list">
    {% assign items = site.articles | sort: "date" | reverse %}
    {% for post in items limit: 6 %}
      <article class="post-item">
        <h3 class="post-title">
          <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
        </h3>
        {% if post.date %}
        <div class="post-meta">
          {{ post.date | date: "%Y-%m-%d" }}
        </div>
        {% endif %}
        {% if post.description %}
          <p class="post-excerpt">{{ post.description }}</p>
        {% else %}
          <p class="post-excerpt">{{ post.content | strip_html | truncate: 120 }}</p>
        {% endif %}
      </article>
    {% endfor %}
  </div>

  <div class="post-more">
    <a href="{{ '/all-articles/' | relative_url }}">>>> 查看全部文章 <<<</a>
  </div>
</div>
