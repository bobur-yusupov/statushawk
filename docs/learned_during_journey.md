# Learned during journey

Learned distributed monolith

```python
monitor = Monitor.objects.only("url", "interval", "is_active").get(id=monitor_id)
```
