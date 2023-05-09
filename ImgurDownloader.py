# import sys

import datetime
import imghdr
import itertools
import os
import queue
import threading
import time
import uuid
import requests
# import sqlite3 as sql


from setup import setup_variables
from dep.db_handler import DB_handler

settings = setup_variables()


DB_Handler = DB_handler


# Numbers used by update_terminal
redirectFileLength = 0
CheckedURLFileLength = 0
ErrorFileLength = 0


work_queue = queue.Queue(maxsize=settings["max_queue_size"])
db_queue = queue.Queue(maxsize=settings["max_queue_size"])

# string_set = set()  # create an empty set to store the strings
threads_amount = 0
total_downloaded = 0
total_tested = 0
archive_files_amount = 0
total_iterations = 0
archive_files_size = ""
latest_string = ""
latest_string_from_File = ""
ErrorLogs = []
StartedWork = False

current_workers = {}


def compare_files():
    archive_files = []
    checked_files = []

    # Get list of files in Archive folder
    for root, dirs, files in os.walk(settings["download_folder"]):
        for file in files:
            archive_files.append(file)

    # Get list of files in checkedURLs.txt
    with open(settings["checked_url_filename"], "r") as f:
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
    global StartedWork
    global work_queue
    pppIterations = 0

    # estimated_latest_string = get_last_file_name(settings["download_folder"])

    # estimated_latest_string = DB_Handler.fetch_last_combination()

    while True:
        try:
            # Create the header
            header = "\n\n\n\n\nIMGUR DOWNLOADER\n"
            header += f"Last refresh: {datetime.datetime.now().strftime('%H:%M:%S')}"

            worker_rows = []
            workerBlock = ""

            # if StartedWork:
            if not settings["worker_print_disable"]:

                if settings["worker_print_mini"]:
                    for worker in current_workers.values():
                        worker_rows.append(
                            f"Workers: {f'{len(current_workers)}'}\n")
                        workerBlock = (
                            f"{worker['WorkerID'][:8].upper()}: {worker['Current_Work']}")
                        if 'StringX' in worker:
                            workerBlock += f" -> {worker['StringX']}"
                        workerBlock += "\n"
                        worker_rows.append(workerBlock)

                elif settings["worker_print_summary"]:
                    jobs_summary = {}

                    for worker in current_workers.values():
                        if worker["Current_Work"] in jobs_summary:
                            jobs_summary[worker["Current_Work"]] += 1
                        else:
                            jobs_summary[worker["Current_Work"]] = 1
                    for job in jobs_summary:
                        worker_rows.append(f"{job}: {jobs_summary[job]}\n")
                
                elif settings["worker_print_hide_check_links_workers"]:
                    workers_in_hiding = 0

                    # Print how many workers exists
                    worker_rows.append(f"Total workers: {f'{len(current_workers)}'}\n")
                    for worker in current_workers.values():
                        #Filter out Check_links workers
                        if worker["Current_Work"] == "check_links":
                            workers_in_hiding +=1
                            continue

                        workerStats = ""
                        
                        # Collect and append key values, filter out items in keys_to_ignore
                        keys_to_ignore = ("WorkerID")
                        for item in worker.keys():
                            if item in keys_to_ignore:
                                continue
                            workerStats = workerStats + \
                                f"  {item}: {worker[item]}\n"

                        # Initiate the section for this current worker
                        workerBlock = (
                            f"Worker: {worker['WorkerID'][:8].upper()}\n" +
                            workerStats + "\n"
                        )
                        worker_rows.append(workerBlock)
                    if workers_in_hiding >= 1:
                        worker_rows.append(f"\nHiding {workers_in_hiding} workers.")
                else:
                    for worker in current_workers.values():
                        workerStats = ""
                        worker_rows.append(
                            f"Workers: {f'{len(current_workers)}'}\n")
                        keys_to_ignore = ("WorkerID")

                        for item in worker.keys():
                            if item in keys_to_ignore:
                                continue
                            workerStats = workerStats + \
                                f"  {item}: {worker[item]}\n"

                        workerBlock = (
                            f"Worker: {worker['WorkerID'][:8].upper()}\n" +
                            workerStats + "\n"
                        )
                        worker_rows.append(workerBlock)

            # Add the totals row and footer
            totals = f'Current session downloads:     {total_downloaded}\n'
            totals += f'Current session URLs tested:   {total_tested}\n'
            totals += f'Number of threads:             {len(current_workers)}\n'
            totals += f'Queue length:                  {work_queue.qsize()}\n'
            totals += f'Queue max length:              {work_queue.maxsize}\n'
            totals += f'Download Folder:               {settings["download_folder"]}\n'
            totals += '\n'
            totals += f'Total iterations:              {total_iterations}\n'
            totals += f'Latest Iteration:              {db_updater.fetch_last_combination()}\n'
            totals += f'Iterations since last refresh: {total_iterations-pppIterations}\n'
            # totals += f'Estimated latest string:       {estimated_latest_string}\n'
            totals += f'Lines in Error registry:       {ErrorFileLength}\n'

            # totals += '\n'
            # totals += f'Total number of files in archive folder: {str(archive_files_amount)}\n' # See "Stats.py" for this info
            # totals += f'Total size of archive folder (in bytes): {archive_files_size}\n'

            # Print the full status message
            footer = []
            for error in ErrorLogs:
                footer.append(str(error) + "\n")

            print(f"{header}\n{totals}\n\n\n{''.join(worker_rows)}\n")

            if len(footer) >= 1:
                print("Last 3 Error messages:\n")
            for error in footer[-3:]:
                print(str(error) + "\n")

            # write_last_info()
            pppIterations = total_iterations

            if StartedWork:
                time.sleep(0.5)
            else:
                time.sleep(5)

        except Exception as e:
            # print(e)
            write_error_string(error=e)
            raise Exception(e)
            # exit()


