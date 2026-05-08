---
layout: page
title: 紀錄
permalink: /list/
toc: false
---

本人超無聊紀錄

## 威力彩記錄

<div class="post-list">
  {% assign items = site.list
    | where: "category", "list-638" %}

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

## 大樂透記錄

<div class="post-list">
  {% assign items = site.list
    | where: "category", "list-649" %}

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

## 刮刮樂記錄

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

## 三星電選四倍十期紀錄

<div class="post-list">
  {% assign items = site.list
    | where: "category", "list-3stars" %}

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
