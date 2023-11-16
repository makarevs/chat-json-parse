"""
Copyright © 2021 EPAM Systems, Inc. All Rights Reserved. All information
contained herein is, and remains the property of EPAM Systems, Inc. and/or
its suppliers and is protected by international intellectual property law.
Dissemination of this information or reproduction of this material is strictly
forbidden, unless prior written permission is obtained from EPAM Systems, Inc
"""
# # __all__ = [langSubtag, langTag, langTags]


# import os
# import sys
from pathlib import Path
# from typing import Tuple  # , Union List, Optional,
from pydantic import BaseModel  # , ValidationError, validator
# import math
# import numpy as np
import pandas as pd
# from functools import lru_cache
# from time import perf_counter, perf_counter_ns
# from contextlib import contextmanager
# import inspect
import logging
# import requests
from typing import Union, List, Dict, Optional, Tuple, Any, Literal
# import pprint


# from python.utils.utils import (
#     OCB,
#     CCB,
# )

logger = logging.getLogger(__name__)


TRIM_CHARS = " \n\r\t" + chr(160)


def trim(s: str, what_to_trim: str = TRIM_CHARS) -> str:  # -> Tuple[str, str]:
    import re

    if s:
        s = re.sub(f"[{what_to_trim}]+", " ", s)
        s = s.strip()
    else:
        s = ""
    return s  # , func_name()


def timestamp_now_tz() -> pd.Timestamp:
    from datetime import datetime

    # use this extension and it adds the timezone
    tznow = datetime.now()  # .astimezone()
    # logger.debug(tznow.isoformat())
    # 2020-11-05T06:56:38.514560-08:00
    # It shows that it does have a valid timezone
    # type(tznow.tzinfo)
    # <class 'datetime.timezone'>
    return pd.Timestamp(tznow)


def func_name():
    """Returns the name of the function where it is found"""
    import inspect

    return inspect.currentframe().f_back.f_code.co_name


def dt_prefix(msecs=False, secs=True, time=True, sep="-", in_pfx_sep="_"):
    """Return date-time prefix preserve creation time in their names"""
    import datetime

    trunc_chars_num = 0
    fmt = "%y%m%d"
    if time:
        if secs:
            fmt = fmt + in_pfx_sep + "%H%M%S"
        else:
            fmt = fmt + in_pfx_sep + "%H%M"
    if msecs:
        fmt = fmt + in_pfx_sep + "%f"
        trunc_chars_num = 3
        pfx = datetime.datetime.now().strftime(fmt)[:-trunc_chars_num]
    else:
        pfx = datetime.datetime.now().strftime(fmt)
    return pfx + sep