def get_last_file_name(directory):
    # Get a list of all files in the directory
    file_list = os.listdir(directory, )

    # Sort the files by name
    sorted_files = sorted(file_list)

    # Get the last file in the list
    last_folder_name = sorted_files[-1]

    file_list = os.listdir(f"{directory}/{last_folder_name}")

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
    file_path = f'{settings["db_folder"]}/{file_prefix}.txt'
    return file_path


# def is_string_used_IO(StringX):
#     sub_folder = StringX[
#         :-2
#     ]  # Use the first N-2 characters of the string as the prefix for the file name
#     file_path = (
#         # Construct the file path using the prefix
#         f'{settings["download_folder"]}/{sub_folder}'
#     )

#     # temp = os.path.abspath(file_path)
#     # temp2 = os.listdir(os.path.abspath(file_path))
#     try:
#         # for filename in temp2:
#         for filename in os.listdir(os.path.abspath(file_path)):
#             if StringX in filename.split(".")[0]:
#                 return True

#         return False
#     except FileNotFoundError:
#         return False


def is_string_used(string="", firstRun=False):
    # TODO Convert this to use db_updater, if that works better.
    temp = DB_Handler.search_for_string(string)
    return temp


# def write_string(string):

#     with open(fetch_checked_file(string), "a+") as f:
#         f.write(string + "\n")
#     # with open(Checked_Strings_File, 'a') as f:
#     #     f.write(string + '\n')


def write_error_string(error="", message="", StringX=""):
    if not os.path.isfile(settings["error_filename"]):
        with open(settings["error_filename"], "w+") as f:
            f.write("")
    
    with open(settings["error_filename"], "a+") as f:
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")

        f.write(f"{current_time}: {message}. Error: {str(error)}\n")
    # if not StringX == "":
    #     write_string(StringX)


# def write_redirect_url(string):
#     with open(settings["redirect_urls_filename"], "a+") as f:
#         f.write(string + "\n")
#     write_string(string)


