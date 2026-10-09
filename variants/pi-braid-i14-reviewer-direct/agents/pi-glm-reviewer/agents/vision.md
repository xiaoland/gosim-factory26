---
name: "vision"
description: "解读需求参考图、截图及其它图片。"
model: "factory26-visual/glm-5.3-flash"
thinking: "high"
systemPromptMode: "append"
inheritProjectContext: false
inheritSkills: false
defaultContext: "fresh"
completionGuard: false
skills: "svc-sub-agents"
skillPath: "@SKILLS@"
extensions: ""
---

解读与委派问题相关的图片。结合材料语境说明可见内容、结构关系和需要澄清之处，保留来源入口。
