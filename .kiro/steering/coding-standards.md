---
description: Coding standards and conventions for the Meduseld project
---

# Coding Standards

## Error Handling

Every `catch` block must include a `console.error()` (or `logger.error()` in Python) with a descriptive message and the error object. Never silently swallow errors.

```javascript
// Bad
catch (e) {
  doFallback();
}

// Good
catch (e) {
  console.error('Description of what failed:', e);
  doFallback();
}
```

```python
# Bad
except Exception:
    pass

# Good
except Exception as e:
    logger.error("Description of what failed: %s", e)
```

## Tooltips

Always use Bootstrap tooltips (`data-bs-toggle="tooltip"` + `data-bs-title="..."`) instead of native HTML `title` attributes. Initialize with `new bootstrap.Tooltip(el)` after dynamically rendering elements. Dispose existing tooltips before re-rendering to prevent memory leaks.

## Punctuation

Never use em dashes (`—`) or double hyphens (`--`) in documentation, comments, commit messages, or UI text. Always use a single hyphen (`-`) surrounded by spaces instead.

```markdown
Bad: ExSpire is source-available — the code is public
Bad: ExSpire is source-available -- the code is public
Good: ExSpire is source-available - the code is public
```
