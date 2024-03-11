import os
import time

import shutil
import questionary
from colorama import Style, Fore

from tkinter import filedialog
from tkinter import messagebox
from tkinter.messagebox import showwarning
import sys
from .make_app import make_app

__all__ = ["make_app"]


# supress TK_SILENCE_DEPRECATION=1 warning
os.environ["TK_SILENCE_DEPRECATION"] = "1"


def _copy_file(source, destination):
    shutil.copy(source, destination)


def progress_bar(duration):
    bar_width = 50

    interval = 0.1

    num_steps = int(duration / interval)

    for i in range(num_steps + 1):
        progress = i / num_steps
        bar = (
            "["
            + "#" * int(progress * bar_width)
            + "-" * (bar_width - int(progress * bar_width))
            + "]"
        )
        sys.stdout.write("\r" + "Progress: {:3.0f}% {}".format(progress * 100, bar))
        sys.stdout.flush()
        time.sleep(interval)

    print("\nCompleted!")


def show_information(title: str, message: str) -> None:
    messagebox.showinfo(title, message)


def copy_app_files(
    app_dir=None, config_file=None, data_files=None, keyfile=None, dest=None
):
    if app_dir is None:
        app_dir = questionary.text(
            "Please specify the desired name for the application",
            validate=lambda text: len(text) > 0,
        ).ask()

    if config_file is None:
        show_information(
            "yaml file",
            "Kindly select your survey.yaml file using the file selection tool",
        )
        filetypes = [("YAML files", "*.yaml")]
        config_file = select_file("survey.yaml", filetypes)

    if data_files is None:
        show_information(
            "csv file(s)",
            "Next, please choose all the necessary input CSV files by using the file selection tool",
        )
        filetypes = [("CSV files", "*.csv")]
        data_files = select_file("data csv", filetypes=filetypes, multiple=True)

    if keyfile is None:
        show_information(
            "Keyfile json",
            "Next, please select your keyfile.json file using the file selection tool",
        )
        filetypes = [("JSON files", "*.json")]
        keyfile = select_file("keyfile.json", filetypes)

    if dest is None:
        show_information(
            "Destination dir",
            "Now, please select the destination directory where you would like the application to be located",
        )
        dest = select_directory()

    default_survey_path = os.path.join(os.path.dirname(__file__), "survey.yaml")
    default_csv_dir = os.path.join(os.path.dirname(__file__), "data")
    default_keyfile_path = os.path.join(os.path.dirname(__file__), "keyfile.json")

    print(Style.BRIGHT + f"Creating app at {dest}")

    if app_dir and not os.path.exists(os.path.join(dest, app_dir)):
        os.makedirs(os.path.join(dest, app_dir))

    app_dir = os.path.join(dest, app_dir)

    if config_file is None:
        config_file = default_survey_path
        _copy_file(config_file, app_dir)
    else:
        for config in config_file:
            _copy_file(config, app_dir)

    data_directory_path = os.path.join(app_dir, "data")
    if not os.path.exists(data_directory_path):
        os.makedirs(data_directory_path)

    if data_files is None:
        files = os.listdir(default_csv_dir)
        for file in files:
            file_path = os.path.join(default_csv_dir, file)
            if os.path.isfile(file_path):
                _copy_file(file_path, data_directory_path)
    else:
        for data_file in data_files:
            _copy_file(data_file, data_directory_path)

    if keyfile is None:
        keyfile = default_keyfile_path
        _copy_file(keyfile, app_dir)
    else:
        for file in keyfile:
            _copy_file(file, app_dir)

    file_contents = """\
import fieldsurveys

app = fieldsurveys.make_app(survey_path="survey.yaml", csv_dir="data", keyfile_path="keyfile.json")
    """

    with open(os.path.join(app_dir, "app.py"), "w") as file:
        file.write(file_contents)

    requirements = """\
fieldsurveys
        """

    with open(os.path.join(app_dir, "requirements.txt"), "w") as file:
        file.write(requirements)

    progress_bar(1)
    print(Style.BRIGHT + f"App created at {app_dir}")
    print(
        Style.BRIGHT
        + f"Navigate to {app_dir} and run the command below to run the app locally"
    )
    print(Fore.YELLOW + "python -m shiny run app.py")


def select_directory() -> str:
    directory_path = filedialog.askdirectory(title="Select Directory")

    if directory_path:
        return directory_path
    else:
        showwarning(
            "No directory selected",
            "Directory needs to be selected in order to proceed",
        )
        sys.exit(1)


def select_file(file_type: str, filetypes: list, multiple: bool = False) -> str:
    file_path = filedialog.askopenfilenames(
        title=f"Select {file_type} File", filetypes=filetypes, multiple=multiple
    )

    if file_path:
        return file_path

    else:
        showwarning(
            "No file(s) selected",
            f"{file_type} file needs to be selected in order to customize app.\n Using default version instead",
        )
        return None
