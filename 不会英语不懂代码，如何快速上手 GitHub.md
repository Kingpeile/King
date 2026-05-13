---
tags:
  - GitHub
  - 工具教程
  - 零基础
  - 效率工具
created: 2026-05-13
source: 小红书整理 + 多方资料汇总
---

# 不会英语不懂代码，如何快速上手 GitHub

> [!tip] 写给谁看
> 这篇笔记专门写给**不懂英语、不懂代码**的普通人。GitHub 不只是程序员的工具，它是全球最大的免费资源宝库，会用就能受益。

---

## 一、GitHub 是什么？

GitHub 是一个**全球最大的开源代码托管平台**，你可以把它理解成：

- 📦 一个巨大的**免费资源仓库**（软件、工具、教程、数据集……）
- 🌍 全球 4000 万开发者在上面共享项目
- 🔍 很多你在网上找的工具、插件，源头都在 GitHub

> [!note] 类比理解
> GitHub = **程序员的百度网盘 + 知乎 + 豆瓣** 的合体，东西多、质量高、完全免费。

---

## 二、第一步：解决英文障碍

### 方法 1：安装汉化插件（推荐）

**github-chinese** 是一款免费开源的汉化插件，装上之后 GitHub 界面变成中文。

**安装步骤（两种方式）：**

#### 方式 A：Chrome 浏览器扩展（最简单）
1. 打开 Chrome 网上应用店
2. 搜索 `GitHub 中文汉化插件`
3. 点击「添加至 Chrome」
4. 刷新 GitHub 页面，界面变中文 ✅

#### 方式 B：油猴脚本
1. 先安装浏览器插件：**Tampermonkey**（篡改猴）
2. 再去 GreasyFork 搜索 `GitHub 中文化插件`
3. 点击安装脚本即可

### 方法 2：用翻译工具辅助

- Chrome 浏览器自带「翻译此页」功能，右键点击页面选择即可
- 遇到看不懂的词，查下面的[[#常用词汇对照表]]

---

## 三、第二步：注册账号

1. 打开 [github.com](https://github.com)
2. 点击右上角「**Sign up**」（注册）
3. 填写邮箱、用户名、密码
4. 验证邮箱

> [!warning] 注意
> 用户名会出现在你的个人主页地址里，建议取一个简洁好记的英文名。

---

## 四、必须搞懂的 4 个按钮

这是 GitHub 最核心的功能，不懂代码也能天天用到。

### ⭐ Star — 收藏

- 相当于**「点赞 + 收藏」**
- 点了之后可以在「Your stars」里随时找回来
- 一个项目的 Star 数越高，说明越受欢迎、越值得信赖

### 👁️ Watch — 关注动态

- 相当于**「追更」**
- 开启后，这个项目有任何更新（新版本、新讨论）都会通知你
- 普通用户建议选「Releases only」，只在出新版本时通知

### 🍴 Fork — 复制到自己账号

- 相当于把别人的项目**「复制一份」**到自己账号下
- 不懂代码的人一般不需要用到
- 主要用于：想修改别人项目时使用

### 📥 Download / Clone — 下载

- **Download ZIP**：直接下载压缩包，最简单
- **Clone**：需要安装 Git，适合开发者

---

## 五、如何下载 GitHub 上的东西

### 方法 1：直接下载 ZIP（最简单，无需安装任何东西）

1. 打开你想要的项目页面
2. 点击绿色按钮「**Code**」
3. 选择「**Download ZIP**」
4. 解压即可使用

### 方法 2：使用 GitHub Desktop（图形界面，无需命令行）

> [!tip] 推荐给完全不懂代码的用户
> GitHub Desktop 是 GitHub 官方出的桌面客户端，有中文界面，点点鼠标就能完成所有操作。

1. 下载安装 [GitHub Desktop](https://desktop.github.com)
2. 登录你的 GitHub 账号
3. 找到想要的项目，点击「Code」→「Open with GitHub Desktop」
4. 选择保存位置，点击 Clone

---

## 六、如何在 GitHub 上找资源

### 搜索技巧

在搜索框输入关键词，加上以下过滤条件效果更好：

| 搜索写法 | 含义 |
|---------|------|
| `关键词 language:Chinese` | 只看中文项目 |
| `关键词 stars:>1000` | Star 数超过 1000 |
| `关键词 in:readme` | 关键词出现在说明文档里 |

### 判断项目质量的标准

- ⭐ **Star 数高**：说明受欢迎
- 🕐 **最近有更新**：说明在维护
- 📄 **有 README**：说明有文档，好上手
- 💬 **Issues 活跃**：社区活跃，遇到问题有人解答

---

## 七、不懂代码，GitHub 能用来做什么？

| 场景 | 具体用法 |
|------|---------|
| 找资源/工具 | 搜索关键词，下载 ZIP |
| 收藏好项目 | 点 Star，随时找回 |
| 追踪更新 | 点 Watch，第一时间知道新版本 |
| 找学习资料 | 搜索 `awesome + 主题`，如 `awesome python` |
| 找免费电子书 | 搜索书名或 `free ebook` |
| 托管个人网站 | 用 GitHub Pages 免费建站（零代码） |

---

## 八、常用词汇对照表

| 英文 | 中文意思 |
|------|---------|
| Repository / Repo | 仓库（一个项目） |
| Star | 收藏/点赞 |
| Fork | 复制到自己账号 |
| Clone | 下载到本地 |
| Commit | 提交（保存一次修改） |
| Pull Request / PR | 申请合并代码 |
| Issue | 问题/反馈 |
| Release | 发布的版本 |
| README | 项目说明文档 |
| Branch | 分支 |
| Open Source | 开源（免费可用） |

---

## 九、推荐工具汇总

| 工具 | 用途 | 链接 |
|------|------|------|
| github-chinese | GitHub 界面汉化 | Chrome 商店搜索 |
| GitHub Desktop | 图形化客户端，无需命令行 | desktop.github.com |
| Tampermonkey | 浏览器脚本管理器 | Chrome 商店搜索 |

---

## 十、学习路径建议

```
第 1 天：注册账号 + 装汉化插件
第 2 天：搜索一个你感兴趣的项目，点 Star 收藏
第 3 天：尝试下载一个项目（ZIP 方式）
第 1 周：找到 5 个你常用的工具或资料并 Star
第 2 周：安装 GitHub Desktop，尝试 Clone 一个项目
之后：按需深入，遇到问题查文档或 Issues
```

> [!quote] 记住
> GitHub 不是只给程序员用的，**会用搜索 + 会点 Star + 会下载 ZIP，就已经超过大多数人了。**

---

## 参考资料

- [写给新手的 Github 指南（复旦）](https://github.com/fudansswebfundamental/Docs)
- [github-chinese 汉化插件](https://github.com/maboloshi/github-chinese)
- [GitHub Watch/Star/Fork 详解 - 知乎](https://zhuanlan.zhihu.com/p/103695781)
- [菜鸟教程 · Github 简明教程](https://www.runoob.com/w3cnote/git-guide.html)
