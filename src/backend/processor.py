import os
import sys
import pandas as pd
from typing import List, Tuple, Optional
import shutil

# Ensure motec-to-csv submodule is in path when running from source
if not getattr(sys, 'frozen', False):
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../motec-to-csv/src'))

try:
    from motec_converter import parse_race_data, to_pandas, RaceData
except ImportError:
    # If we are frozen, this means the build failed to include the module
    if getattr(sys, 'frozen', False):
         raise ImportError("Could not import 'motec_converter' in frozen application. Build configuration issue.")
    else:
         raise ImportError("Could not import 'motec_converter'. Ensure submodule is initialized.")

class MotecProcessor:
    def __init__(self):
        pass

    def load_data(self, filepath: str) -> RaceData:
        """Loads the .ld file using the library."""
        try:
            return parse_race_data(filepath)
        except Exception as e:
            raise ValueError(f"Failed to parse file: {e}")

    def to_dataframes(self, race_data: RaceData) -> List[pd.DataFrame]:
        """Converts RaceData to a list of DataFrames (auto-split by library)."""
        return to_pandas(race_data)

    def scan_file(self, filepath: str) -> dict:
        """
        Parses the file and returns metadata about splits for preview.
        Returns: { 'filename': str, 'comment': str, 'runs': [{'duration': float, 'samples': int}, ...] }
        """
        race_data = self.load_data(filepath)
        dfs = self.to_dataframes(race_data)
        
        runs = []
        for df in dfs:
            if not df.empty:
                duration = df.index[-1] - df.index[0]
                runs.append({
                    'duration': duration,
                    'start': df.index[0],
                    'end': df.index[-1],
                    'samples': len(df)
                })
                
        return {
            'filepath': filepath,
            'metadata': {
                'comment': race_data.comment,
                'driver': race_data.driver,
                'event': race_data.racetype,
                'location': race_data.track
            },
            'runs': runs
        }

    def process_file(
        self, 
        filepath: str, 
        output_dir: str, 
        enable_splitting: bool = True
    ) -> List[str]:
        """
        Full processing pipeline for a single file.
        Returns list of generated file paths.
        """
        race_data = self.load_data(filepath)
        
        # Metadata for naming
        metadata = {
            'comment': race_data.comment,
            'driver': race_data.driver,
            'event': race_data.racetype,
            'location': race_data.track
        }
        
        dfs = self.to_dataframes(race_data)
        
        created_files = []
        valid_dfs = [df for df in dfs if not df.empty]
        
        for i, df in enumerate(valid_dfs):
            duration = df.index[-1] - df.index[0]
            # Name
            out_path = self.generate_filename(output_dir, metadata, duration)
            
            # Export
            df.to_csv(out_path, float_format="%.3f")
            created_files.append(out_path)
            
        return created_files


    def clean_text(self, text: str) -> str:
        """Sanitizes text: replaces spaces with _, removes special chars."""
        if not text:
            return ""
        import re
        # Replace spaces with underscore
        text = text.replace(" ", "_")
        # Remove chars that are not alphanumeric, underscore, hyphen or period
        text = re.sub(r'[^a-zA-Z0-9_\-\.]', '', text)
        return text

    def get_output_filename(self, metadata: dict, duration: float, collision_count: int = 0) -> str:
        """
        Generates filename based on metadata and duration.
        Format: Run_{Comment}_{Duration}s_{Driver}_{Event}_{Location}[_{Count}].csv
        """
        parts = ["Run"]
        
        # Comment
        comment = self.clean_text(metadata.get('comment', ''))
        if comment: parts.append(comment)
        
        # Duration
        parts.append(f"{int(duration)}s")
        
        # Driver
        driver = self.clean_text(metadata.get('driver', ''))
        if driver: parts.append(driver)
        
        # Event
        event = self.clean_text(metadata.get('event', ''))
        if event: parts.append(event)
        
        # Location
        location = self.clean_text(metadata.get('location', ''))
        if location: parts.append(location)
        
        base_name = "_".join(parts)
        
        if collision_count > 0:
            return f"{base_name}_{collision_count}.csv"
        else:
            return f"{base_name}.csv"

    def generate_filename(self, output_dir: str, metadata: dict, duration: float) -> str:
        """
        Generates a safe, unique filename checking against disk for collisions.
        Uses the collision_count param in get_output_filename.
        """
        candidate = self.get_output_filename(metadata, duration, 0)
        full_path = os.path.join(output_dir, candidate)
        
        # Handle collision
        counter = 1
        name_root, ext = os.path.splitext(candidate)
        while os.path.exists(full_path):
            candidate = self.get_output_filename(metadata, duration, counter)
            full_path = os.path.join(output_dir, candidate)
            counter += 1
            
        return full_path
