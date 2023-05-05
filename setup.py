import os
import configparser



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

    ;Check for missmatch between the Database and the actual files inside of the Archive. 
    ;check_for_DB_missmatch = False

    ; Length of string. Example i.imgur.com/AAAAA.jpg
    ;string_length = 5

    ; Percentage of CPU to use
    ;max_threads_percent = 90

    ; Number of times to run iterations towards new URLS.
    ; This is mostly for debugging. 
    ; Set to -1 for infinite iterations
    ;max_iterations_per_run = -1

    ; Max Queue size:
    ; max_queue_size = 500

    ; Max Generation queue size:
    ; max_combination_gen_size = 500

    ; File locations:

    ; Download folder location. 
    ; DO NOT USE "/" AT THE END!
    ; To just use Current Dir, enter only a punctationmark.
    ;download_folder_root_location    = . 

    ; If this is just a word, a dir will be created in Current working directory,
    ; If it is a path it will use the Path.
    ;download_folder_name = Archive 

    ;worker_print_mini = False

    ;db_folder_path_suffix = DB
    ;CheckedURLsFile      = 0checkedURLs.txt
    ;redirect_urls_filename         = 0RedirectURLs.txt
    ;error_filename            = 0ErrorStings.txt
    ;retry_filename     = 0RetryStrings.txt

    """
        )
                
        input(
            "Settings.ini is now created. Rerun the script after editing the settings. Press any key to exit."
        )




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
        "worker_print_mini": False,
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
        "url_base": ","

    }
    # Settings currently not used, but still want to have around:


    # Read Config into variable
    config = configparser.ConfigParser()
    config.read("settings.ini")

    # Set folder location variables:
    returning_settings["db_folder_path_suffix"] = config.get("DEFAULT","db_folder_path_suffix",fallback=returning_settings["db_folder_path_suffix"],)
    returning_settings["download_folder_root_location"] = config.get("DEFAULT","download_folder_root_location",fallback=returning_settings["download_folder_root_location"],)
    returning_settings["download_folder_name"] = config.get("DEFAULT","download_folder_name",fallback=returning_settings["download_folder_name"],)
    returning_settings["error_filename"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}/{config.get('DEFAULT', 'error_filename', fallback=returning_settings['error_filename'])}"
    returning_settings["redirect_urls_filename"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}/{config.get('DEFAULT', 'redirect_urls_filename', fallback=returning_settings['redirect_urls_filename'])}"  # noqa: E501
    returning_settings["retry_filename"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}/{config.get('DEFAULT', 'retry_filename', fallback=returning_settings['retry_filename'])}"

    # Folder location variables, that use other variables when created.
    returning_settings["checked_url_filename"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}/{config.get('DEFAULT', 'checked_url_filename', fallback=returning_settings['checked_url_filename'])}"  # noqa: E501
    returning_settings["db_folder"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['db_folder_path_suffix']}"
    returning_settings["download_folder"] = f"{returning_settings['download_folder_root_location']}/{returning_settings['download_folder_name']}"


    # Variables about multithreading
    returning_settings["max_threads"] = int(os.cpu_count() - 1)
    # returning_settings["max_threads_percent"] = int(config.get("DEFAULT","max_threads_percent",fallback=returning_settings["max_threads_percent"],))


    # Queue and combinations settings
    returning_settings["max_combination_gen_size"] = int(config.get("DEFAULT","max_combination_gen_size",fallback=returning_settings["max_combination_gen_size"],))
    returning_settings["max_iterations_per_run"] = int(config.get("DEFAULT", "max_iterations_per_run", fallback=returning_settings["max_iterations_per_run"]))
    returning_settings["max_queue_size"] = int(config.get("DEFAULT", "max_queue_size", fallback=returning_settings["max_queue_size"]))

    # Settings about the URL that are geing created
    returning_settings["character_list"] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    returning_settings["generated_string_length"] = int(config.get("DEFAULT", "string_length", fallback=returning_settings["string_length"]))
    returning_settings["url_base"] = "https://i.imgur.com/"


    # Optimization settings. These are optional, but if you want to make sure that the DB is OK, these should be enables.
    returning_settings["check_for_DB_missmatch"] = int(config.get("DEFAULT","check_for_DB_missmatch",fallback=returning_settings["check_for_DB_missmatch"],))

    # Output settings: 
    returning_settings['worker_print_mini'] = config.get('DEFAULT','worker_print_mini',fallback=returning_settings['worker_print_mini'],)


    return returning_settings