# def write_retry_strings(string):
#     with open(settings["retry_filename"], "a+") as f:
#         if string.endsWith("\n"):
#             f.write(string)
#         f.write(string + "\n")
#     write_string(string)


def download_image(string, response, current_worker_info):
    global total_downloaded
    file_name = ""
    update_worker_status("Getting file extension", current_worker_info)
    file_extension = get_file_extension(response)
    file_name = string + file_extension
    update_worker_status(
        f"Got file extension and filename {file_name}", current_worker_info
    )
    dir_name = os.path.join(settings["download_folder"], file_name[:3])

    update_worker_status("Configurating Filepath", current_worker_info)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    file_path = os.path.join(dir_name, file_name)

    update_worker_status("Writing image to file", current_worker_info)
    with open(file_path, "wb") as f:
        f.write(response.content)
        # print(f"Downloaded image {file_name}")
        # write_string(string)
    file_size = get_file_size(file_path)
    status_code = response.status_code
    # DB_handler.submit_new_stringX(StringX=string, response_code=int(status_code), was_image=True, file_path=file_path, file_size=file_size, message="Download_image")

    db_queue.put({"work_type": "submit_new_stringX",
                  "StringX": string,
                  "response_code": int(status_code),
                  "was_image": True,
                  "file_path": file_path,
                  "file_size": file_size,
                  "message": "Download_image"
                  })

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

    current_workers[current_worker_info["WorkerID"]
                    ]["current_message"] = message


def check_links(current_worker_info, retries=0, response=None):
    global total_tested
    # global current_workers
    global ErrorLogs

    global StartedWork
    StartedWork = True

    # Set string X from current_worker_info
    StringX = current_worker_info["StringX"]

    if retries > 3:
        # try:
        update_worker_status(
            "String failed. Writing down string and closing down.",
            current_worker_info,
        )
        db_queue.put({
            "message": "Error after trying 3 times.",
            "response_code": int(response.status_code),
            "StringX": StringX,
        })
        # write_string(StringX)
        return
        # except AttributeError as e:
        #     update_worker_status(
        #         "String failed. Writing down string and closing down.",
        #         current_worker_info,
        #     )
        #     DB_Handler(
        #         message=f"Error after trying 3 times",
        #         error=e,
        #         StringX=StringX,
        #     )
        #     # write_string(StringX)
        #     return

    update_worker_status(
        "Checking if string is already used", current_worker_info)
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
        url = settings["url_base"] + StringX + ".jpg"
        response = requests.get(url, allow_redirects=False, timeout=15)
        response_status = int(response.status_code)
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

    except ConnectionError as e:
        update_worker_status(
            "Got timeout. Adding to Retry list for later.", current_worker_info
        )
        db_queue.put({
            "work_type": "submit_new_stringX",
            "message": f"Got Timeout Error. Error: {e}",
            "StringX": StringX,
            "response_code": int(response_status)
        })
        # write_retry_strings(StringX)
        # DB_handler.submit_new_stringX(StringX=StringX, response_code=response_status, was_image=False)
        pass
    # except Exception as e:
    #     update_worker_status(
    #         "Got Error. Writing down error, and continue.", current_worker_info
    #     )
    #     write_error_string(
    #         message=f"Error with String {StringX}. Could not get response. Error: \n{e}",
    #         StringX=StringX,
    #     )
    #     write_retry_strings(StringX)
    #     pass

    if response_status == 200:
        update_worker_status(
            "Got Status code 200. Downloading image. ", current_worker_info
        )
        download_image(StringX, response, current_worker_info)
        return

    if response_status == 302:
        update_worker_status(
            "Got Status code 302. Skip this URL ", current_worker_info)
        # write_string(StringX)
        db_queue.put({
            "work_type": "submit_new_stringX",
            "StringX": StringX,
            "was_image": False,
            "response_code": int(response_status),
            "message": "Status 302"
        })
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
        update_worker_status(
            f"Got job with string {StringX}", current_worker_info)
        check_links(current_worker_info)


