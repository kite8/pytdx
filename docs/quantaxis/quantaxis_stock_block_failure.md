# QUANTAXIS `save stock_block` failure

## Root cause

`save stock_block` in QUANTAXIS saves two sources in sequence:

1. `QA_fetch_get_stock_block('tdx')`
2. `QA_fetch_get_stock_block('tushare')`

The traceback you saw is not from pytdx TDX block parsing. The TDX part already succeeded.  
The failure happens in the Tushare branch:

- `ts.get_zz500s()` now fails or returns `None`
- `QA_util_to_json_from_pandas(None)` then crashes on `.copy()`

This is not caused by a missing Tushare token. QUANTAXIS calls the old Tushare
API `ts.get_zz500s()`, not Tushare Pro. That legacy function does not read a
token; it downloads an Excel-like file URL and passes it to `pandas.read_excel`.

## Dynamic reproduction

Script:

```powershell
$env:PYTHONPATH='E:\develop\quant'
& 'E:\Anaconda\envs\quantaxis\python.exe' -u scripts\diagnose_quantaxis_stock_block.py `
  --qa-env-file 'E:\develop\quant\qa_test\.env' `
  --qa-home 'E:\develop\quant\pytdx\.qa_home_diag'
```

Observed results:

| Step | Result |
| --- | --- |
| `QA_fetch_get_stock_block('tdx')` | Success, returned `100439` rows with columns `blockname/code/type/source`. |
| `QA_util_to_json_from_pandas(tdx_block)` | Success, converted `100439` rows. |
| `QA_fetch_get_tdx_industry()` | Success, returned `10431` rows. |
| `QATushare.QA_fetch_get_stock_block()` | Prints `Excel file format cannot be determined, you must specify an engine manually.` and returns `None`. |
| `QA_SU_save_stock_block()` with fake Mongo client | Inserts `100439` TDX rows, then fails on Tushare `None` with `'NoneType' object has no attribute 'copy'`. |

The exact URL used by `ts.get_zz500s()` in this environment is:

```text
http://www.csindex.com.cn/uploads/file/autofile/closeweight/000905closeweight.xls
```

Live response inspection:

```text
status=200
content-type=text/html
first-bytes=b'<!DOCTYPE html><'
```

So pandas is being asked to parse an HTML page as Excel. That is why it raises
the engine/format error. Installing a Tushare token will not fix this specific
path.

## Files to patch in QUANTAXIS

- `QUANTAXIS/QAFetch/QATushare.py`
- `QUANTAXIS/QASU/save_tdx.py`

## Minimal fix

### `QUANTAXIS/QAFetch/QATushare.py`

Wrap `ts.get_zz500s()` itself and return `None` cleanly:

```python
def QA_fetch_get_stock_block():
    import tushare as ts
    try:
        csindex500 = ts.get_zz500s()
        if csindex500 is None or len(csindex500) == 0:
            return None
        csindex500['blockname'] = '中证500'
        csindex500['source'] = 'tushare'
        csindex500['type'] = 'csindex'
        csindex500 = csindex500.drop(['date', 'name', 'weight'], axis=1)
        return csindex500.set_index('code', drop=False)
    except Exception as e:
        print(e)
        return None
```

### `QUANTAXIS/QASU/save_tdx.py`

Skip the Tushare block when it is empty or fails:

```python
tdx_block = QA_fetch_get_stock_block('tdx')
if tdx_block is None or len(tdx_block) == 0:
    raise ValueError('tdx stock block is empty')
coll.insert_many(QA_util_to_json_from_pandas(tdx_block))

try:
    tushare_block = QA_fetch_get_stock_block('tushare')
    if tushare_block is not None and len(tushare_block) > 0:
        coll.insert_many(QA_util_to_json_from_pandas(tushare_block))
except Exception as e:
    QA_util_log_info('skip tushare Block: {}'.format(e), ui_log=ui_log)
```

## Temporary workaround

If you only need TDX block data now, call the TDX fetch path directly and skip the Tushare fallback.

## After replacing Tushare with Akshare

I re-ran the flow against the user-modified QUANTAXIS checkout in
`E:\develop\github\QUANTAXIS` and the installed `akshare` package.

Observed behavior:

- `QA_fetch_get_stock_block('tushare')` now returns `500` rows
- The returned frame has columns:
  - `code`
  - `name`
  - `blockname`
  - `source`
  - `type`
- The frame index is `code`
- `QA_SU_save_stock_block()` completes both inserts with a fake client:
  - TDX block: `100439` rows
  - Akshare block: `500` rows

Comparison with TDX output:

- TDX sample keys: `blockname`, `code`, `source`, `type`
- Akshare sample keys: `blockname`, `code`, `name`, `source`, `type`

So the new Akshare path is saveable and index-compatible, but it is not
strictly identical to the TDX schema because it keeps the constituent security
`name` column.
