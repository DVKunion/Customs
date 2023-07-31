# Customs

<p align="center">
<img src="assets/logo_transparent.png" width="30%" >
</p>

镜像海关 - Github Action自动化 Docker 镜像数据收集与分析，为云安全研究提供数据支持。

基于`GitHub GraphQL API v4` ，获取存在`Dockerfile`的前一天创建的仓库，通过`REST API`去定向搜索具体的`code`，获取所有`FROM`字段

依此来逃过`search code API`最多只能获取到1000个的限制。

## 一些存在的问题：

很多repo没有indexed，导致搜索时报错：

`This repository's code is being indexed right now. Try again in a few minutes.`

search接口的limit为 10次/分钟，只能依照这个速率进行爬取。