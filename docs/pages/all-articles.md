---
layout: page
title: 全部文章
permalink: /all-articles/
toc: false
---

<div class="post-list">
    {% assign items = site.articles | sort: "date" | reverse %}
    {% for post in items%}
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
