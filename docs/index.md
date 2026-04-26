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
  <div class="home-section-head">
    <div>
      <h2>最新一期開獎結果</h2>
    </div>
  </div>

  <div class="latest-draws-grid">
    {% for game in site.data.latest_draws.games %}
      <section class="latest-draw-card latest-draw-card--{{ game.key }}">
        <div class="latest-draw-card__top">
          <div>
            <p class="latest-draw-card__eyebrow">{{ game.name }}</p>
            <h3>第 {{ game.issue }} 期</h3>
          </div>
          <span class="latest-draw-card__date">{{ game.date }}</span>
        </div>

        <div class="latest-draw-card__body">
          <div class="ball-row latest-draw-card__balls">
            {% for number in game.numbers %}
              <span class="ball" aria-hidden="true">{{ number }}</span>
            {% endfor %}
            {% if game.special_number %}
              <span class="ball ball--red" aria-hidden="true">{{ game.special_number }}</span>
            {% endif %}
          </div>
        </div>
      </section>
    {% endfor %}
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
