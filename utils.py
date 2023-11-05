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
# from pydantic import BaseModel  # , ValidationError, validator
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


