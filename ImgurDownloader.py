# import sys
import configparser
import datetime
import imghdr
import itertools
import os
import queue
import threading
import time
import uuid

import requests

if not os.path.isfile("settings.ini"):
    with open("settings.ini", "w") as file:
        file.write(
            """
[DEFAULT]

;Check for missmatch between the Database and the actual files inside of the Archive. 
;check_for_DB_missmatch = False

; Length of string. Example i.imgur.com/AAAAA.jpg
;string_length = 5

; Percentage of CPU to use
;max_threads_percent = 90

; Number of times to run iterations towards new URLS.
; This is mostly for debugging. 
; Set to -1 for infinite iterations
;max_iterations = -1

; Max Queue size:
; max_queue_size = 500

; Max Generation queue size:
; max_combination_gen_size = 500

; File locations:

; Download folder location. 
; DO NOT USE "/" AT THE END!
; To just use Current Dir, enter only a punctationmark.
;download_folder_location    = . 

; If this is just a word, a dir will be created in Current working directory,
; If it is a path it will use the Path.
;download_folder_name = Archive 


;DB_files_path_prefix = DB
;CheckedURLsFile      = 0checkedURLs.txt
;RedirectURLs         = 0RedirectURLs.txt
;ErrorFile            = 0ErrorStings.txt
;RetryStringsFile     = 0RetryStrings.txt

"""
        )
        print(
            "Settings.ini is now created. Rerun the script after editing the settings."
        )


# SETTINGS
# To change these settings, write them as an entry in settings.ini.
# Default settings:
default_settings = {
    "check_for_DB_missmatch": False,
    "string_length": 5,
    "max_threads_percent": 90,
    "max_iterations": -1,
    "download_folder_location": ".",
    "download_folder_name": "Archive",
    "DB_files_path_prefix": "DB",
    "CheckedURLsFile": "0checkedURLs.txt",
    "RedirectURLs": "0RedirectURLs.txt",
    "ErrorFile": "0ErrorStings.txt",
    "RetryStringsFile": "0RetryStrings.txt",
    "max_queue_size": 500,
    "max_combination_gen_size": 500,
}

config = configparser.ConfigParser()
config.read("settings.ini")
check_for_DB_missmatch = int(
    config.get(
        "DEFAULT",
        "check_for_DB_missmatch",
        fallback=default_settings["check_for_DB_missmatch"],
    )
)

string_length = int(
    config.get("DEFAULT", "string_length", fallback=default_settings["string_length"])
)
max_threads_percent = int(
    config.get(
        "DEFAULT",
        "max_threads_percent",
        fallback=default_settings["max_threads_percent"],
    )
)
max_iterations = int(
    config.get("DEFAULT", "max_iterations", fallback=default_settings["max_iterations"])
)

download_folder_name = config.get(
    "DEFAULT", "download_folder_name", fallback=default_settings["download_folder_name"]
)
download_folder_location = config.get(
    "DEFAULT",
    "download_folder_location",
    fallback=default_settings["download_folder_location"],
)
DB_files_path_prefix = config.get(
    "DEFAULT", "DB_files_path_prefix", fallback=default_settings["DB_files_path_prefix"]
)

CheckedURLsFile = f"{download_folder_location}/{DB_files_path_prefix}/{config.get('DEFAULT', 'CheckedURLsFile', fallback=default_settings['CheckedURLsFile'])}"  # noqa: E501
RedirectURLs = f"{download_folder_location}/{DB_files_path_prefix}/{config.get('DEFAULT', 'RedirectURLs', fallback=default_settings['RedirectURLs'])}"  # noqa: E501
ErrorFile = f"{download_folder_location}/{DB_files_path_prefix}/{config.get('DEFAULT', 'ErrorFile', fallback=default_settings['ErrorFile'])}"
RetryStringsFile = f"{download_folder_location}/{DB_files_path_prefix}/{config.get('DEFAULT', 'RetryStringsFile', fallback=default_settings['RetryStringsFile'])}"
max_queue_size = int(
    config.get("DEFAULT", "max_queue_size", fallback=default_settings["max_queue_size"])
)
max_combination_gen_size = int(
    config.get(
        "DEFAULT",
        "max_combination_gen_size",
        fallback=default_settings["max_combination_gen_size"],
    )
)
download_folder = f"{download_folder_location}/{download_folder_name}"
DB_Folder = f"{download_folder_location}/{DB_files_path_prefix}"

