# AI 刷题面试平台（AI Quiz Master）

一个基于 **DeepSeek 大模型** 的 AI 面试准备神器：从 AI 出题、实时判分、学习路线，到 **全流程 AI 面试官**（语音回答 + 评估报告），一站搞定求职刷题与面试模拟。不限行业、不限岗位——编程、金融、法律、医学、考公都能练。

## 功能亮点

**AI 智能出题**
- 输入任意主题，AI 生成高质量选择题 / 简答题（难度可选：入门 / 进阶 / 困难 / 混合）
- 高质量干扰项 + 每题 100-200 字精讲，答错可追问 AI"为什么我选的错"

**个性化学习路线**
- AI 拆解主题生成分章学习路线，从"开始练习"进题自动更新章节掌握度（答对 80% 即掌握）
- 路线进度可存档、随时恢复，历史路线列表常驻可一键续学

**学习统计与错题本**
- 正确率趋势、各主题掌握度、答题会话统计
- 错题本：一键重练错题、导出 Markdown 错题集

**AI 面试官（全流程模拟）**
- 填目标岗位 + 简历，AI 面试官按「自我介绍 → 项目深挖 → 技术题 → 行为题」逐题拷问
- 每题**实时点评 + 打分**，回答太浅**自动追问**，支持**语音回答**（Web Speech API 中文识别）
- 面试结束生成完整**评估报告**（分维度评分表 / 各题表现 / 改进建议），可导出 MD
- 面试进度自动保存，刷新不丢

**全行业主题 + AI 生成**
- 16 大分类 100+ 预设主题：编程语言 / 数据库 / 计算机基础 / 后端 / 前端 / AI 大模型 / 金融财会 / 法律 / 医学健康 / 教育考试 / 商务职场 / 工程建设 / 人文社科 / 艺术设计 / 生活技能…
- 实时搜索过滤；搜不到？🤖 **AI 自动生成相关主题**，点击即出题

**隐私安全**
- 答题历史 / 面试记录 / 项目材料**仅存本地**（SQLite + 浏览器 localStorage），部署不携带任何个人数据
- DeepSeek Key 由 `.gitignore` 保护，绝不上传

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10 · FastAPI · SQLAlchemy · SQLite |
| AI | DeepSeek API（OpenAI 兼容 SDK，结构化 JSON 输出 + 失败自动重试） |
| 前端 | 原生 HTML / CSS / JavaScript 单页应用（无构建步骤） |
| 语音 | Web Speech API（中文语音识别） |

## 核心设计

```
出题：主题 ──▶ AI 结构化 JSON（重试容错）──▶ 选择题/简答题
答题：作答 ──▶ 即时判分 + 解析 ──▶ 错题本 / 掌握度更新
面试：岗位+简历 ──▶ 逐题拷问 ──▶ 点评+打分+追问 ──▶ 评估报告
```

- **结构化输出**：`response_format=json_object` + 详细 prompt 约束，模型不稳定时自动截取 JSON 片段 + 重试一次
- **AI 面试官状态机**：无状态 API + 前端维护会话，每轮回答由 AI 决定"点评 / 追问 / 进入下一题"，最后汇总生成报告
- **全栈持久化**：答题进度按 tab 独立保存（刷新 / 切换 tab 不丢），路线与面试进度同样可恢复
- **Prompt 工程**：角色设定（资深面试官 / 出题专家）+ 质量约束（干扰项迷惑性 / 解析长度 / 贴合岗位）

## 快速开始

### 环境要求
- Python 3.10+
- DeepSeek API Key（[platform.deepseek.com](https://platform.deepseek.com)）

### 安装运行

```bash
# 1. 克隆项目
git clone https://github.com/Noah-Deleveq/ai-quiz-master.git
cd ai-quiz-master

# 2. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate          # Windows（macOS/Linux: source .venv/bin/activate）
pip install fastapi "uvicorn[standard]" sqlalchemy openai

# 3. 配置 API Key（创建 app/secret.py）
DEEPSEEK_API_KEY = "sk-你的Key"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"

# 4. 启动
.venv\Scripts\python -m uvicorn app.main:app --port 8060
```

浏览器打开 **http://127.0.0.1:8060** 即可使用。

> **Windows**：也可以直接双击根目录 `start.bat` 一键启动。

### 使用示例

1. **主题练习**：点热门主题（或输入任意主题）→ 🚀 开始出题 → 答题判分 → 看解析
2. **学习路线**：输入主题 → 🗺️ 生成学习路线 → 每章"开始练习"，答对 80% 掌握
3. **AI 面试官**：填岗位（如"AI 应用开发工程师"）+ 简历 → 🎙️ 开始面试 → 逐题回答（可 🎤 语音）→ 结束生成评估报告
4. **项目面试模拟**：上传你的项目 README / 源码 → AI 针对项目出题拷问 + 生成项目学习路线

## 项目结构

```
ai-quiz-master/
├─ app/
│  ├─ main.py          # FastAPI 入口
│  ├─ quiz.py          # AI 出题 / 判分 / 答疑引擎（含容错重试）
│  ├─ interview.py     # AI 面试官：题目生成 / 点评追问 / 评估报告
│  ├─ roadmap.py       # 学习路线生成与章节进度
│  ├─ history.py       # 答题历史 / 错题本（SQLite）
│  ├─ materials.py     # 项目材料管理
│  ├─ routes.py        # 全部 REST 接口
│  ├─ secret.py        # 🔑 DeepSeek Key（已被 .gitignore 保护）
│  └─ static/          # 前端单页应用
│      └─ index.html
├─ start.bat           # Windows 一键启动
└─ README.md
```

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/quiz/generate` | 出选择题：`{topic, num, difficulty}` |
| POST | `/quiz/essay/generate` | 出简答题 |
| POST | `/quiz/essay/grade` | AI 评分简答题 |
| POST | `/quiz/explain` | 错题针对性答疑 |
| POST | `/quiz/save` | 保存答题会话 |
| GET | `/history` `/history/{id}` | 历史记录 / 详情 |
| GET | `/stats` | 学习统计 |
| POST | `/roadmap/generate` | 生成学习路线 |
| POST | `/roadmap/{rid}/report` | 汇报章节掌握度 |
| POST | `/topics/suggest` | AI 生成相关主题 |
| POST | `/interview/start` | 开始面试（生成题目） |
| POST | `/interview/answer` | 提交回答（点评+打分+追问） |
| POST | `/interview/report` | 生成面试评估报告 |
| POST | `/materials` | 上传项目材料 |

## 免责声明

- 所有内容（题目、解析、学习路线、面试评分）均由 **AI 自动生成**，仅供学习参考，请以权威资料为准
- 学习数据**仅存本机**，不上传任何服务器

## License

[MIT](LICENSE)