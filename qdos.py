import os
import pygame
import time
import subprocess

# Initialize Pygame
pygame.init()

# Define constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FONT = pygame.font.SysFont('Consolas', 14)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
# Boot screen assets
BOOT_LOGO = 'bootlogo.png'
BOOT_SOUND = 'bootsound.mp3'


class File:

    def __init__(self, name, size, date, time):
        self.name = name
        self.size = size
        self.date = date
        self.time = time


class Directory:

    def __init__(self, name):
        self.name = name
        self.files = []  # List of files in this directory
        self.subdirectories = []  # List of subdirectories
        self.selected_index = 0  # Track which item is selected

    def add_file(self, file):
        self.files.append(file)

    def add_subdirectory(self, subdir):
        self.subdirectories.append(subdir)

    def list_files(self):
        """Return a formatted list of files and directories."""
        output = []
        for subdir in self.subdirectories:
            output.append(f"{subdir.name} [Directory]")
        for file in self.files:
            output.append(f"{file.name} | {file.size} | {file.date} | {file.time}")
        return output


class QDOS:

    def __init__(self, screen):
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get directory where script is located

        # Initialize root directory as the script's directory
        self.root = Directory(script_dir)
        self.current_dir = self.root
        self.registers = {
            'AX': 0,
            'BX': 0,
            'CX': 0,
            'DX': 0,
            'SI': 0,
            'DI': 0,
            'BP': 0,
            'SP': 0xFFFF,
            'IP': 0,
            'FLAGS': 0
        }

        # Load files and subdirectories from the script's directory
        self.load_directory_content(self.root, script_dir)

        self.screen = screen
        self.font = FONT

    def load_directory_content(self, dir_obj, path):
        """Load files and subdirectories into the Directory object."""
        try:
            entries = os.listdir(path)  # Get all entries in the directory
            for entry in entries:
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):  # If it's a directory, add it to subdirectories
                    subdir = Directory(entry)
                    dir_obj.add_subdirectory(subdir)
                elif os.path.isfile(full_path):  # If it's a file, add it to files
                    file_info = os.stat(full_path)
                    size = file_info.st_size  # File size
                    mod_time = time.localtime(file_info.st_mtime)  # Last modified time
                    formatted_time = time.strftime("%H:%M:%S", mod_time)
                    formatted_date = time.strftime("%Y-%m-%d", mod_time)
                    file_obj = File(entry, size, formatted_date, formatted_time)
                    dir_obj.add_file(file_obj)
        except PermissionError:
            pass  # Handle permission errors for protected directories
        except Exception as e:
            print(f"Error loading directory content: {e}")

    def draw_text(self, text, x, y, color):
        """Draw text on the screen at the specified position."""
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def print_directory(self):
        """Render the current directory's contents in the Pygame window."""
        self.screen.fill(BLUE)

        # Display header information
        self.draw_text(
            f"Directory Tag View Copy Move Erase Unerase Rename Attribute Other/more Change, Make, Erase, Graft, and Rename Directories",
            10, 10, WHITE)
        self.draw_text("_____________________________________________________________", 10, 30, WHITE)
        self.draw_text(f"PATH >> {self.current_dir.name}", 10, 50, WHITE)
        self.draw_text("_____________________________________________________________", 10, 70, WHITE)
        self.draw_text(f"Count                  Total Size    |  File Name | Size | Date | Time |", 10, 90, WHITE)
        self.draw_text(f"{len(self.current_dir.files)} Files              553.355    |", 10, 110, WHITE)
        self.draw_text(f"{len(self.current_dir.subdirectories)} Directories                           |", 10, 130, WHITE)
        self.draw_text("_____________________________________________________________", 10, 150, WHITE)

        items = self.current_dir.list_files()

        # Display the files and directories
        for i, item in enumerate(items):
            color = WHITE
            if i == self.current_dir.selected_index:
                color = YELLOW
                self.draw_text(item, 10, 180 + i * 20, RED)  # Red background with yellow text for the selected item
            else:
                self.draw_text(item, 10, 180 + i * 20, color)

        # Display navigation options
        self.draw_text("F1- Help  F2- Status  F3- Chg Drive  F4- Prev Dir", 10, SCREEN_HEIGHT - 50, WHITE)
        self.draw_text("F5- Chg Dir  F6- DOS Cmd  F7- Srch Spec  F8- Sort", 10, SCREEN_HEIGHT - 40, WHITE)
        self.draw_text("F9- Edit  F10- Quit", 10, SCREEN_HEIGHT - 30, WHITE)

        self.draw_text("Q-DOS 3 Version 1.0", 10, SCREEN_HEIGHT - 70, WHITE)
        self.draw_text("GAZELLE SYSTEMS (C) 1991", 10, SCREEN_HEIGHT - 60, WHITE)
        self.draw_text("February, 10, 2025 11:49:00 AM", 10, SCREEN_HEIGHT - 50, WHITE)

        pygame.display.update()

    def navigate(self, key):
        """Handle navigation and selection."""
        try:
            if key == pygame.K_UP:
                self.current_dir.selected_index = (self.current_dir.selected_index - 1) % len(self.current_dir.list_files())
            elif key == pygame.K_DOWN:
                self.current_dir.selected_index = (self.current_dir.selected_index + 1) % len(self.current_dir.list_files())
            elif key == pygame.K_RETURN:
                selected_item = self.current_dir.list_files()[self.current_dir.selected_index]
                if "[Directory]" in selected_item:  # If it's a directory, navigate into it
                    selected_subdir_name = selected_item.split(" ")[0]
                    for subdir in self.current_dir.subdirectories:
                        if subdir.name == selected_subdir_name:
                            self.current_dir = subdir
                            self.current_dir.selected_index = 0
                            # Re-load the subdirectory content
                            self.load_directory_content(self.current_dir, os.path.join(self.current_dir.name, selected_subdir_name))
                else:  # Execute the file
                    self.execute_file(selected_item)
        except Exception as e:
            print(f"Error during navigation: {e}")

    def execute_file(self, selected_item):
        """Execute the selected file."""
        try:
            selected_file_name = selected_item.split(" ")[0]
            file_path = os.path.join(self.current_dir.name, selected_file_name)

            # Check if it's a file and try to open it
            if os.path.isfile(file_path):
                subprocess.run([file_path], check=True)
        except Exception as e:
            print(f"Error executing {selected_item}: {e}")

    def handle_function_keys(self, key):
        """Handle F1-F10 function keys."""
        try:
            if key == pygame.K_F1:
                self.display_help()
            elif key == pygame.K_F2:
                self.display_status()
            elif key == pygame.K_F3:
                self.change_drive()
            elif key == pygame.K_F4:
                self.prev_directory()
            elif key == pygame.K_F5:
                self.change_directory()
            elif key == pygame.K_F6:
                self.dos_command()
            elif key == pygame.K_F7:
                self.search_spec()
            elif key == pygame.K_F8:
                self.sort_files()
            elif key == pygame.K_F9:
                self.edit_file()
            elif key == pygame.K_F10:
                pygame.quit()
        except Exception as e:
            print(f"Error handling function keys: {e}")

    def display_help(self):
        """Display help information."""
        self.screen.fill(BLUE)
        self.draw_text("F1 - Help: Displays help information.", 10, 10, WHITE)
        self.draw_text("F2 - Status: Displays system status.", 10, 30, WHITE)
        self.draw_text("F3 - Chg Drive: Change drives.", 10, 50, WHITE)
        self.draw_text("F4 - Prev Dir: Go to the previous directory.", 10, 70, WHITE)
        self.draw_text("Press any key to return to the main menu.", 10, 90, WHITE)
        pygame.display.update()

    def display_status(self):
        """Display status information."""
        self.screen.fill(BLUE)
        self.draw_text("System Status:", 10, 10, WHITE)
        self.draw_text(f"Current Directory: {self.current_dir.name}", 10, 30, WHITE)
        self.draw_text(f"Files in Directory: {len(self.current_dir.files)}", 10, 50, WHITE)
        self.draw_text("Press any key to return.", 10, SCREEN_HEIGHT - 50, WHITE)
        pygame.display.update()


# Boot screen with logo and sound
def boot_screen():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Booting QDOS...")

    # Load the logo
    logo = pygame.image.load(BOOT_LOGO)
    logo = pygame.transform.scale(logo, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # Play the boot sound
    pygame.mixer.music.load(BOOT_SOUND)
    pygame.mixer.music.play()

    # Display the logo
    screen.blit(logo, (0, 0))
    pygame.display.update()

    # Wait for the sound to finish before continuing
    while pygame.mixer.music.get_busy():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

# Main Program
boot_screen()

# Now start the QDOS emulator after the boot screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("QDOS Emulator")
qdos = QDOS(screen)

# Main loop
running = True
while running:
    qdos.print_directory()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN]:
                qdos.navigate(event.key)
            elif event.key == pygame.K_F1 or event.key == pygame.K_F2 or event.key == pygame.K_F3 or event.key == pygame.K_F4:
                qdos.handle_function_keys(event.key)

pygame.quit()