CharacterListA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
url_base = "https://i.imgur.com/"


# # File locations:
# DB_files_path = "DB"
# CheckedURLsFile = f"{DB_files_path}/0checkedURLs.txt"
# RedirectURLs = f"{DB_files_path}/0RedirectURLs.txt"
# ErrorFile = f"{DB_files_path}/0ErrorStings.txt"
# RetryStringsFile = f"{DB_files_path}/0RetryStrings.txt"
# File locations:
file_name = ""
# Checked_Strings_File = "checkedURLs.txt"

redirectFileLength = 0
CheckedURLFileLength = 0
ErrorFileLength = 0


# max_threads = int(os.cpu_count() * max_threads_percent / 100)
max_threads = int(os.cpu_count() - 1)
work_queue = queue.Queue(maxsize=max_queue_size)
# queue = queue.Queue()
string_set = set()  # create an empty set to store the strings
threads_amount = 0
total_downloaded = 0
total_tested = 0
archive_files_amount = 0
total_iterations = 0
archive_files_size = ""
latest_string = ""
latest_string_from_File = ""
ErrorLogs = []


current_workers = {}


def compare_files():
    archive_files = []
    checked_files = []

    # Get list of files in Archive folder
    for root, dirs, files in os.walk(download_folder):
        for file in files:
            archive_files.append(file)

    # Get list of files in checkedURLs.txt
    with open(CheckedURLsFile, "r") as f:
        for line in f:
            checked_files.append(line.strip())

    # Find files that exist in checkedURLs.txt but not in Archive folder
    diff_files = set(checked_files) - set(archive_files)

    return diff_files


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


def update_terminal():
    global current_workers
    global total_downloaded
    global total_tested
    global total_iterations
    global threads_amount
    global ErrorLogs
    global archive_files_amount
    global archive_files_size
    global redirectFileLength
    global CheckedURLFileLength
    global ErrorFileLength
    global latest_string
    pppIterations = 0

    estimated_latest_string = get_last_file_name(download_folder)


    while True:
        try:
            # os.system("clr")

            # TODO Make it prettier....
            # terminal_size_width = shutil.get_terminal_size().columns

            # Create the header
            header = "\n\n\n\n\nIMGUR DOWNLOADER\n"
            header += f"Last refresh: {datetime.datetime.now().strftime('%H:%M:%S')}"

            worker_rows = []

            # Create the worker section

            for worker in current_workers.values():
                workerStats = ""
                for item in worker.keys():
                    workerStats = workerStats + f"  {item}: {worker[item]}\n"

                workerBlock = (
                    f"Worker: {worker['WorkerID'][:8].upper()}\n" + workerStats + "\n"
                )

                worker_rows.append(workerBlock)

            # Add the totals row and footer
            totals = f"Current session downloads: {total_downloaded}\n"
            totals += f"Current session URLs tested: {total_tested}\n"
            totals += f"Number of threads: {threads_amount}\n"
            totals += f"Download Folder: {download_folder}\n"

            totals += "\n"
            totals += f"Total iterations: {total_iterations}\n"
            totals += f"Latest Iteration: {latest_string}\n"
            totals += f"Iterations since last refresh: {total_iterations-pppIterations}\n"
            totals += f"Estimated latest string: {estimated_latest_string}\n"

            totals += "\n"
            totals += f"Total number of files in archive folder: {str(archive_files_amount)}\n"
            totals += f"Total size of archive folder (in bytes): {archive_files_size}\n"

            totals += "\n"

            totals += "\n"
            totals += f"Lines in Error registry:                 {ErrorFileLength}\n"

            # Print the full status message
            footer = []
            for error in ErrorLogs:
                footer.append(str(error) + "\n")

            print(f"{header}\n{totals}\n{'Workers:'}\n\n{''.join(worker_rows)}\n")
            if len(footer) >= 1:
                print("Last 3 Error messages:\n")
            for error in footer[-3:]:
                print(str(error) + "\n")

            write_last_info()
            pppIterations = total_iterations
            time.sleep(0.5)


        except Exception as e:
            # print(e)
            write_error_string(error=e)
            raise Exception(e)
            # exit()

