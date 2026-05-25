# pytdx

这是一个本地 fork，用于兼容 QUANTAXIS 并修复股票列表、板块解析和编码问题。

## 安装

先卸载环境里已有的 pip 版：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' -m pip uninstall -y pytdx
```

然后在仓库根目录安装本项目：

```powershell
cd E:\develop\quant\pytdx
& 'E:\ProgramData\anaconda3\python.exe' -m pip install -e .
```

如果你只想看完整说明，见 [INSTALL.md](INSTALL.md)。

验证当前环境是否导入了本地 fork：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' scripts\verify_local_install.py
```

在已安装 QUANTAXIS 的环境中做兼容 smoke：

```powershell
& 'E:\ProgramData\anaconda3\python.exe' scripts\qa_compat_smoke.py --mode qa --stock-ip 119.97.185.59 --stock-port 7709 --future-ip 121.37.232.167 --future-port 7727
```

脚本会优先读取 `--qa-env-file` 或 `QA_ENV_FILE`，其次自动发现同级 `qa_test/.env`，最后使用进程环境变量；QUANTAXIS home 默认放到仓库内的 `.qa_home`。

## 参考

1. 原作者说明文档：https://rainx.gitbooks.io/pytdx/content/
2. 备份说明文档：https://counsel-chai.gitbook.io/pytdx-1/
3. 原作者代码地址：https://github.com/rainx/pytdx
