# 为 MAHO 贡献

English: [`CONTRIBUTING.md`](CONTRIBUTING.md)

感谢你帮助改进证据优先的智能体工程方法。

## 修改代码前

1. 写清用户可见结果和非目标。
2. 保持改动窄小、可逆。
3. 添加或更新能够证明结果的测试。
4. 保留失败和中止证据，不要为了让结果好看而改写历史。
5. 面向人的英文和简体中文文档必须同步更新。

运行本地门禁：

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q harness scripts tests
```

智能体兼容测试必须使用 disposable repo。测试夹具中不得包含凭据、生产数据、私人绝对路径或付费账户假设。

## 开发者原创声明

贡献采用 Developer Certificate of Origin 1.1。提交时添加签署：

```bash
git commit -s
```

该签署表示你有权依据 Apache License 2.0 提交贡献。首次公开发布不要求签署 CLA。
