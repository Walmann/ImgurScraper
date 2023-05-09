from genericpath import isdir
import os
import configparser
import sys
# import sqlite3 as sql
from  dep.db_handler import DB_handler

def create_settings_file(): # TODO Update the created settings file
    """
    Generates the Settings.ini file, if it does not already exists.\n
    After generating it wil exit the script, so you can edit the settings file before starting download.
    """ 
    if not os.path.isfile("settings.ini"):
        with open("settings.ini", "w") as file:
            file.write(
                """
[DEFAULT]

;;;; Work queue settings ;;;;
; max_queue_size = 500
; max_combination_gen_size = 500


;;;; Threads settings ;;;;
; Number of threads to use to check and download links.
;max_threads = 10


;;;; String generation ;;;;
; Length of string. Example i.imgur.com/AAAAA.jpg
;string_length = 5
;url_base = "https://i.imgur.com/"

; Number of times to run iterations towards new URLS.
; Set to -1 for infinite iterations
; max_iterations_per_run = -1


;;;; Optimization ;;;
;Check for missmatch between the Database and the actual files inside of the Archive. 
;check_for_DB_missmatch = False


;;;; Output settings ;;;;
; Make workers in the Workerblock smaller. Usefull if you got many threads
;worker_print_mini = True
;worker_print_summary = True
;worker_print_disable = True
;worker_print_hide_check_links_workers = True


;;;; Folder names ;;;;
; Download folder location. 
; DO NOT USE "/" AT THE END!
; To just use Current Dir, enter only a punctationmark.
;download_folder_root_location = . 
;download_folder_name = Archive 
;db_folder_path_suffix = DB


;;;; File names ;;;;
;CheckedURLsFile = 0checkedURLs.txt
;redirect_urls_filename = 0RedirectURLs.txt
;error_filename = 0ErrorStings.txt
;retry_filename = 0RetryStrings.txt

    """
        )
                
        input(
            "Settings.ini is now created. Rerun the script after editing the settings. Press any key to exit."
        )
        sys.exit()


def create_database(settings):
    # os.path.isdir("Y:\000 - Download\Websites\ImgurImages\Archive/")
    if os.path.isfile("file_db.db"):
        DB_handler.create_new_database()

        if not os.path.isdir(settings["download_folder"]):
            print(f"Can't find Download folder. {settings['download_folder']}")
        
        # Update database with current data:
        print("Creating Database")
        files = 0
        dirs = 0
        
        itt = 50
        for root, dirnames, filenames in os.walk(settings["download_folder"], followlinks=True):
            for dir in dirnames:
                dir2 = os.path.join(root,dir)
                for root2, dirnames2, filenames2 in os.walk(dir2):
                    for filename in filenames2:
                        path = os.path.join(root2, filename)
                        file_size = os.stat(path).st_size
                        StringX = filename.split(".")[0]
                        if itt >= 0:
                            print(f"Added file {filename}", end="\r")
                            itt = 50
                        DB_handler.submit_new_stringX(StringX=StringX, file_path=path, file_size=file_size, was_image=True, response_code=200)

        # Print database contents
        data = DB_handler.runQuerry("select * from FILESDB", ())
        for row in data: 
            print(row)

        input("Finished creating database from already downloaded files. Press Enter and restart script.")
        sys.exit()

    return True



