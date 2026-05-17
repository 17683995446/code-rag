# Code RAG v13.0 - 项目结构指南

## 核心目录
```
/workspace/code-rag/
├── src/                           # 源代码
│   ├── code_rag/                  # 主要代码库 (v12+ 架构)
│   │   ├── base_layer/            # 基础层
│   │   ├── data_layer/            # 数据层
│   │   ├── processing_layer/      # 处理层
│   │   ├── search_layer/          # 搜索层
│   │   ├── rag_engine/            # RAG引擎
│   │   ├── service_layer/         # 服务层
│   │   ├── middleware_layer/      # 中间件层
│   │   ├── observability_layer/   # 可观测性层
│   │   └── api_layer/             # API层
│   └── api/                       # FastAPI应用
├── tests/                         # 测试
│   ├── unit/                      # 单元测试
│   └── integration/               # 集成测试
├── docs/                          # 文档
├── data/                          # 数据目录
├── visualization/                 # 可视化网站
├── scripts/                       # 工具脚本
└── archive/                       # 归档文件
```

## 已整合的功能
- v11.0: 9层模块化架构
- v12.0: 代码智能理解、NL2Code、语义搜索

## 下一阶段 (v13.0)
- 整合与清理
- 功能完善
- 创新功能
- 用户体验提升