def frames_to_excel(
    dfs: Dict[str, pd.DataFrame],
    excel_book_name: Union[str, Path],
    cols: Dict[str, list] = None,  # columns to enforce as strings
    all_to_str: bool = False,
    add_datetime: bool = False,
    force_folder: Union[str, Path] = None,
    add_not_replace_suffix: bool = False,  # if non-excel extension, add
    fail: bool = True,  # Raise exception if failed
    quiet: bool = False,  # do not generate messages. Does not override 'fail'
) -> bool:
    """Dump the whole search dataframe to Excel"""

    OK = False
    msg = ""
    if force_folder:
        folder = Path(force_folder)
    else:
        folder = Path(excel_book_name).parent
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        msg = f"Error creating folder '{folder}'. {e}"
        logger.error(msg)
    if msg == "":

        excel_suffix = ".xlsx"
        have_suffix = Path(excel_book_name).suffix.lower()
        # add_not_replace_suffix = True
        filename = Path(excel_book_name).name
        if have_suffix != excel_suffix:
            if add_not_replace_suffix:
                new_filename = Path(f"{filename}{excel_suffix}")
            else:
                new_filename = Path(filename).with_suffix(excel_suffix)
            if not quiet:
                msg = (
                    "Changing the name of the file to be saved "
                    f"from '{filename}' to '{new_filename}'."
                )
                logger.warning(msg)
                msg = ""
            filename = str(new_filename)
        file_name = filename
        # file_name = (
        #     f"{Path(Path(excel_book_name).stem).with_suffix('.xlsx')}"
        # )
        if add_datetime:
            file_name = Path(f"{dt_prefix()}{file_name}")
        excel_book_name = folder / file_name

    if msg == "":
        attempt = 0
        while attempt < 2:  # Give chance to close Excel in debug mode
            attempt += 1
            try:
                writer = pd.ExcelWriter(
                    str(excel_book_name), 
                    engine="xlsxwriter",
                )
            except Exception as e:
                if not quiet:
                    msg = (
                        "Error initializing ExcelWriter "
                        "(check if Excel file in opened in Excel) with"
                        f" '{excel_book_name}'. {e}"
                    )
                    logger.error(msg)
                if fail and attempt >= 2:
                    raise  # e(msg)
    for sheet_name, data in dfs.items():
        if data is None:
            continue
        if msg != "":
            break
        if cols is not None:
            # df.dtypes
            if all_to_str:
                cols = {}
                cols[sheet_name] = data.columns.tolist()
        # for col in cols:
        if cols is not None and cols.get(sheet_name, None) is not None:
            try:
                data[cols[sheet_name]] = data[cols[sheet_name]].astype(str)
            except Exception as e:
                msg = (
                    f"Failed to convert columns ({cols[sheet_name]})"
                    f" of dataframe to string type. {e}"
                )
                if not quiet:
                    logger.error(msg)
                if fail:
                    raise e(msg)
        try:
            data.to_excel(writer, sheet_name=sheet_name)
        except Exception as e:
            if not quiet:
                msg = (
                    f"Error writing to sheet '{sheet_name}'"
                    f" in {excel_book_name}. {e}"
                )
                logger.error(msg)
            if fail:
                raise ValueError(msg)
    # Close the Pandas Excel writer and output the Excel file.
    if msg == "":
        try:
            # writer.save()  # Deprecated
            writer.close()
        except Exception as e:
            if not quiet:
                msg = f"Error saving to '{excel_book_name}'. {e}"
                logger.error(msg)
            if fail:
                raise ValueError(msg)
    # try:  # ...Even in the face of previous errors
    #     # D:\Miniconda3\envs\nlp\lib\site-packages\xlsxwriter
    #       \workbook.py:338:
    #     # UserWarning: Calling close() on already closed file.
    #     writer.close()
    #     OK = True
    # except Exception as e:
    #     if not quiet:
    #         msg = f"Error closing '{excel_book_name}'. {e}"
    #         logger.error(msg)
    #     if fail:
    #         raise e(msg)
    return OK



def check_dim(v):
    from six import string_types, text_type, integer_types

    if isinstance(v, string_types + (text_type,)):
        length = None
    else:
        if isinstance(v, integer_types + (float,)):
            length = None
        else:
            # Still try avoiding exception, to allow Raised Exceptions in Code
            if ("len" in v.__dir__()) or ("__len__" in v.__dir__()):
                try:  # ducktype, whoever defines len()
                    length = len(v)
                except Exception:
                    length = None
            else:
                length = None
    return length


