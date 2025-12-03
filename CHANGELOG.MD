# todo:
- Engine:
  - implement support for multiple scrappers
- OfferScrappers:
  - should support filtering offers by multiple languages - python job filtering should not be hard codded
  - scrappers shouldn't implement _fetch_content_page, they should use http client with composition
- add saving results to md file for obsidian to work with
  - reading changes from md file. I want to keep notes and basic informations like if I've applied or not
- basic db support that will store offers
- add http communication client for scrappers
- add single offer engine
- add test offer engine (loading content from html files) - will be useful for testing parsers

# Changelog:

## 0.3.1
- Added better async http client support (HttpxClient)

## 0.3.0
- Added logger support
- Added basic offer ordering (descending by max salary)
- Added offer details scrapping support
- Added justjoinit offer detail parser

## 0.2.0
- Added scrapper execution engine 
- Added justjoinit offer listing scrapper
- Fixed converting salary units for justjoinit hourly offers

## 0.1.0
- Added Docker environments
- Added uv package manager

### Project setup
- Added .pre-commit-config
- Initial project structure