def get_last_file_name(directory):
    # Get a list of all files in the directory
    file_list = os.listdir(directory)

    # Sort the files by name
    sorted_files = sorted(file_list)

    # Get the last file in the list
    last_folder_name = sorted_files[-1]

    file_list = os.listdir(f"{directory}\{last_folder_name}")
    
    # Sort the files by name
    sorted_files = sorted(file_list)
    
    # Get the last file in the list
    last_file_name = sorted_files[-1]
    return last_file_name.split(".")[0]



def fetch_checked_file(StringX):
    file_prefix = StringX[
        :-2
    ]  # Use the first N-2 characters of the string as the prefix for the file name
    # Construct the file path using the prefix
    file_path = f"{DB_Folder}/{file_prefix}.txt"
    return file_path


def is_string_used_IO(StringX):
    sub_folder = StringX[
        :-2
    ]  # Use the first N-2 characters of the string as the prefix for the file name
    file_path = (
        # Construct the file path using the prefix
        f"{download_folder}/{sub_folder}"
    )

    # temp = os.path.abspath(file_path)
    # temp2 = os.listdir(os.path.abspath(file_path))
    try:
        # for filename in temp2:
        for filename in os.listdir(os.path.abspath(file_path)):
            if StringX in filename.split(".")[0]:
                return True

        return False
    except FileNotFoundError:
        return False


def is_string_used(string="", firstRun=False):
    # if not os.path.exists(Checked_Strings_File):
    #     open(Checked_Strings_File, 'w').close()

    try:
        if is_string_used_IO(string):
            return True
        with open(fetch_checked_file(string), "r") as f:
            if string in f.read():
                return True
            # return string in f.read()
    except FileNotFoundError:
        with open(fetch_checked_file(string), "w+") as f:
            f.write("")
        is_string_used(string, firstRun=firstRun)


def is_url_redirect(string):
    if not os.path.exists(RedirectURLs):
        open(RedirectURLs, "w").close()

    with open(RedirectURLs, "r") as f:
        # temp = string in f.read()
        return string in f.read()


def write_string(string):
    with open(fetch_checked_file(string), "a+") as f:
        f.write(string + "\n")
    # with open(Checked_Strings_File, 'a') as f:
    #     f.write(string + '\n')


def write_error_string(error="", message="", StringX=""):
    with open(ErrorFile, "a+") as f:
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")

        f.write(f"{current_time}: {message}. Error: {str(error)}\n")
    if not StringX == "":
        write_string(StringX)


def write_redirect_url(string):
    with open("RedirectURLs.txt", "a+") as f:
        f.write(string + "\n")
    write_string(string)


def write_retry_strings(string):
    with open("RetryStrings.txt", "a+") as f:
        if string.endsWith("\n"):
            f.write(string)
        f.write(string + "\n")
    write_string(string)


# Check files already downloaded still exists
# def compare_files():
#     archive_files = []
#     checked_files = []

#     # Get list of files in Archive folder
#     for root, dirs, files in os.walk(download_folder):
#         for file in files:
#             archive_files.append(file.split(".")[0])

#     # Get list of files in checkedURLs.txt
#     with open(CheckedURLsFile, "r") as f:
#         for line in f:
#             checked_files.append(line.strip())

#     # Find files that exist in checkedURLs.txt but not in Archive folder
#     diff_files = set(checked_files) - set(archive_files)

#     # Remove entries that are missing in the archive list from the checked_files list
#     for file in diff_files:
#         checked_files.remove(file)

#     # Remove entries that are missing in the archive list from the "checkedURLs.txt" file
#     with open(CheckedURLsFile, "w") as f:
#         for file in checked_files:
#             f.write(file + "\n")

#     return diff_files


