---
layout: page
title: 刮刮樂
permalink: /instant/
toc: false
---

[台灣彩券刮刮樂玩法](https://www.taiwanlottery.com/instant/info)

## 最新刮刮樂

<div class="post-list">
  {% assign items = site.articles
    | where: "category", "all-instants"
    | sort: "published" | reverse %}

  {% for post in items %}
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

## 本人超無聊紀錄

<div class="post-list">
  {% assign items = site.list
    | where: "category", "list-instant" %}

  {% for post in items %}
    <article class="post-item">
      <h3 class="post-title">
        <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      </h3>
      <!-- post.description -->
      {% if post.description %}
        <p class="post-excerpt">{{ post.description }}</p>
      {% else %}
        <p class="post-excerpt">{{ post.content | strip_html | truncate: 120 }}</p>
      {% endif %}
    </article>
  {% endfor %}
</div>
