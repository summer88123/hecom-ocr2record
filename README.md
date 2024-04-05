# 表单识别Demo

## 环境准备

### 创建虚拟环境

要创建虚拟环境，你可以使用随Python一起提供的`venv`模块。

```sh
python3 -m venv venv
```
这将在名为venv的目录中创建一个新的虚拟环境。

### 激活虚拟环境
在你开始安装或使用虚拟环境中的包之前，你需要激活它。激活虚拟环境将把虚拟环境特定的python和pip可执行文件放入你的shell的PATH中。

在macOS和Linux上：
```sh
source venv/bin/activate
```
在Windows上：
```sh
.\venv\Scripts\activate
```
### 安装依赖
此项目使用pip来管理依赖。要安装所有必需的包，请运行：
```sh
pip install -r requirements.txt
```

### 添加环境变量
在根目录创建文件`.env`
添加大模型的API KEY，当前Demo中使用MoonShot，所以需要在配置文件中加入
```
MOONSHOT_API_KEY=your-api-key
```

### 运行项目
要运行项目，使用以下命令：
```sh
streamlit run app.py
```