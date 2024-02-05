import tkinter as tk
from tkinter import messagebox, filedialog
import platform
import subprocess
import distro
import logging
from logging.handlers import RotatingFileHandler
import pkgutil
from bs4 import BeautifulSoup
import urllib.request

class UpdateCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Update Checker")

        self.root.geometry('800x400')
        self.root.configure(bg='#333333')

        self.font_style = ("Arial", 14)
        self.button_color = "#4609d4"
        self.text_color = "#FFFFFF"
        self.button_text_color = "#FFFFFF"
        self.label_bg_color = "#333333"

        self.setup_logging()

        self.hardware_info_label = tk.Label(root, text="", bg=self.label_bg_color, fg=self.text_color, font=self.font_style)
        self.hardware_info_label.pack(pady=20)
        
        # Call get_hardware_info here to display system information when the app starts
        self.get_hardware_info()

        self.check_updates_button = tk.Button(root, text="Check for Updates", command=self.check_updates, bg=self.button_color, fg=self.button_text_color, font=self.font_style)
        self.check_updates_button.pack(pady=10)

        self.check_software_updates_button = tk.Button(root, text="Check Software Updates", command=self.check_software_updates, bg=self.button_color, fg=self.button_text_color, font=self.font_style)
        self.check_software_updates_button.pack(pady=10)

        self.choose_log_location_button = tk.Button(root, text="Choose Log Location", command=self.choose_log_location, bg=self.button_color, fg=self.button_text_color, font=self.font_style)
        self.choose_log_location_button.pack(pady=10)

    def create_custom_dialog(self, title, message):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg='#333333')
        dialog.geometry("600x400")

        message_label = tk.Label(dialog, text=message, wraplength=350, bg=self.label_bg_color, fg=self.text_color, font=self.font_style)
        message_label.pack(padx=10, pady=10)

        close_button = tk.Button(dialog, text="Close", command=dialog.destroy, bg=self.button_color, fg=self.button_text_color, font=self.font_style)
        close_button.pack(pady=10)

    def setup_logging(self):
        # Create a logger
        self.logger = logging.getLogger("UpdateCheckerApp")
        self.logger.setLevel(logging.DEBUG)
        # Create a formatter and add it to the handler
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        # Create a rotating file handler for update history
        self.history_handler = RotatingFileHandler("update_history.log", maxBytes=1024*1024, backupCount=5)
        self.history_handler.setLevel(logging.INFO)
        self.history_handler.setFormatter(formatter)
        self.logger.addHandler(self.history_handler)
        # Create a rotating file handler for errors
        self.error_handler = RotatingFileHandler("error_log.log", maxBytes=1024*1024, backupCount=5)
        self.error_handler.setLevel(logging.ERROR)
        self.error_handler.setFormatter(formatter)
        self.logger.addHandler(self.error_handler)

    def get_hardware_info(self):
        system_info = platform.uname()
        info_text = f"System: {system_info.system}\nNode Name: {system_info.node}\n" \
                    f"Release: {system_info.release}\nVersion: {system_info.version}\n" \
                    f"Machine: {system_info.machine}\nProcessor: {system_info.processor}"
        self.hardware_info_label.config(text=info_text)

    def get_user_consent(self):
        return messagebox.askyesno("User Consent", "Do you want to check for updates?")

    def check_updates(self):
        self.get_hardware_info()
        if self.get_user_consent():
            # Check for updates based on the user's operating system
            if platform.system() == 'Windows':
                # Trigger Windows Update
                subprocess.run(["powershell", "Install-Module PSWindowsUpdate -Force -AllowClobber"])
                subprocess.run(["powershell", "Get-WindowsUpdate -Install -AcceptAll"])
                self.logger.info("Windows Update checked")
            elif platform.system() == 'Darwin':
                # Trigger macOS Update
                subprocess.run(["softwareupdate", "-i", "-a"])
                self.logger.info("macOS Update checked")
            elif platform.system() == 'Linux':
                # Use distro.id() to get the distribution ID as a string
                dist_id = distro.id()
                update_command = ""
                if "ubuntu" in dist_id or "debian" in dist_id:
                    update_command = "sudo apt-get update && sudo apt-get upgrade -y"
                elif "fedora" in dist_id or "centos" in dist_id:
                    update_command = "sudo dnf update -y"
                elif "arch" in dist_id:
                    update_command = "sudo pacman -Syu"
                else:
                    self.create_custom_dialog("Linux Update Information", "Your Linux distribution is not supported for automatic updates through this script.")
                    return

                self.create_custom_dialog("Update Information", f"For your system ({dist_id}), use the following command to update:\n{update_command}")
                self.logger.info(f"Linux Update Information provided for {dist_id}")

                # Run the update command in the terminal
                subprocess.run(update_command.split())
            else:
                self.create_custom_dialog("Unsupported System", "Updates are not supported for the current operating system.")

            self.logger.info("Update process completed.")

    def check_software_updates(self):
        try:
            # Get the current operating system
            current_os = platform.system().lower()

            # Check updates based on the operating system
            if current_os == 'linux':
                # Use the appropriate command for your Linux package manager (e.g., 'dpkg -l' for Debian-based systems)
                process = subprocess.Popen(['dpkg', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # ... (rest of the Linux-specific code)

            elif current_os == 'darwin':  # macOS
                # Use the appropriate command for macOS package manager (e.g., 'brew list --versions')
                process = subprocess.Popen(['brew', 'list', '--versions'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # ... (rest of the macOS-specific code)

            elif current_os == 'windows':
                # Use the appropriate command for Windows package manager (e.g., 'choco list --local-only')
                process = subprocess.Popen(['choco', 'list', '--local-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # ... (rest of the Windows-specific code)

            else:
                self.logger.warning(f"Unsupported operating system: {current_os}")
                return

            output, _ = process.communicate()

            # Parse the output to get the installed programs and their versions
            installed_programs = {}
            for line in output.split('\n')[5:]:
                columns = line.split()
                if len(columns) >= 3:
                    program_name = columns[1]
                    program_version = columns[2]
                    installed_programs[program_name] = program_version

            # Check for updates and notify the user
            for program_name, installed_version in installed_programs.items():
                latest_version = self.get_latest_version(program_name)
                if installed_version < latest_version:
                    self.create_custom_dialog("Software Update", f"Update available for {program_name}: {installed_version} -> {latest_version}")
                    self.logger.info(f"Software Update checked for {program_name}")
                else:
                    self.create_custom_dialog("Software Update", f"{program_name} is up to date.")
                    self.logger.info(f"{program_name} is up to date")

        except Exception as e:
            self.logger.error(f"Error checking software updates: {str(e)}")

    def get_latest_version(self, program_name):
        # Implement this function to retrieve the latest version for the given program
        # You may need to use a different method based on the software you're checking
        pass

    def choose_log_location(self):
        log_location = filedialog.askdirectory()
        if log_location:
            # Update log file locations
            self.history_handler.baseFilename = f"{log_location}/update_history.log"
            self.error_handler.baseFilename = f"{log_location}/error_log.log"
            self.create_custom_dialog("Log Location Updated", f"Log files will be saved in: {log_location}")


if __name__ == "__main__":
    root = tk.Tk()
    app = UpdateCheckerApp(root)
    root.mainloop()