def setup_variables():
    """
    Imports settigns from settings.ini\n
    settings.ini will be generated in the root folder if it does not already exists.\n
    Returns a dict with settings.

    Returns:
        dict : Dict containing all settings for the project
        
    """   

    create_settings_file()


    # SETTINGS
    # To change these settings, write them as an entry in settings.ini.
    # Default settings:
    returning_settings = {
        "check_for_DB_missmatch": False,
        "checked_url_filename": "0checkedURLs.txt",
        "db_folder_path_suffix": "DB",
        "download_folder_root_location": ".",
        "download_folder_name": "Archive",
        "error_filename": "0ErrorStings.txt",
        "max_combination_gen_size": 500,
        "max_iterations_per_run": -1,
        "max_queue_size": 500,
        "max_threads_percent": 90,
        "max_threads": 1,
        "retry_filename": "0RetryStrings.txt",
        "redirect_urls_filename": "0RedirectURLs.txt",
        "string_length": 5,
        "db_folder": "",
        "download_folder": "",
        "character_list": "",
        "generated_string_length": 5,
        "url_base": "https://i.imgur.com/",
        "worker_print_mini": False,
        "worker_print_disable":  False,
        "worker_print_summary": False,
        "worker_print_hide_check_links_workers": False

    }
    # Settings currently not used, but still want to have around:


    # Read Config into variable
    config = configparser.ConfigParser()
    config.read("settings.ini")

    # Set folder location variables:
    returning_settings["db_folder_path_suffix"] = config.get("DEFAULT","db_folder_path_suffix",fallback=returning_settings["db_folder_path_suffix"],)
    returning_settings["download_folder_root_location"] = config.get("DEFAULT","download_folder_root_location",fallback=returning_settings["download_folder_root_location"],)
    returning_settings["download_folder_name"] = config.get("DEFAULT","download_folder_name",fallback=returning_settings["download_folder_name"],)
    returning_settings["error_filename"] = f"{config.get('DEFAULT', 'error_filename', fallback=returning_settings['error_filename'])}"
    returning_settings["redirect_urls_filename"] = f"{config.get('DEFAULT', 'redirect_urls_filename', fallback=returning_settings['redirect_urls_filename'])}"  # noqa: E501
    returning_settings["retry_filename"] = f"{config.get('DEFAULT', 'retry_filename', fallback=returning_settings['retry_filename'])}"
    # returning_settings["error_filename"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}/{config.get('DEFAULT', 'error_filename', fallback=returning_settings['error_filename'])}"
    # returning_settings["redirect_urls_filename"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}/{config.get('DEFAULT', 'redirect_urls_filename', fallback=returning_settings['redirect_urls_filename'])}"  # noqa: E501
    # returning_settings["retry_filename"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}/{config.get('DEFAULT', 'retry_filename', fallback=returning_settings['retry_filename'])}"

    # Folder location variables, that use other variables when created.
    returning_settings["checked_url_filename"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}/{config.get('DEFAULT', 'checked_url_filename', fallback=returning_settings['checked_url_filename'])}"  # noqa: E501
    returning_settings["db_folder"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}"
    returning_settings["download_folder"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['download_folder_name']}"


    # Variables about multithreading
    returning_settings["max_threads"] = int(config.get("DEFAULT","max_threads",fallback=returning_settings["max_threads"],))
    # returning_settings["max_threads_percent"] = int(config.get("DEFAULT","max_threads_percent",fallback=returning_settings["max_threads_percent"],))


    # Queue and combinations settings
    returning_settings["max_combination_gen_size"] = int(config.get("DEFAULT","max_combination_gen_size",fallback=returning_settings["max_combination_gen_size"],))
    returning_settings["max_iterations_per_run"] = int(config.get("DEFAULT", "max_iterations_per_run", fallback=returning_settings["max_iterations_per_run"]))
    returning_settings["max_queue_size"] = int(config.get("DEFAULT", "max_queue_size", fallback=returning_settings["max_queue_size"]))

    # Settings about the URL that are geing created
    returning_settings["character_list"] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    returning_settings["generated_string_length"] = int(config.get("DEFAULT", "string_length", fallback=returning_settings["string_length"]))
    # returning_settings["url_base"] = "https://i.imgur.com/"
    returning_settings["url_base"] = config.get("DEFAULT", "url_base", fallback=returning_settings["url_base"])


    # Optimization settings. These are optional, but if you want to make sure that the DB is OK, these should be enables.
    returning_settings["check_for_DB_missmatch"] = int(config.get("DEFAULT","check_for_DB_missmatch",fallback=returning_settings["check_for_DB_missmatch"],))

    # Output settings: 
    returning_settings['worker_print_mini'] = config.get('DEFAULT','worker_print_mini',fallback=returning_settings['worker_print_mini'],)
    returning_settings['worker_print_disable'] = config.get('DEFAULT','worker_print_disable',fallback=returning_settings['worker_print_disable'],)
    returning_settings['worker_print_summary'] = config.get('DEFAULT','worker_print_summary',fallback=returning_settings['worker_print_summary'],)
    returning_settings['worker_print_hide_check_links_workers'] = config.get('DEFAULT','worker_print_hide_check_links_workers',fallback=returning_settings['worker_print_hide_check_links_workers'],)

    
    return returning_settings

# setup_variables()