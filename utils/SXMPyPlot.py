import plotly.graph_objects as go
import numpy as np

def generate_auto_move_preview(center_x, center_y, scan_range, scan_angle, movement_script=None):
    """
    Generate a preview of the auto-move scan area.

    Parameters:
    center_x (float): The X coordinate of the scan center (in nm).
    center_y (float): The Y coordinate of the scan center (in nm). 
    scan_range (float): The scan range (in nm).
    scan_angle (float): The scan angle (in degrees).
    movement_script (str, optional): The movement script, e.g., 'RULLDDRR'.

    Returns:
    plotly.graph_objs._figure.Figure: The preview plot.
    """
    # Create the figure
    fig = go.Figure()

    # Set the scan area frame
    x_range = scan_range / 2
    y_range = scan_range / 2
    angle_rad = np.radians(scan_angle)

    # Calculate the rotated scan frame corners
    corners_x = [-x_range, x_range, x_range, -x_range, -x_range] 
    corners_y = [-y_range, -y_range, y_range, y_range, -y_range]

    rotated_x = []
    rotated_y = []
    for x, y in zip(corners_x, corners_y):
        rx = x * np.cos(angle_rad) - y * np.sin(angle_rad) + center_x
        ry = x * np.sin(angle_rad) + y * np.cos(angle_rad) + center_y
        rotated_x.append(rx)
        rotated_y.append(ry)

    # Plot the scan area frame
    fig.add_trace(go.Scatter(
        x=rotated_x,
        y=rotated_y,
        mode='lines',
        line=dict(color='blue', width=2),
        name='Scan Area'
    ))

    # If a movement script is provided, plot the movement path
    if movement_script:
        path_x = [center_x]
        path_y = [center_y]
        x, y = center_x, center_y

        for direction in movement_script:
            if direction == 'R':
                x += scan_range
            elif direction == 'L':
                x -= scan_range
            elif direction == 'U':
                y += scan_range
            elif direction == 'D':
                y -= scan_range
            path_x.append(x)
            path_y.append(y)

        fig.add_trace(go.Scatter(
            x=path_x,
            y=path_y,
            mode='lines+markers',
            line=dict(color='red', width=2),
            marker=dict(size=8),
            name='Movement Path'
        ))

    # Set the figure layout
    fig.update_layout(
        template='plotly_white',
        showlegend=True,
        title=dict(
            text='Auto-Move Preview',
            x=0.5,
            xanchor='center'
        ),
        xaxis_title='X Position (nm)',
        yaxis_title='Y Position (nm)',
        xaxis=dict(showgrid=True, zeroline=True),
        yaxis=dict(showgrid=True, zeroline=True),
        plot_bgcolor='rgba(240,240,240,0.95)',
        width=800,
        height=600,
        margin=dict(l=50, r=50, t=50, b=50)
    )

    return fig