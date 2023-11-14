<!--toc:start-->
- [Description](#description)
- [Roadmap](#roadmap)
  - [Core](#core)
  - [Plugins](#plugins)
<!--toc:end-->

# Description

CLI note manager for Zettelkasten-like note-taking.


# Roadmap

## Core
- [x] Add `last_changed_time` in sqlite database
- [x] Support for tags
- [x] Support for backlinks
- [ ] Search for tags, links, words, title, date
- [x] SQLite caching of indexed notes
- [-] Scratchpad for temporary notes
- [x] Support for reindexing
- [-] Support for scratchpad where to save notes not ready
- [ ] Support for TOML configuration
- [ ] Support for using external or internal tool for fuzzy finding/searching (no dependencies)
- [ ] Knowledge graph creation
- [ ] Plugin system

## Plugins
- [ ] AI for categorisation and grouping of notes
- [ ] AI for tag creation
- [ ] AI for summarisation of notes
- [ ] Select multiple notes and summarise them into one
- [ ] PDF summarizer
- [ ] flashcards
- [ ] Daily/Weekly/Monthly knowledge summarization (using git/langchain)
