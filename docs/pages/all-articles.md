---
layout: page
title: 全部文章
permalink: /all-articles/
toc: false
---

<div class="article-filter" data-article-filter>
  <div class="article-filter__row">
    <span class="article-filter__label">遊戲</span>
    <div class="article-filter__chips" data-filter-group="game">
      <button type="button" class="tag-chip" data-filter-value="649" aria-pressed="false">大樂透</button>
      <button type="button" class="tag-chip" data-filter-value="638" aria-pressed="false">威力彩</button>
      <button type="button" class="tag-chip" data-filter-value="539" aria-pressed="false">今彩539</button>
      <button type="button" class="tag-chip" data-filter-value="instants" aria-pressed="false">刮刮樂</button>
    </div>
  </div>
  <div class="article-filter__row">
    <span class="article-filter__label">類型</span>
    <div class="article-filter__chips" data-filter-group="kind">
      <button type="button" class="tag-chip" data-filter-value="bonus" aria-pressed="false">加碼</button>
    </div>
  </div>
  <div class="article-filter__row">
    <span class="article-filter__label">刮刮樂</span>
    <div class="article-filter__chips" data-filter-group="status">
      <button type="button" class="tag-chip" data-filter-value="active" aria-pressed="false">上架中</button>
      <button type="button" class="tag-chip" data-filter-value="archived" aria-pressed="false">已下架</button>
    </div>
  </div>
  <div class="article-filter__bar">
    <span class="article-filter__count" data-filter-count aria-live="polite"></span>
    <label class="article-filter__sort">排序
      <select data-filter-sort>
        <option value="date-desc">日期：新到舊</option>
        <option value="date-asc">日期：舊到新</option>
        <option value="title">標題</option>
      </select>
    </label>
  </div>
</div>

<div class="post-list post-list--filterable" data-article-list>
    {% assign items = site.articles | sort: "date" | reverse %}
    {% for post in items %}
      {% assign game = "" %}
      {% assign status = "" %}
      {% assign kind = "" %}
      {% assign game_label = "" %}
      {% if post.category contains "all-instants" %}
        {% assign game = "instants" %}
        {% assign game_label = "刮刮樂" %}
        {% if post.category == "all-instants-archive" %}{% assign status = "archived" %}{% else %}{% assign status = "active" %}{% endif %}
      {% elsif post.category contains "649" %}
        {% assign game = "649" %}
        {% assign game_label = "大樂透" %}
      {% elsif post.category contains "638" %}
        {% assign game = "638" %}
        {% assign game_label = "威力彩" %}
      {% elsif post.category contains "539" %}
        {% assign game = "539" %}
        {% assign game_label = "今彩539" %}
      {% endif %}
      {% if post.url contains "bonus" %}{% assign kind = "bonus" %}{% endif %}
      <article class="post-item" data-game="{{ game }}" data-kind="{{ kind }}" data-status="{{ status }}" data-date="{{ post.date | date: '%Y-%m-%d' }}" data-title="{{ post.title | escape }}">
        <h3 class="post-title">
          <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
        </h3>
        <div class="post-meta">
          {% if post.date %}{{ post.date | date: "%Y-%m-%d" }}{% endif %}
          {% if game_label != "" %}<span class="tag-chip tag-chip--static">{{ game_label }}</span>{% endif %}
          {% if kind == "bonus" %}<span class="tag-chip tag-chip--static">加碼</span>{% endif %}
          {% if status == "active" %}<span class="tag-chip tag-chip--static">上架中</span>{% elsif status == "archived" %}<span class="tag-chip tag-chip--static">已下架</span>{% endif %}
        </div>
        {% if post.description %}
          <p class="post-excerpt">{{ post.description }}</p>
        {% else %}
          <p class="post-excerpt">{{ post.content | strip_html | truncate: 120 }}</p>
        {% endif %}
      </article>
    {% endfor %}
    <p class="post-empty" data-filter-empty hidden>沒有符合條件的文章。</p>
</div>

<script src="{{ '/assets/js/article-filter.js' | relative_url }}" defer></script>
