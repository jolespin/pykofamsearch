##### Daily Change Log:

* [2024.11.8] - Changed `enzyme_commissions` type in `reformat_pykofamsearch` from `set` to `list` for consistency with `veba --module annotate`
* [2024.11.7] - Added enzyme commission (EC) identifiers to `pykofamsearch`/`reformat_pykofamsearch` output and deprecated `reformat_enzymes.py`
* [2024.11.7] - Added online (download) and offline modes to `serialize_kofam_models` and automatically parsed enzyme commission (EC) identifiers
* [2024.10.18] - Uses entry points for executables instead of copying scripts to bin/
* [2024.7.15] - Added assertion to check that `name_to_hmm` dictionary is not empty which can happen if `--profiles` are the wrong directory [Issue #5](https://github.com/jolespin/pykofamsearch/issues/5)
* [2024.7.15] - Added `scaled_threshold` and prevent scaled threshold from compoundin in [Pulls #2,3,6](https://github.com/jolespin/pykofamsearch/pull/6)
* [2024.7.8] - Added `--threshold` argument and fixed `missing_kos` error.
* [2024.4.25] - Changed default version of PyHmmer to 0.10.12 because of [PyHmmer Issue #67](https://github.com/althonos/pyhmmer/issues/67)

##### Pending
* Add script to download data and transform metadata table to include a column for EC
* Add length cutoff option
* Add enzyme information to relevant KOs during serialization
* Add `bin/` directory and move executables to it.

