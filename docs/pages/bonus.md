---
layout: page
title: 加碼
permalink: /bonus/
toc: false
---

歷年春節、端午、中秋的大樂透加碼活動辦法與開獎統計。

<div class="post-list">
  {% assign items = site.articles
    | where: "category", "649-research"
    | sort: "date" | reverse %}

  {% for post in items %}
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
