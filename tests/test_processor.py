import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import os
import shutil
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from backend.processor import MotecProcessor

class TestMotecProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = MotecProcessor()
        self.test_dir = "test_output"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_generate_filename(self):
        metadata = {'comment': 'My Run', 'driver': 'Driver A', 'event': 'Q1', 'location': 'Track'}
        duration = 100.5
        
        # Case 1: No collision
        # Expected: Run_My_Run_100s_Driver_A_Q1_Track.csv
        name = self.processor.generate_filename(self.test_dir, metadata, duration)
        expected = os.path.join(self.test_dir, "Run_My_Run_100s_Driver_A_Q1_Track.csv")
        self.assertEqual(name, expected)
        
        # Case 2: Collision
        with open(name, 'w') as f: f.write("test")
        
        name2 = self.processor.generate_filename(self.test_dir, metadata, duration)
        expected2 = os.path.join(self.test_dir, "Run_My_Run_100s_Driver_A_Q1_Track_1.csv")
        self.assertEqual(name2, expected2)

    @patch('backend.processor.parse_race_data')
    @patch('backend.processor.to_pandas')
    def test_scan_file(self, mock_to_pandas, mock_parse):
        # Mock Data
        mock_race_data = MagicMock()
        mock_race_data.comment = "TestLap"
        mock_race_data.driver = "FastDriver"
        mock_race_data.racetype = "Practice"
        mock_race_data.track = "Monza"
        mock_parse.return_value = mock_race_data
        
        # Mock DF list (2 runs)
        df1 = pd.DataFrame({'Time': [0,1,2,3], 'Val': [1,1,1,1]}).set_index('Time')
        df2 = pd.DataFrame({'Time': [10,11,12], 'Val': [2,2,2]}).set_index('Time')
        mock_to_pandas.return_value = [df1, df2]
        
        # Verify Scan
        result = self.processor.scan_file("dummy.ld")
        self.assertEqual(result['filepath'], "dummy.ld")
        # Check metadata
        self.assertEqual(result['metadata']['comment'], "TestLap")
        self.assertEqual(result['metadata']['driver'], "FastDriver")
        self.assertEqual(len(result['runs']), 2)

    @patch('backend.processor.parse_race_data')
    @patch('backend.processor.to_pandas')
    def test_process_flow(self, mock_to_pandas, mock_parse):
        # Mock Data
        mock_race_data = MagicMock()
        mock_race_data.comment = "TestLap"
        mock_race_data.driver = "Driver"
        mock_race_data.racetype = "Race"
        mock_race_data.track = "Track"
        mock_parse.return_value = mock_race_data
        
        # Mock DF list (2 runs)
        df1 = pd.DataFrame({'Time': [0,1,2,3], 'Val': [1,1,1,1]}).set_index('Time')
        df2 = pd.DataFrame({'Time': [10,11,12], 'Val': [2,2,2]}).set_index('Time')
        mock_to_pandas.return_value = [df1, df2]
        
        # Run
        out_files = self.processor.process_file("dummy.ld", self.test_dir)
        
        # Check calls
        self.assertEqual(len(out_files), 2)
        # Check files exist
        self.assertTrue(os.path.exists(out_files[0]))
        self.assertTrue(os.path.exists(out_files[1]))

if __name__ == '__main__':
    unittest.main()