def download_image(string, response, current_worker_info):
    global total_downloaded

    update_worker_status("Getting file extension", current_worker_info)
    file_extension = get_file_extension(response)
    file_name = string + file_extension
    update_worker_status(
        f"Got file extension and filename {file_name}", current_worker_info
    )
    dir_name = os.path.join(download_folder, file_name[:3])

    update_worker_status("Configurating Filepath", current_worker_info)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    file_path = os.path.join(dir_name, file_name)

    update_worker_status("Writing image to file", current_worker_info)
    with open(file_path, "wb") as f:
        f.write(response.content)
        # print(f"Downloaded image {file_name}")
        write_string(string)
    total_downloaded += 1


def get_file_extension(response):
    image_type = imghdr.what(None, h=response.content)
    if image_type:
        extension = "." + image_type
    else:
        extension = ".jpg"
    return extension


# def update_worker_status(message, workerID):
def update_worker_status(message, current_worker_info):
    global current_workers

    current_workers[current_worker_info["WorkerID"]]["current_message"] = message

    # for index, worker in enumerate(current_workers.items()):
    #     if current_worker_info["WorkerID"] in worker:
    #         workerIndex = index
    # try:
    #     current_workers[workerIndex]["current_message"] = message
    # except Exception as e:
    #     pass
    #     # raise Exception

    # global current_workers
    # global ErrorLogs
    # # current_workers[workerID][3] = message
    # try:
    #     current_workers[workerID]["current_message"] = message
    #     cworker = current_workers[workerID]
    #     message = cworker["current_message"]
    #     current_message = cworker["current_message"]
    # except IndexError as e:
    #     if not "cworker" in locals():
    #         cworker = "ERROR EMTPY"
    #     if not "message" in locals():
    #         message = "ERROR EMTPY"
    #     write_error_string(f"Error writing Error: \nCurrent_workers: {current_workers}\nWorker: {cworker}\nCurrent Message: {current_message}\n New Message: {message}\nRaised Error:\n {e}")
    # except Exception as e:
    #     print(e)
    #     print()


# def check_links_get_respose(StringX):
#     url = url_base + StringX + ".jpg"
#     response = requests.get(url, allow_redirects=False)
#     return response


def check_links(current_worker_info, retries=0, response=None):
    global total_tested
    global current_workers
    global ErrorLogs

    # Set string X from current_worker_info
    StringX = current_worker_info["StringX"]
    # worker_status = current_worker_info["current_message"]
    # workerID = current_worker_info["WorkerID"]

    if retries > 3:
        try:
            update_worker_status(
                "String failed. Writing down string and closing down.",
                current_worker_info,
            )
            write_error_string(
                message=f"Error after trying 3 times. String {StringX}, Response code: {response.status_code}",
                StringX=StringX,
            )
            # write_string(StringX)
            return
        except AttributeError as e:
            update_worker_status(
                "String failed. Writing down string and closing down.",
                current_worker_info,
            )
            write_error_string(
                message=f"Error after trying 3 times. String {StringX}, Response code: NOT AVAILABLE MOST LIKLEY FAILED RESPONSE",
                error=e,
                StringX=StringX,
            )
            # write_string(StringX)
            return

    update_worker_status("Checking if string is already used", current_worker_info)
    if is_string_used(StringX):
        update_worker_status(
            "String is already used. Closing this worker.", current_worker_info
        )
        total_tested += 1
        return

    try:
        response_status = 0
        update_worker_status(
            f"Connecting to URL, retries: {retries}", current_worker_info
        )
        url = url_base + StringX + ".jpg"
        response = requests.get(url, allow_redirects=False, timeout=15)
        response_status = response.status_code
        update_worker_status(
            f"Finished connecting to URL, retries: {retries}", current_worker_info
        )

    except requests.exceptions.SSLError:
        update_worker_status(
            f"Got SSLError. String: {StringX}, . Retries left: {retries}",
            current_worker_info,
        )
        # We have been blocked by the host. Wait for a little bit and try again.
        time.sleep(5)
        retries += 1
        check_links(
            current_worker_info=current_worker_info, retries=retries, response=response
        )

    except HTTPSConnectionPool as e:
        update_worker_status(
            "Got timeout. Adding to Retry list for later.", current_worker_info
        )
        write_error_string(
            message=f"Error with String {StringX}. Got Timeout Error. Adding to ErrorString and Retry List. Error: {e}",
            StringX=StringX,
        )
        write_retry_strings(StringX)
        pass
    except Exception as e:
        update_worker_status(
            "Got Error. Writing down error, and continue.", current_worker_info
        )
        write_error_string(
            message=f"Error with String {StringX}. Could not get response. Error: \n{e}",
            StringX=StringX,
        )
        write_retry_strings(StringX)
        pass

    if response_status == 200:
        update_worker_status(
            "Got Status code 200. Downloading image. ", current_worker_info
        )
        download_image(StringX, response, current_worker_info)
        return

    if response_status == 302:
        update_worker_status("Got Status code 302. Skip this URL ", current_worker_info)
        write_string(StringX)
        total_tested += 1
        return

    if response_status == 429:
        update_worker_status(
            f"Got Status code {response_status}, blocked by host. Retrying",
            current_worker_info,
        )
        # We have been blocked by the host. Wait for a little bit and try again.
        time.sleep(5)
        retries += 1
        check_links(
            current_worker_info=current_worker_info, retires=retries, response=response
        )

    if response_status == 104:
        update_worker_status(
            f"Got Status code {response_status}, Connection Reset From Host. Retries left: {retries}",
            current_worker_info,
        )
        # We have been blocked by the host. Wait for a little bit and try again.
        time.sleep(5)
        retries += 1
        check_links(
            current_worker_info=current_worker_info, retires=retries, response=response
        )

    if response_status == 500:
        update_worker_status(
            f"Got Status code {response_status}, Connection Reset From Host. Retries left: {retries}",
            current_worker_info,
        )
        # We have been blocked by the host. Wait for a little bit and try again.
        time.sleep(5)
        retries += 1
        check_links(
            current_worker_info=current_worker_info, retries=retries, response=response
        )

    update_worker_status(
        f"Got unknow status code: {response_status}. Writing down error, put String into file of strings to try later, then continue.",
        current_worker_info,
    )
    # write_error_string(f"Error with String {StringX}. Got unknown Status code: {response_status}")
    # write_retry_strings(StringX)

    time.sleep(5)
    retries += 1
    check_links(
        current_worker_info=current_worker_info, retries=retries, response=response
    )
    return