def get_file_length(file):
    line_count = 0
    with open(file, "r") as f:
        for line in f:
            line_count += 1
        return line_count


def get_file_size(path):
    temp = os.stat(path).st_size
    return temp


def fetch_files_number_and_size():
    while True:
        try:
            # Get total number of files and total size of archive folder
            # global archive_files_amount
            # global archive_files_size
            # global redirectFileLength
            # global CheckedURLFileLength
            global ErrorFileLength

            # archive_files_amount = 0

            ErrorFileLength = get_file_length(settings["error_filename"])

        except Exception as e:
            write_error_string(message=f"Error updating stats: {e}")
            raise Exception(e)


def create_strings(current_worker_info):
    global total_iterations
    # global latest_string

    iterations_this_run = settings["max_iterations_per_run"]

    Batches_before_save = 50
    Batches_ran = 0
    try:
        update_worker_status(
            message="I will now start generating combinations.",
            current_worker_info=current_worker_info,
        )

        while True:
            # latest_gen = db_queue.put("fetch_last_combination")
            latest_gen = db_updater.fetch_last_combination()
            if latest_gen is not None:
                break

        Caught_up_to_previous_value = False
        Batches_ran = Batches_before_save
        for combination in itertools.product(settings["character_list"], repeat=settings["generated_string_length"]):
            if Caught_up_to_previous_value is False:
                if not combination == latest_gen:
                    continue

            Caught_up_to_previous_value = True
            StringX = "".join(combination)

            # latest_string = StringX
            # if not Caught_up_to_previous_value:
            #     print(f"\rCreating combination {StringX}     ")
            #     if StringX == latest_string_from_File:
            #         print("Found Starting point!")
            #         Caught_up_to_previous_value = True
            #     if latest_string_from_File == "":
            #         pass
            #     else:
            #         continue

            update_worker_status(
                message=f"I have made string {StringX}",
                current_worker_info=current_worker_info,
            )

            # Batches_ran -= 1
            # if Batches_ran <= 0:
            #     # write_last_info()
            #     Batches_ran = Batches_before_save

            total_iterations += 1
            if is_string_used(StringX):
                update_worker_status(
                    current_worker_info=current_worker_info,
                    message=f"The String {StringX} was used. Checking next combination.",
                )
                continue

            while True:
                if work_queue.full():
                    time.sleep(1)
                else:
                    work_queue.put(StringX)
                    # string_set.add(StringX)
                    iterations_this_run -= 1
                    # check_links(StringX=StringX)
                    break

            if iterations_this_run == 0:
                break

        # Wait for all tasks to complete
        work_queue.join()
    except Exception as e:
        # print(e)
        write_error_string(error=e)
        raise Exception
        # write_error_string(error=e, StringX=StringX)

# class db_updater(StringX = "", file_path = "", file_size = 0, was_image = False, response_code = 0, message="Empty"):


class db_updater():
    # TODO Make other workers add things to the db_queue, so this worker can updater it.
    # This is to mabye skip the I/O Errors
    DB_Handler = DB_handler

    def fetch_last_combination():
        """
        docstring
        """
        latest_gen = DB_Handler.fetch_last_combination()
        return latest_gen

    def loop_worker(current_worker_info):
        update_worker_status(message="Starting to check db_queue for work", current_worker_info=current_worker_info)
        while True:
            work = db_queue.get()

            # StringX="",
            # response_code=int(0),
            # was_image="",
            # file_path="",
            # file_size=int(0),
            # message=""

            # StringX=work["StringX"],
            # response_code=int(work["response_code"]),
            # was_image=work["was_image"],
            # file_path=work["file_path"],
            # file_size=work["file_size"],
            # message=work["message"]

            
            update_worker_status(message=f"Starting to work with {work['work_type']}", current_worker_info=current_worker_info)
            if work["work_type"] == "submit_new_stringX":
                kwargs = {}
                try:
                    for arg in work.keys():
                        if arg in work:
                            kwargs[arg] = work[arg]
                        else:
                            kwargs[arg] = None

                    update_worker_status(message=f"Sending {work['work_type']} to DB_Handler. StringX: {work['StringX']}", current_worker_info=current_worker_info)
                    DB_handler.submit_new_stringX(**kwargs)
                    
                except Exception as e:
                    raise Exception(e)
            # if work["work_type"] == "submit_new_stringX":

            else:
                raise ValueError(f"Invalid Work_type: {work['work_type']}")

