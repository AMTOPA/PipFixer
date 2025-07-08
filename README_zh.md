<div align="center">
<h1>PipFixer: AI智能命令修正工具</h1>

简体中文 | [ENGLISH](README.md)

[![GitHub release](https://img.shields.io/github/release/AMTOPA/PipFixer.svg?style=for-the-badge)](https://github.com/AMTOPA/PipFixer/releases)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![GLM](https://img.shields.io/badge/GLM-4--Flash-orange?style=for-the-badge)](https://open.bigmodel.cn/)

</div>

---

## ✨ 功能特性

- 🚀 **AI智能命令修正**  
  自动修正常见pip/conda命令错误（如"pip istall" → "pip install"）
- 📦 **包名验证**  
  修正常见包名错误（如"pytorch" → "torch"）
- 🌐 **镜像源管理**  
  一键切换清华、阿里云等PyPI镜像源
- ✔️ **智能执行**  
  识别有效命令，避免不必要的修正
- 🔍 **版本查询**  
  支持多种版本查询格式（如"numpy -v"）

---

## 🖥️ 演示

<div align="center">

![命令修正演示](./demo/1.png)

</div>

---

## 🛠️ 安装指南

### 环境要求

- Python 3.7+
- 智谱AI API密钥（有免费模型）

### 快速开始

```bash
pip install zhipuai
git clone https://github.com/AMTOPA/PipFixer.git
cd PipFixer
python main.py
```

### 📚 使用说明

首次运行将提示配置：

输入智谱AI API密钥：Apply for a free API key at [Zhipu AI Platform](https://www.bigmodel.cn/usercenter/proj-mgmt/apikeys):
![API Application](demo/2.png)

选择默认包管理器（pip/conda）

配置镜像源

自然输入命令：

```bash
pip >>> instal pytorch
修正结果: pip install torch
确认执行? [Y/n]: y
特殊命令：
```

```bash
change mirror  # 切换镜像源
exit          # 退出程序
```
