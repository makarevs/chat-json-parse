import glob
from typing import List, Tuple, Dict
import typer
from pathlib import Path
import json
from chat_model import ChatModel
import pandas as pd
from datetime import datetime
from utils import frames_to_excel, trim
import logging

logger = logging.getLogger(__name__)


def table_sheet_name(ord: int, ord2: int) -> str:
    """Create the sheet name for a numbered table"""

    return f"Table {ord}.{ord2}"


def parse_chat_response(text: str, message_no: int) -> Tuple[List[str], List[Dict[str, pd.DataFrame]]]:
    """process the text response into plain text, and dataframes from table(s)"""

    lines: List[str] = []
    df_tables: List[pd.DataFrame] = []
    message_lines = text.split('\n')

    # Process, line by line identifying the table
    in_table = False
    df_table: pd.DataFrame = None
    for line_no, line in enumerate(message_lines):
        prev_in_table = in_table
        if len(line) > 0:
            if line[0] == line[-1] == '|':
                in_table = True
                row_list = [trim(element) for element in line.split('|')][1:-1]
            if in_table:
                if df_table is None:
                    df_table = pd.DataFrame(columns=row_list)
                    table_name = table_sheet_name(message_no, len(df_tables)+1)
                    # lines.append("")
                    lines.append(f"(See table in sheet '{table_name}')")
                    # lines.append("")
                else:
                    #  Check if divider line
                    if len(''.join([elem.replace('-', '') for elem in row_list])) > 0:
                        # df_table = pd.append([df_table, pd.DataFrame])
                        df_table.loc[len(df_table)] = row_list
            else:
                lines.append(line)
        else:
            lines.append(line)
            in_table = False

        if (not in_table and prev_in_table) or (line_no == len(message_lines)):
            df_tables.append({"name": table_name, "df": df_table})
            df_table: pd.DataFrame = None

    return lines, df_tables


def parse_chat(json_file: Path) -> Tuple[pd.DataFrame, List[List[pd.DataFrame]]]:
    """Read and parse the JSON file from the chat, extracting dialog and tables"""

    dfs_tables: List[pd.DataFrame] = []

    with open(json_file, 'r') as f:
        chat_data = json.load(f)
        my_json_text = json.dumps(chat_data)
        chat = ChatModel(**chat_data)
    # print(my_json_text)
    
    # Parse chat messages into dataframe
    df_chat = pd.DataFrame(columns=["Role", "Text"])
    for message_no, message in enumerate(chat.history[0].messages):
        if message.role == 'user':
            row = {"Role": ["Q"], "Text": [message.content]}
        elif message.role == 'assistant':
            message_lines, df_tables = parse_chat_response(text=message.content, message_no=message_no)
            if df_tables:
                dfs_tables.extend(df_tables)
            row = {
                "Role": ["A"], "Text": [
                    # message.content
                    '\n'.join(message_lines)
                ]
            }
        else:
            row = {"Role": ["?"], "Text": [message.content]}
        df_chat = pd.concat([df_chat, pd.DataFrame.from_dict(row)], ignore_index=True)

    return df_chat, dfs_tables


def get_json_folder(folder: Path = None):
    """Identify the folder to read JSONs from"""

    json_folder = None
    if folder is not None:
        if folder.exists and folder.is_dir():
            json_folder = folder

    if json_folder is None:
        #  Identify the dfeault Download folder
        json_folder = str(Path.home() / "Downloads")

    return json_folder


def get_jsons_list(json_folder: Path = None):
    """Get the list of available JSON files"""

    listFiles = glob.iglob(f'{get_json_folder(json_folder)}/*.json') 
    return listFiles


def start_monitoring(json_folder: Path = None):
    """Monitor the downloads folder for new JSONs from ChatGPR"""

    import os
    import os.path
    # import datetime, time

    OUT_DIR = Path("output")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    quiet = False

    # find the last JSON file in it

    listFiles = get_jsons_list(json_folder)
    if listFiles:
        latestFile = Path(max(listFiles, key=os.path.getctime))
        latestFileTime = os.path.getctime(latestFile)
        out_name = OUT_DIR / f"{datetime.fromtimestamp(latestFileTime).strftime('%y%m%d_%H%M%S')}_{latestFile.with_suffix('.xlsx').name}"
        df_tables: List[pd.DataFrame] = []

        df_chat, df_tables = parse_chat(latestFile)
        dfs = {"Chat": df_chat}
        if df_tables:
            dict_tables = {t['name']:t['df'] for t in df_tables}
            dfs.update(dict_tables)

        # df_chat.to_excel(out_name)
        frames_to_excel(
            dfs=dfs,
            excel_book_name=out_name,
        )
    else:
        if not quiet:
            msg = f"No JSON files in folder '{json_folder}'."
            logger.error(msg)


def show_help():
    """Show command heko"""


def main(json_file: Path = None, monitor: bool = True):
    print("Hello, World")
    if json_file:
        parse_chat(json_file=json_file)
    else:
        if monitor:
            start_monitoring()
        else:
            show_help()

    print("Bye, World")


if __name__ == "__main__":
    typer.run(main)