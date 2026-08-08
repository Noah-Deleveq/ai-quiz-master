# 🎯 AI 出题官（AI Quiz Master）

一个帮助你**主动学习**的 AI 工具：输入想学的主题，AI 生成高质量选择题考你，答完即时判分 + 逐题精讲。基于认知科学中的"主动回忆 + 反馈"原理，比看书看视频更高效。

## ✨ 功能亮点

- **AI 出题**：输入任意主题（Redis、Python 装饰器、MySQL 索引…），AI 生成 3-10 道选择题
- **难度可选**：入门 / 进阶 / 困难 / 混合，由浅入深
- **高质量干扰项**：错误选项有迷惑性，覆盖概念、原理、应用场景
- **即时判分**：点选答案立即判断对错，附进度得分条
- **逐题精讲**：每题 100-200 字解析，讲清"为什么对、错在哪"
- **再来一组**：随时换主题继续练

## 🏗 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10 · FastAPI · Uvicorn |
| AI | DeepSeek API（OpenAI 兼容 SDK，**强制 JSON 结构化输出**） |
| 前端 | 原生 HTML / CSS / JavaScript（无框架） |

## 🧠 核心设计

```
用户输入主题 ──▶ AI 出题（结构化 JSON）──▶ 逐题作答 ──▶ 判分 + 精讲
```

- **结构化输出**：通过 `response_format=json_object` + 详细 prompt 约束，让大模型稳定输出
  `{questions: [{question, options[4], answer, explanation}]}` 格式，程序直接解析，杜绝自由文本解析问题
- **判题逻辑**：后端独立 `grade` 接口，前后端分离
- **Prompt 工程**：角色设定（资深技术面试官）+ 质量要求（干扰项迷惑性、解析 100-200 字）+ 难度控制

## 🚀 快速开始

### 环境要求
- Python 3.10+
- DeepSeek API Key（[platform.deepseek.com](https://platform.deepseek.com)）

### 安装运行

```bash
# 1. 配置 API Key（编辑 app/secret.py）
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxx"

# 2. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install fastapi "uvicorn[standard]" openai

# 3. 启动（或直接双击 start.bat）
python -m uvicorn app.main:app --port 8060
```

浏览器打开 <http://127.0.0.1:8060> 即可使用。

## 📁 项目结构

```
ai-quiz-master/
├─ start.bat              # Windows 一键启动
├─ app/
│  ├─ main.py            # FastAPI 入口
│  ├─ routes.py          # REST 接口（/quiz/generate、/quiz/grade）
│  ├─ quiz.py            # AI 出题引擎（结构化输出 + 判题讲解）
│  ├─ secret.py          # API Key 配置（已被 .gitignore 保护）
│  └─ static/
│      └─ index.html     # 前端单页应用
```

## 🔌 API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/quiz/generate` | 出题：`{topic, num, difficulty}` → 选择题列表 |
| POST | `/quiz/grade` | 判题：`{question, answer}` → 对错 + 解析 |

## ⚠️ 免责声明

- 本平台所有内容（题目、解析、学习路线、评分）均由 **AI 模型自动生成**，仅供学习参考，**不构成任何学术或职业保证**；如发现不准确之处，请以权威教材和官方文档为准。
- 您的学习进度、答题历史与上传的项目材料**仅存储在本机**（SQLite 数据库 + 浏览器 localStorage），不会上传到任何服务器；部署此项目不会携带他人的数据。
- 本项目仅供学习交流使用，作者不对使用本平台产生的任何后果承担责任。


## 📄 License

[MIT](LICENSE)
