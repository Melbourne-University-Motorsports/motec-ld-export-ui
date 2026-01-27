# MoTeC Export UI

A Python-based GUI application for converting MoTeC `.ld` data files to CSV format. 

## Features

- **Looks Nice**: Thumbs up for that.
- **Bulk Export**: Drag-and-drop support for processing multiple files. It's slow tho :)
- **Smart Naming**: An improvement to the number mess M1 tune cranks out.
- **Auto-Splitting**: Automatically detects gaps in data (e.g. engine off or pitting) and splits a single `.ld` file into multiple "Run" CSVs. (WIP)
- **Detailed Preview**: 
    - **Runs**: Tree view visualization of identified splits and durations.
    - **Filenames**: List view showing exact output filenames before export.

## Installation

1. **Clone the Repository** (with submodules):
   ```bash
   git clone --recursive https://github.com/Melbourne-University-Motorsports/motec-export-ui.git
   cd motec-export-ui
   ```
   *If you already cloned without recursive, run:* `git submodule update --init --recursive`

2. **Set up Virtual Environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Application**:
   ```bash
   python src/main.py
   ```

2. **Workflow**:
   - **Drop Files**: Drag `.ld` files into the left pane.
   - **Review**: Check the right pane to see identified runs and durations.
   - **Export**: Click **Export CSV**. 
     - *Default Output*: Files are saved to an `./out` folder in the project directory created automatically.
     - You can change the destination by clicking "Change".

## Project Structure

- `src/ui`: PyQt6 user interface components.
  - `main_window.py`: Application entry point and layout.
  - `header.py`: Custom branded header widget.
  - `worker.py`: Background threads for scanning and exporting.
- `src/backend`: Data processing logic (wraps `motec-to-csv`).
- `motec-to-csv`: Submodule containing the core parsing logic.

## License

MIT License
