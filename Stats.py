import time
import datetime
import threading
import os



from setup import setup_variables

def filesize_format(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


def create_new_worker(work):


    # Give worker a job:
    if work == "get_file_and_folder_amount":
        t = threading.Thread(target=get_file_and_folder_amount)

    elif work == "get_total_file_size":
        # download_folder = settings["download_folder"]
        t = threading.Thread(target=get_total_file_size, args=(settings["download_folder"], None))
    
    elif work == "update_terminal":
        t = threading.Thread(target=update_terminal)

    else:
        print("Worker got no job.")
        raise Exception("Worker got no job!")

    t.daemon = False
    t.start()


def get_file_and_folder_amount():
    global total_files_archive
    global total_folders_archive
    while True:
        total_files = 0
        total_folders = 0
        for root, dirs, files in os.walk(settings["download_folder"]):
            total_files += len(files)
            total_folders += len(dirs)

        total_files_archive = total_files
        total_folders_archive = total_folders
            

    
def get_total_file_size(path, checked_files=None):
    global total_files_size_archive
    if checked_files is None:
        checked_files = set()
    total_size = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path not in checked_files:
                checked_files.add(file_path)
                total_size += os.path.getsize(file_path)
    for dir in dirs:
        dir_path = os.path.join(root, dir)
        if dir_path not in checked_files:
            checked_files.add(dir_path)
            size = get_total_file_size(dir_path, checked_files)
            total_size += size
    total_files_size_archive = total_size
    get_total_file_size(path)

def info_if_empty(var_to_check = "", string_to_print = ""):
    if var_to_check == 0:
        return "Calculating..."
    else: 
        return string_to_print

def update_terminal():
    global total_files_archive
    global total_files_size_archive
    global ErrorFileLength


    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        # os.system("clr")

        # TODO Make it prettier....
        # terminal_size_width = shutil.get_terminal_size().columns

        # Create the header
        header = "#################\n# Archive Stats #\n#################"



        # Add the totals row and footer
        totals = f"Last refresh: {datetime.datetime.now().strftime('%H:%M:%S')}\n"
        totals +=  f'Total filesize of Archive:  {info_if_empty(var_to_check=total_files_size_archive, string_to_print=filesize_format(total_files_size_archive))}\n'
        totals +=  f'Total files in Archive:     {info_if_empty(total_files_archive, total_files_archive)}\n'
        totals +=  f'Total folders in Archive:   {info_if_empty(total_folders_archive, total_folders_archive)}\n'
        # totals += f'\n'
        # totals += f'Lines in Error registry:    {ErrorFileLength}\n'
        
        

        print(f"{header}\n{totals}")
        

        # Wait until update.
        time.sleep(1)


total_files_archive      = 0
total_folders_archive    = 0
total_files_size_archive = 0
settings = setup_variables()

# get_total_file_size(settings["download_folder"])

create_new_worker(work="update_terminal")
create_new_worker(work="get_file_and_folder_amount")
create_new_worker(work="get_total_file_size")