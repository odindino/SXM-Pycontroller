import numpy as np
import matplotlib.pyplot as plt

coordinate1 = np.array([[0, 5],[5, 5],[0,10],[10,10]])
coordinate2 = np.array([[0,5],[3,5],[0,2],[3, 2]])
coordinate3 = np.array([[6, 2],[8, 2],[6, 4],[8, 4]])

# combine the coordinates
coordinates = np.concatenate((coordinate1, coordinate2, coordinate3))
print("coordinates: ", coordinates)

# Sort the coordinates by the y-axis, then by the x-axis
sorted_indices = np.lexsort((coordinates[:, 0], coordinates[:, 1]))
print("sorted_indices: ", sorted_indices)

# Sort the coordinates
sorted_coordinates = coordinates[sorted_indices]
print("sorted_coordinates: ", sorted_coordinates)

sorted_coordinates = sorted_coordinates.tolist()
# remove the duplicates
unique_coordinates = []
for i in range(len(sorted_coordinates)):
    print(f"sorted_coordinates[{i}]: ", sorted_coordinates[i])
    if sorted_coordinates[i] not in unique_coordinates:
        unique_coordinates.append(sorted_coordinates[i])
unique_coordinates = np.array(unique_coordinates)
print("unique_coordinates: ", unique_coordinates)

# Plot the coordinates
plt.plot(unique_coordinates[:, 0], unique_coordinates[:, 1], 'o')

# Rotate the coordinates
angle_rad = np.radians(-45)
cos_angle = np.cos(angle_rad)
sin_angle = np.sin(angle_rad)
rotate_matrix = np.array([
    [cos_angle, sin_angle], 
    [-sin_angle, cos_angle]
    ])
rotated_coordinates =  unique_coordinates @ rotate_matrix

# Plot the rotated coordinates
plt.plot(rotated_coordinates[:, 0], rotated_coordinates[:, 1], 'o')

# Set plot properties
plt.axis('equal')
plt.grid(True)
plt.xlabel('X')
plt.ylabel('Y')
plt.legend(['Original', 'Rotated'])


plt.show()