def check_links_start(current_worker_info):
    while True:
        current_worker_info["current_message"] = "Now i wait for a job from the Queue!"
        StringX = work_queue.get()
        current_worker_info["StringX"] = StringX
        # current_worker_info["current_message"] = f"Got job with string {StringX}"
        update_worker_status(f"Got job with string {StringX}", current_worker_info)
        check_links(current_worker_info)


# def worker():
#     global ErrorLogs
#     global current_workers
#     global threads_amount

#     WorkerID = threading.current_thread().ident
#     while True:

#         # Get string for worker to use
#         StringX = work_queue.get()

#         # Create a dictionary to hold the current worker's information
#         current_worker_info = {
#             "workerID": WorkerID,
#             "StringX": StringX,
#             "current_message": "Birthed"
#         }

#         current_workers[WorkerID] = current_worker_info

#         threads_amount += 1
#         # check_links(current_worker_info)
#         check_links(current_worker_info)
#         threads_amount -= 1

#         # del current_workers[get_worker_index(StringX)]
#         del current_workers[current_worker_info["workerID"]]
#         work_queue.task_done()


def get_file_length(file):
    line_count = 0
    with open(file, "r") as f:
        for line in f:
            line_count += 1
        return line_count


def fetch_files_number_and_size():
    while True:
        try:
            # Get total number of files and total size of archive folder
            global archive_files_amount
            global archive_files_size
            global redirectFileLength
            global CheckedURLFileLength
            global ErrorFileLength

            archive_files_amount = 0

            # archive_file_limit = 1000000
            # if archive_files_amount >= archive_file_limit:
            #     archive_files_amount = f"Over {archive_file_limit}"
            # else:
            #     archive_files_amount = sum([len(files) for r, d, files in os.walk(download_folder)])

            # redirectFileLength = get_file_length(RedirectURLs)
            # CheckedURLFileLength = get_file_length(Checked_Strings_File)
            ErrorFileLength = get_file_length(ErrorFile)

            # update_terminal()
            # time.sleep(0.1)

        except Exception as e:
            write_error_string(message=f"Error updating stats: {e}")
            raise Exception(e)


