# Command to start a behavioral session taking user input from 
# board, box, and mouse.

import os
import shutil
import json
import subprocess
from django.core.management.base import BaseCommand
import ArduFSM.Runner

def get_user_input_from_keyboard():
    """Get user to type the board, box, and mouse"""
    board = raw_input("Enter board: ")
    board = board.upper().strip()
    box = raw_input("Enter box: ")
    box = box.upper().strip()
    mouse = raw_input("Enter mouse: ")
    mouse = mouse.upper().strip()
    
    return {
        'board': board,
        'box': box,
        'mouse': mouse,
    }

def run():
    # Create a place to keep sandboxes
    sandbox_root = os.path.expanduser('~/sandbox_root')

    # Where to look for protocols by name
    protocol_root = os.path.expanduser('~/dev/ArduFSM')
        
    # Get session parameters from user (board number, etc)
    user_input = get_user_input_from_keyboard()

    # Look up the specific parameters
    specific_parameters = ArduFSM.Runner.ParamLookups.base.\
        get_specific_parameters_from_user_input(user_input)

    # Use the sandbox parameters to create the sandbox
    sandbox_paths = ArduFSM.Runner.Sandbox.create_sandbox(
        user_input, sandbox_root=sandbox_root)

    # Copy protocol to sandbox
    ArduFSM.Runner.Sandbox.copy_protocol_to_sandbox(
        sandbox_paths,
        build_parameters=specific_parameters['build'], 
        protocol_root=protocol_root)

    # Write the C parameters
    ArduFSM.Runner.Sandbox.write_c_config_file(
        sketch_path=sandbox_paths['sketch'],
        c_parameters=specific_parameters['C'])

    # Write the Python parameters
    ArduFSM.Runner.Sandbox.write_python_parameters(
        sandbox_paths, 
        python_parameters=specific_parameters['Python'], 
        script_name=specific_parameters['build']['script_name'])

    # Compile and upload
    ArduFSM.Runner.Sandbox.compile_and_upload(sandbox_paths, specific_parameters)

    # Call Python process
    # Extract some subprocess kwargs from the build dict
    subprocess_kwargs = {}
    for kwarg in ['nrows', 'ncols', 'xpos', 'ypos', 'zoom']:
        try:
            subprocess_kwargs[kwarg] = specific_parameters['build'][
                'subprocess_window_' + kwarg]
        except KeyError:
            continue
    ArduFSM.Runner.Sandbox.call_python_script(
        script_path=sandbox_paths['script'], 
        script_name=specific_parameters['build']['script_name'],
        **subprocess_kwargs
        )


class Command(BaseCommand):
    def handle(self, **options):
        run()

if __name__ == "__main__":
    run()