def to_df(
    results_object: Union[str, list, dict, pd.Series, pd.DataFrame],
    array_is_vertical: bool = False,
    column_key: Optional[Union[str, List[str]]] = None,  # None to retain
    row_label: Union[int, str] = 0,
    default_columns_key: str = "result",
    squeeze: bool = False,  # ensure 1 row height
    strict_1d: bool = False,  # Make true to raise exceptions, if taller
    quiet: bool = False,  # do not spill warnings
) -> pd.DataFrame:
    """Transform any 0D or 1D data structure to horizontal dataframe.

    ...suitable for appending to accumulating data set
    Accepts any standard data structure.
    Use None to retain original column names (in dict, df, series)
    """

    # Prep some values we will need
    # type_results_object = str(type(results_object)).split("'")[1]
    if not row_label:
        row_label = 0
    if not column_key:
        column_key = default_columns_key
    if not column_key:  # if someone None'd default_columns_key
        column_key = "result"

    if isinstance(results_object, str):
        d = {column_key: [results_object]}
        df = pd.DataFrame(d, index=[row_label])
    elif isinstance(results_object, (list, tuple)):
        length = check_dim(results_object)
        num_digs = len(str(length - 1))  # math.ceil(math.log(length, 10))
        if length == 1:
            d = {column_key: list(results_object)}
        else:
            d = {
                f"{column_key}{str(k).zfill(num_digs)}": [results_object[k]]
                for k in range(length)
            }
        df = pd.DataFrame(d, index=[row_label])
    elif isinstance(results_object, dict):
        for i, (k, v) in enumerate(results_object.items()):
            length = check_dim(v)
            if length and length > 1 and squeeze:
                msg = (
                    f"Element {k} in position {i} is non-scalar"
                    f" (length {length}): {OCB}{k}: {v}{CCB}"
                )
                if not quiet:
                    print(msg)
                    logger.error(msg)
                if strict_1d:
                    raise ValueError(msg)
        d = {
            k: v if check_dim(v) == 1 or not squeeze
            # we want a 1-row df.to_df to remain one-row
            else [v]  # otherwise force to one-row
            for k, v in results_object.items()
        }
        df = pd.DataFrame(d, index=[row_label])
    elif isinstance(results_object, pd.Series):
        df = results_object.to_frame().transpose()
    elif isinstance(results_object, pd.DataFrame):
        # With DataFrame want it horizontal
        rows, columns = results_object.shape
        if rows > 1 and (squeeze or strict_1d):
            msg = (
                f"shape of DataFrame is {(rows, columns)}. Will"
                " squeeze each column to one dataframe array element"
            )
            print(msg)
            logger.error(msg)
            if strict_1d:
                raise ValueError(msg)
            # values = results_object.values  # to work with numpy for speed
            cols = results_object.columns.tolist()
            dd = {}
            for col in cols:
                dd[col] = [results_object[col].values.tolist()]
            df = pd.DataFrame().from_dict(dd)
            df = df[cols]  # re-sort tp original order
        else:
            df = results_object
    else:
        msg = (
            "Do not know how to transform results"
            f" of type '{type(results_object)}' to Pandas DataFrame."
        )
        logger.error(msg)
        raise ValueError(msg)

    length = check_dim(row_label)
    if (row_label is not None) and not length:  # row label defined and scalar
        if len(df) == 1:
            df.index = [row_label]
        else:
            pass  # ignore label, warned of multi-rows elsewhere

    if array_is_vertical:
        # Label will go to rows now
        df = df.transpose()

    results_object = df  # .to_dict()

    return results_object




def dump_data(
    results_object: Union[str, list, dict, pd.Series, pd.DataFrame],
    file_name: Union[Path, str],
    sheet: str = None,
    to_con: bool = True,
    to_txt: bool = False,
    to_tsv: bool = False,
    to_excel: bool = True,
    date_time_prefix: bool = False,
    array_is_vertical: bool = False,
    squeeze: bool = False,  # Make true to enforce 1-D horizontal
    strict_1d: bool = None,  # Make True to raise on multi-row 2D objects
):
    """Write results to disk

    Accepts any standard data structure.
    """

    type_results_object = str(type(results_object))
    pfx = dt_prefix() if date_time_prefix is True else ""
    stem = Path(file_name).stem
    file_path_base_name = Path(GO.f.OUTPUT_DIR.path) / f"{pfx}{stem}"
    text_output = file_path_base_name.with_suffix(".txt")
    tsv_output = file_path_base_name.with_suffix(".tsv")
    excel_output = file_path_base_name.with_suffix(".xlsx")
    if sheet is None:
        sheet = stem

    # Convert object to horizontal 1-row dd
    results_object = to_df(
        results_object,
        array_is_vertical,
        strict_1d=strict_1d,
        squeeze=squeeze,
    )

    msg = None
    if to_con:
        try:
            # with open('output.txt', 'wt') as out:
            pp = pprint.PrettyPrinter(indent=4, compact=False)
            pp.pprint(results_object)
        except Exception as e:
            msg = (
                f"Failed writing {type_results_object}"
                f"->{type(results_object)} results"
                f" to text file '{text_output}'. {e}"
            )
            logger.error(msg)
    if to_txt:
        try:
            # with open('output.txt', 'wt') as out:
            outf = open(text_output, "w", errors="backslashreplace")
            ppf = pprint.PrettyPrinter(stream=outf)
            ppf.pprint(results_object)
            outf.close()
        except Exception as e:
            msg = (
                f"Failed writing {type_results_object}"
                f"->{type(results_object)} results"
                f" to text file '{text_output}'. {e}"
            )
            logger.error(msg)
    if to_tsv:
        try:
            results_object.to_csv(tsv_output, sep="\t")
        except Exception as e:
            msg = (
                f"Failed writing {type_results_object}"
                f"->{type(results_object)} results"
                f" to TSV file '{tsv_output}'. {e}"
            )
            logger.error(msg)
    if to_excel:
        try:
            OK = frames_to_excel(
                dfs={sheet: results_object},
                excel_book_name=excel_output,
                add_datetime=False,
                force_folder=None,
            )
            if OK:
                pass
        except Exception as e:
            msg = (
                f"Failed writing {type_results_object}"
                f"->{type(results_object)} results"
                f" to Excel file '{excel_output}'. {e}"
            )
            logger.error(msg)
    if msg:
        # print(msg)
        # logger.error(msg)
        raise IOError(msg)


