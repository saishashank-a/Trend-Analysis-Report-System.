# Documentation

Welcome to the Swiggy App Store Review Trend Analysis System documentation.

## Quick Navigation

### For New Users
Start here to get up and running:
1. **[index.md](index.md)** - Project overview and what the system does
2. **[getting-started.md](getting-started.md)** - Installation and setup guide

### For Users
Learn how to use the system:
- **[user-guide.md](user-guide.md)** - Complete usage guide for CLI and Web UI
- **[troubleshooting.md](troubleshooting.md)** - Fix common issues

### For Developers
Understand the system architecture and code:
- **[architecture.md](architecture.md)** - System design and components
- **[data-flow.md](data-flow.md)** - Detailed pipeline explanation
- **[api-reference.md](api-reference.md)** - Code documentation and API endpoints

## Documentation Structure

```
docs/
├── README.md                 # This file
├── index.md                  # Overview and introduction
├── getting-started.md        # Setup and installation (20 min read)
├── user-guide.md             # How to use the system (30 min read)
├── architecture.md           # System design (25 min read)
├── api-reference.md          # Code documentation (35 min read)
├── data-flow.md              # Data pipeline details (20 min read)
└── troubleshooting.md        # Common issues and solutions (15 min read)
```

## Documentation by Role

### Product Manager / Analyst
- Start with: [index.md](index.md)
- Then read: [user-guide.md](user-guide.md)
- Reference: [troubleshooting.md](troubleshooting.md)

### Developer
- Start with: [getting-started.md](getting-started.md)
- Then read: [architecture.md](architecture.md) → [data-flow.md](data-flow.md)
- Reference: [api-reference.md](api-reference.md)

### DevOps / System Admin
- Start with: [getting-started.md](getting-started.md)
- Then read: [architecture.md](architecture.md)
- Reference: [troubleshooting.md](troubleshooting.md)

### QA / Tester
- Start with: [getting-started.md](getting-started.md)
- Then read: [user-guide.md](user-guide.md)
- Reference: [troubleshooting.md](troubleshooting.md)

## Quick Start Paths

### I want to analyze Swiggy reviews (5 minutes)
1. Read [getting-started.md](getting-started.md) → Installation section
2. Run `python main.py`
3. Done!

### I want to understand how it works (30 minutes)
1. [index.md](index.md) → Overview
2. [architecture.md](architecture.md) → System design
3. [data-flow.md](data-flow.md) → Data pipeline
4. Done!

### I want to build on this project (1 hour)
1. [getting-started.md](getting-started.md) → Full setup
2. [architecture.md](architecture.md) → System design
3. [api-reference.md](api-reference.md) → Code reference
4. [data-flow.md](data-flow.md) → Implementation details
5. Start coding!

### I'm getting errors (10 minutes)
1. [troubleshooting.md](troubleshooting.md) → Find your error
2. Follow the solution
3. If not resolved, check [getting-started.md](getting-started.md) for setup verification

## Key Concepts

### Before You Start
Make sure you understand these concepts:

- **LLM Provider**: The AI service that extracts topics (Ollama, Anthropic, or Groq)
- **Caching**: Saves reviews locally to avoid re-fetching (100x faster)
- **Topic Extraction**: AI reads reviews and identifies topics/issues
- **Topic Consolidation**: AI groups similar topics together
- **Canonical Topic**: The "main" version of a topic after consolidation

### Common Terms

| Term | Definition |
|------|------------|
| App ID | Package identifier (e.g., `in.swiggy.android`) |
| Review | User comment from Play Store |
| Topic | Issue/request/feedback extracted from review |
| Canonical Topic | Merged/consolidated version of similar topics |
| Batch Processing | Processing multiple items at once |
| Cache | Local storage of previously fetched data |
| CLI | Command Line Interface (`python main.py`) |
| Web Dashboard | Web interface (`python app.py`) |

## Documentation Stats

- **Total pages**: 7
- **Total words**: ~35,000
- **Total reading time**: ~2.5 hours (full read)
- **Quick start time**: 5-10 minutes
- **Code examples**: 100+
- **Diagrams**: 20+

## File Sizes

| File | Size | Lines | Read Time |
|------|------|-------|-----------|
| index.md | 5.3 KB | 180 | 5 min |
| getting-started.md | 9.8 KB | 360 | 20 min |
| architecture.md | 18.6 KB | 600 | 25 min |
| user-guide.md | 16.7 KB | 550 | 30 min |
| api-reference.md | 19.8 KB | 850 | 35 min |
| data-flow.md | 21.1 KB | 700 | 20 min |
| troubleshooting.md | 17.7 KB | 700 | 15 min |
| **Total** | **109 KB** | **3,940** | **2.5 hrs** |

## Getting Help

If the documentation doesn't answer your question:

1. **Search the docs**: Use Cmd/Ctrl+F in your editor
2. **Check troubleshooting**: [troubleshooting.md](troubleshooting.md) has 50+ solutions
3. **Review code comments**: The code has extensive inline documentation
4. **Test with examples**: All docs include working code examples

## Contributing to Documentation

If you find errors or want to improve the docs:

1. **Typos/errors**: Fix directly in the markdown files
2. **Missing info**: Add sections to appropriate files
3. **New features**: Update relevant docs when adding features
4. **Examples**: Add more examples to [user-guide.md](user-guide.md)

## Documentation Standards

This documentation follows:
- **Markdown syntax**: GitHub-flavored markdown
- **Code blocks**: Language-specific syntax highlighting
- **Examples**: Real, working code snippets
- **Structure**: Clear headings and table of contents
- **Links**: Relative links within docs, absolute for external

## Version

- **Documentation version**: 1.0
- **Last updated**: December 26, 2024
- **Compatible with**: Swiggy Review Analysis System v1.0

## License

This documentation is part of the Pulsegen Technologies AI Engineer Assignment.

---

**Ready to get started?** → [getting-started.md](getting-started.md)

**Want to understand the system?** → [index.md](index.md)

**Having issues?** → [troubleshooting.md](troubleshooting.md)