def create_strings(current_worker_info):
    global max_iterations
    global total_iterations
    global latest_string
    try:
        update_worker_status(
            message="I will now start generating combinations.",
            current_worker_info=current_worker_info,
        )
        Caught_up_to_previous_value = False

        for combination in itertools.product(CharacterListA, repeat=string_length):
            StringX = "".join(combination)
            latest_string = StringX
            if not Caught_up_to_previous_value:
                if StringX == latest_string_from_File:
                    Caught_up_to_previous_value = True
                if latest_string_from_File == "":
                    pass
                else:
                    continue

            update_worker_status(
                message=f"I have made string {StringX}",
                current_worker_info=current_worker_info,
            )
            total_iterations += 1
            # if firstCheckForChecked:
            if is_string_used(StringX):
                update_worker_status(
                    current_worker_info=current_worker_info,
                    message=f"The String {StringX} was used. Checking next combination.",
                )
                continue
            # else:
            #     firstCheckForChecked = False

            while True:
                if work_queue.full():
                    time.sleep(1)
                else:
                    work_queue.put(StringX)
                    # string_set.add(StringX)
                    max_iterations -= 1
                    # check_links(StringX=StringX)
                    break

            if max_iterations == 0:
                break

        # Wait for all tasks to complete
        work_queue.join()
    except Exception as e:
        # print(e)
        write_error_string(error=e, StringX=StringX)


def create_new_worker(work):
    global ErrorLogs
    global current_workers
    global threads_amount

    # Create worker:
    current_worker_info = {
        "Current_Work": work,
        "current_message": "Birthed",
        "WorkerID": str(uuid.uuid4()),
    }

    # Give worker a job:
    if work == "check_links":
        # current_workers[WorkerID]["current_message"] = f"Got job checking strings!"
        current_worker_info["current_message"] = "Got job checking strings!"
        # Create worker thread:
        t = threading.Thread(target=check_links_start, args=(current_worker_info,))

    elif work == "create_strings":
        # current_workers[WorkerID]["current_message"] = f"Got job creating links."
        current_worker_info["current_message"] = "Got job creating links."
        # Create worker thread:
        t = threading.Thread(target=create_strings, args=(current_worker_info,))

    elif work == "update_terminal":
        # current_workers[WorkerID]["current_message"] = f"Got job updating Terminal."
        current_worker_info["current_message"] = "Got job updating Terminal."
        # Create worker thread:
        t = threading.Thread(target=update_terminal)

    elif work == "fetch_files_number_and_size":
        # current_workers[WorkerID]["current_message"] = f"Got job updating Terminal."
        current_worker_info["current_message"] = "Got job updating Terminal."
        # Create worker thread:
        t = threading.Thread(target=fetch_files_number_and_size)
    else:
        print("Worker got no job.")
        raise Exception("Worker got no job!")

    # Add worker to list:
    current_workers[current_worker_info["WorkerID"]] = current_worker_info

    t.daemon = False
    current_worker_info["current_message"] = "Got all my settings!"
    t.start()


def write_last_info(mode=""):
    global total_iterations
    global latest_string_from_File

    filePath = f"{download_folder_location}/{DB_files_path_prefix}/00LastStringX.txt"
    try:
        if mode == "Restore":
            import ast

            try:
                with open(filePath, "r+") as file:
                    # latest_string_from_File, total_iterations = tuple(file.read())
                    tuple_value = ast.literal_eval(file.read())
                    latest_string_from_File, total_iterations = tuple_value
                    return
            except SyntaxError:
                return

    except FileNotFoundError:
        return
    with open(filePath, "w+") as file:
        tuple = (latest_string, total_iterations)
        file.write(str(tuple))


os.system("clear")

# Load last StringX
write_last_info(mode="Restore")


create_new_worker(work="update_terminal")
create_new_worker(work="create_strings")
create_new_worker(work="fetch_files_number_and_size")
for i in range(max_threads - 3):  # -1 gets reserved for updating filesize etc
    create_new_worker(work="check_links")


# Clean up the checkedURLs.txt for files that are missing in Archive
# compare_files()
