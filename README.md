# 天天生鲜项目



### celery异步处理邮箱验证，使用celery+redis

```python
# 运行celery的worker
celery -A celery_tasks.tasks worker -l info -P eventlet
```




