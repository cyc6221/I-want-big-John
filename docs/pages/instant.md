---
layout: page
title: 刮刮樂
permalink: /instant/
toc: false
---

## 最新刮刮樂

<div class="post-list">
  {% comment %}只顯示最新發行日（date）的所有刮刮樂，同日再依期號（num）由新到舊排序{% endcomment %}
  {% assign all_items = site.articles
    | where: "category", "all-instants"
    | sort: "date" | reverse %}
  {% assign latest_date = all_items.first.date | date: "%Y-%m-%d" %}
  {% assign latest_items = "" | split: "" %}
  {% for post in all_items %}
    {% assign post_date = post.date | date: "%Y-%m-%d" %}
    {% if post_date != latest_date %}{% break %}{% endif %}
    {% assign latest_items = latest_items | push: post %}
  {% endfor %}
  {% assign items = latest_items | sort: "num" | reverse %}

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

  <div class="post-more">
    <a href="{{ '/list/instant-compare/' | relative_url }}">全部刮刮樂比較 →</a>
  </div>
</div>

## 參考資料

- [台灣彩券刮刮樂玩法](https://www.taiwanlottery.com/instant/info)
- [熱賣中刮刮樂](https://www.taiwanlottery.com/instant/games)
- [刮刮樂銷售資訊](https://www.taiwanlottery.com/instant/sale)
- [歷史刮刮樂銷售資訊](https://www.taiwanlottery.com/instant/history)
