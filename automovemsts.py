from api import SMUControlAPI
import time

def setup_smu_channels(controller):
    """
    Setup and enable both SMU channels with proper configuration.
    
    Args:
        controller: SMUControlAPI instance
    
    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        # Configure and enable channel 1 (Drain)
        if not controller.set_channel_output(1, True):
            raise Exception("Failed to enable channel 1")
        print("Channel 1 enabled")
            
        # Configure and enable channel 2 (Gate)
        if not controller.set_channel_output(2, True):
            raise Exception("Failed to enable channel 2")
        print("Channel 2 enabled")
        
        # Set initial voltages to 0V for safety
        controller.set_channel_value(1, 'VOLTAGE', 0.0)
        controller.set_channel_value(2, 'VOLTAGE', 0.0)
        
        return True
        
    except Exception as e:
        print(f"Channel setup error: {str(e)}")
        return False

def main():
    # Initialize API controller
    controller = SMUControlAPI()
    
    try:
        # Connect to SMU (Update address according to your setup)
        print("\nConnecting to SMU...")
        smu_address = "TCPIP0::172.30.32.98::inst0::INSTR"  # Update this address
        if not controller.connect_smu(smu_address):
            raise Exception("Failed to connect to SMU")
        print("SMU connected successfully")

        # Setup SMU channels
        print("\nSetting up SMU channels...")
        if not setup_smu_channels(controller):
            raise Exception("Failed to setup SMU channels")
        print("SMU channels setup completed")

        # Auto move MSTS parameters
        movement_params = {
            'script': "UUUUUUUUUUUU",          # Move Right, Up, Left, Down
            'distance': 200,          # 20 nm per move
            'num_points_x': 11,        # 32 points in X direction
            'num_points_y': 21,        # 32 points in Y direction
            'script_name': 'script_001',  # Your STS script name
            'initial_direction': -1,    # Scan from bottom to top
            'wait_time': 10,         # Wait 1 second between moves
            'repeat_count': 1          # Perform measurement once per position
        }

        # Execute auto move MSTS measurement
        print("\nStarting auto move MSTS measurement...")
        success = controller.auto_move_msts_cits(
            movement_script=movement_params['script'],
            distance=movement_params['distance'],
            num_points_x=movement_params['num_points_x'],
            num_points_y=movement_params['num_points_y'],
            script_name=movement_params['script_name'],
            initial_direction=movement_params['initial_direction'],
            wait_time=movement_params['wait_time'],
            repeat_count=movement_params['repeat_count']
        )

        if success:
            print("Measurement completed successfully")
        else:
            print("Measurement failed or was interrupted")

    except Exception as e:
        print(f"\nError during execution: {str(e)}")

    finally:
        # Cleanup
        print("\nPerforming cleanup...")
        controller.cleanup()
        print("Cleanup completed")

if __name__ == "__main__":
    main()