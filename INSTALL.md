# 安装说明

当前仓库现在可以直接使用 `pip install -e .` 安装。关键点是：所有命令都要在 QUANTAXIS 实际使用的同一个 Python 环境里执行。

## 1. 确认 Python 解释器

Windows 上可能会误用到 WindowsApps 的 `python.exe`。先确认路径：

```powershell
Get-Command python
where.exe python
```

如果 QA 环境用的是 Anaconda，建议直接写完整路径，例如：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' -m pip --version
```

后续命令里的 `python` 都应替换成同一个解释器。

## 2. 先移除环境里的 pip 版 pytdx

在同一个 Python 环境里执行，例如：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' -m pip uninstall -y pytdx
```

如果提示仍然安装了，就重复执行，直到显示未安装。

## 3. 安装当前本地仓库

在仓库根目录执行：

```powershell
cd E:\develop\quant\pytdx
& 'E:\ProgramData\anaconda3\python.exe' -m pip install -e .
```

如果你不需要 editable 模式，也可以改成：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' -m pip install .
```

## 4. 验证导入是否指向本地仓库

```powershell
& 'E:\ProgramData\anaconda3\python.exe' -c "import pytdx; print(pytdx.__file__)"
```

输出应指向 `E:\develop\quant\pytdx\...`。

也可以使用仓库内的检查脚本：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' scripts\verify_local_install.py
```

## 5. 如果 editable 安装被旧包遮蔽

如果 `pip show pytdx` 显示 editable project location 是本仓库，但 `import pytdx` 仍指向类似：

```text
E:\ProgramData\anaconda3\Lib\site-packages\pytdx\__init__.py
```

说明全局 `site-packages` 里有旧目录残留。确认路径无误后再清理：

```powershell
Remove-Item -Recurse -Force E:\ProgramData\anaconda3\Lib\site-packages\pytdx
Remove-Item -Recurse -Force E:\ProgramData\anaconda3\Lib\site-packages\pytdx-*.dist-info
```

然后重新安装并验证：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' -m pip install -e E:\develop\quant\pytdx
& 'E:\ProgramData\anaconda3\python.exe' scripts\verify_local_install.py
```

## 6. QA 兼容 smoke 测试

脚本默认会读取 `E:\develop\quant\qa_test\.env`，并把 QUANTAXIS 的 home 目录切到仓库内的 `.qa_home`，避免碰到 `C:\Users\kite\.quantaxis` 的旧配置。

在安装了 QUANTAXIS 的环境中执行：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' scripts\qa_compat_smoke.py --mode qa --stock-ip 119.97.185.59 --stock-port 7709 --future-ip 121.37.232.167 --future-port 7727
```

旧入口也保留可用：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' tests\test_quantaxis_compatibility.py --mode qa --stock-ip 119.97.185.59 --stock-port 7709 --future-ip 121.37.232.167 --future-port 7727
```

## 7. 如果暂时不能安装

可临时把父目录加入 `PYTHONPATH`：

```powershell
$env:PYTHONPATH="E:\develop\quant;$env:PYTHONPATH"
```
