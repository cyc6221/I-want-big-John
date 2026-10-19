---
layout: home
title: IWBJ
---

## 最新開獎

<div class="latest-draws-grid">
  {% for game in site.data.latest_draws.games %}
    {% include latest-draw-card-body.html game=game actions=true %}
  {% endfor %}
</div>

## 最新文章

<div class="post-list">
  {% assign items = site.articles | sort: "date" | reverse %}
  {% assign latest_date = items.first.date | date: "%Y-%m-%d" %}
  {% for post in items %}
    {% assign post_date = post.date | date: "%Y-%m-%d" %}
    {% if post_date != latest_date %}{% break %}{% endif %}
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

  <div class="post-more">
    <a href="{{ '/all-articles/' | relative_url }}">查看全部文章 →</a>
  </div>
</div>
