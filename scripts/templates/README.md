# Templates

這個資料夾放的是手動建立內容時可複製的模板檔。  
This folder stores copyable templates for manually creating new content files.

## Included Files

- `all-instants-article.md.example`

## How To Use

如果你要新增新的刮刮樂文章，可以先複製：

```bash
scripts/templates/all-instants-article.md.example
```

再改名成對應期號，例如 `docs/_articles/all-instants/5148.md`。  
Then rename it to the target issue number, such as `docs/_articles/all-instants/5148.md`.

這類模板主要是給人工整理資料時參考，不會被 `python scripts/run.py` 直接執行。  
These templates are reference files for manual data entry and are not executed by `python scripts/run.py`.
