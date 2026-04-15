---
layout: home
title: IWBJ
---

<div class="hero-grid">
  <div class="hero">
    <h1>🧧 威力彩 🧧</h1>
    <p>
      <a class="btn btn--primary" href="{{ '/recommender_638/' | relative_url }}">抽一組</a>
      <a class="btn btn--gold" href="{{ '/638/' | relative_url }}">研究方法</a>
    </p>
  </div>

  <div class="hero">
    <h1>🧧 大樂透 🧧</h1>
    <p>
      <a class="btn btn--primary" href="{{ '/recommender_649/' | relative_url }}">抽一組</a>
      <a class="btn btn--gold" href="{{ '/649/' | relative_url }}">研究方法</a>
    </p>
  </div>

  <div class="hero">
    <h1>🧧 今彩539 🧧</h1>
    <p>
      <a class="btn btn--primary" href="{{ '/recommender_539/' | relative_url }}">抽一組</a>
      <a class="btn btn--gold" href="{{ '/539/' | relative_url }}">研究方法</a>
    </p>
  </div>
</div>

<div class="card card--couplet">
  <h2>最新更新</h2>

  <div class="post-list">
    {% assign items = site.articles | sort: "date" | reverse %}
    {% for post in items limit: 6 %}
      <article class="post-item">
        <h3 class="post-title">
          <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
        </h3>
        <!-- post.date -->
        {% if post.date %}
        <div class="post-meta">
          {{ post.date | date: "%Y-%m-%d" }}
        </div>
        {% endif %}
        <!-- post.description -->
        {% if post.description %}
          <p class="post-excerpt">{{ post.description }}</p>
        {% else %}
          <p class="post-excerpt">{{ post.content | strip_html | truncate: 120 }}</p>
        {% endif %}
      </article>
    {% endfor %}
  </div>

  <div class="post-more">
    <a href="{{ '/all-articles/' | relative_url }}">>>> 全部文章 <<<</a>
  </div>
</div>