class RowAccumulator(BaseModel):
    """DataFrame growing by the Series-rows, with possibly different columns"""

    df: pd.DataFrame = None  # pd.DataFrame()
    current_row: int = 0

    def add_row(
        self,
        row: Union[str, dict, list, pd.Series, pd.DataFrame],
        need_flattening: bool = False,
        key: str = "result",
        quiet: bool = False,
    ):
        """Append the row to the current collection"""
        # d = to_dict(row, array_is_vertical=False, key=key)
        # d = {k: [v] for k, v in d.items()}  # "column" under each header
        # d2: pd.DataFrame = pd.DataFrame(d, index=[self.current_row])
        d2 = to_df(
            row,
            array_is_vertical=False,
            column_key=key,
            row_label=self.current_row,
            squeeze=True,
            quiet=quiet,
        )
        self.current_row += 1

        if self.df is None or len(self.df) == 0:
            self.df = d2
        else:
            if self.df.columns.tolist() == d2.columns.tolist():
                self.df = self.df.append(d2)
            else:
                # Align columns: calculate if d2 has extra columns
                cols_to_add_to_df = [
                    c
                    for c in d2.columns.tolist()
                    if c not in self.df.columns.tolist()
                ]
                if cols_to_add_to_df:
                    self.df[[cols_to_add_to_df]] = None
                # Align columns: calculate if self.df has extra columns
                cols_to_add_to_d2 = [
                    c
                    for c in self.df.columns.tolist()
                    if c not in d2.columns.tolist()
                ]
                for new_col in cols_to_add_to_d2:
                    d2[new_col] = None
                # Now have same set of columns, only reorder before append
                self.df = self.df.append(d2[self.df.columns])

                # # NOTE: If cells contain lists, below merge will fail
                # self.df = self.df.merge(
                #     d2,
                #     on=list(
                #         set(self.df.columns.tolist()).intersection(
                #             set(d2.columns.tolist())
                #         )
                #     ),
                #     how="outer",
                # )

    def dump(
        self,
        results_object: Union[str, list, dict, pd.Series, pd.DataFrame],
        file_name: Union[Path, str],
        sheet: str = None,
        to_con: bool = True,
        to_txt: bool = False,
        to_tsv: bool = False,
        to_excel: bool = True,
        date_time_prefix: bool = True,
        array_is_vertical: bool = True,
    ):
        """Write results to disk

        Accepts any standard data structure.
        """

        dump_data(
            results_object=results_object,
            file_name=file_name,
            sheet=sheet,
            to_con=to_con,
            to_txt=to_txt,
            to_tsv=to_tsv,
            to_excel=to_excel,
            date_time_prefix=date_time_prefix,
            array_is_vertical=array_is_vertical,
        )

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True  # TODO: write validator