def create_database(settings):
    if not os.path.isfile("file_db.db"):
        DB_handler.create_new_database()
        # Update database with current data:
        print("Creating Database")
        for root, dirs, files in os.walk(settings["download_folder"]):
            for file in files:
                path = os.path.join(root, file)
                file_size = os.stat(path).st_size
                StringX = file.split(".")[0]
                
                DB_handler.submit_new_StringX(StringX = StringX, file_path=path, file_size=file_size, was_image=True, response_code=200)
                # filename_tuple = tuple(StringX)
                # file_path = os.path.join(dir, file)
                # sqlquerry = "INSERT INTO FILESDB (StringX, file_path, file_size, was_image, message) values(?, ?, ?, ?, ?)"
                # con.execute(sqlquerry, (StringX, file, file_size, True, ""))


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

    print(f"Creating worker {work}. Info: {current_worker_info}")
    # Give worker a job:
    if work == "check_links":
        
        current_worker_info["current_message"] = "Got job checking strings!"
        # Create worker thread:
        t = threading.Thread(target=check_links_start, args=(current_worker_info,))

    elif work == "db_worker":
        
        current_worker_info["current_message"] = "Got job working with the SQL DB!"
        # Create worker thread:
        t = threading.Thread(target=db_updater.loop_worker, args=(current_worker_info,))

    elif work == "create_strings":
        
        current_worker_info["current_message"] = "Got job creating links."
        # Create worker thread:
        t = threading.Thread(target=create_strings,
                             args=(current_worker_info,))

    elif work == "update_terminal":
        
        current_worker_info["current_message"] = "Got job updating Terminal."
        # Create worker thread:
        t = threading.Thread(target=update_terminal)

    elif work == "fetch_files_number_and_size":
        
        current_worker_info["current_message"] = "Got job updating Terminal."
        # Create worker thread:
        t = threading.Thread(target=fetch_files_number_and_size)
    else:
        print(f"Worker got no job! Work: {work}")
        raise Exception("Worker got no job!")

    # Add worker to list:
    current_workers[current_worker_info["WorkerID"]] = current_worker_info

    t.daemon = False
    # current_worker_info["current_message"] = "Got all my settings!"
    t.start()


# def write_last_info(mode=""):
#     global total_iterations
#     global latest_string_from_File

#     filePath = "/00LastStringX.txt" ## TODO Add this to settings file if it is still needed.
#     if not os.path.isfile(filePath):
#         with open(settings["error_filename"], "w+") as f:
#             f.write("")
    
#     try:
#         if mode == "Restore":
#             import ast

#             try:
#                 with open(filePath, "r+") as file:
#                     # latest_string_from_File, total_iterations = tuple(file.read())
#                     tuple_value = ast.literal_eval(file.read())
#                     latest_string_from_File, total_iterations = tuple_value
#                     return
#             except SyntaxError:
#                 return

#     except FileNotFoundError:
#         return
#     with open(filePath, "w+") as file:
#         tuple = (latest_string, total_iterations)
#         file.write(str(tuple))


# os.system("clear")

# Load last StringX
# print("Loading last info")
# write_last_info(mode="Restore")

# Fetching SQL DB
# SQLDB = sql.connect('file_db.db')

create_database(settings)


print("Creating Workers ")
create_new_worker(work="update_terminal")
create_new_worker(work="db_worker")
create_new_worker(work="create_strings")
# create_new_worker(work="fetch_files_number_and_size") # No need for this after converting to sqlite
for i in range(settings["max_threads"]):
    create_new_worker(work="check_links")
