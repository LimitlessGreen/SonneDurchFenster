#!/usr/bin/env python
# coding: utf-8

# # Konzept für: Lichtschatten durch Fenster
# Hier wird ein Konzept geschrieben für ein späteres FHEM Modul, welches den Lichteinfall in Räumen berechnet.
# Es wird hier in unregelmäßigen Abständen erweitert.
# 
# Thread zum Thema: https://forum.fhem.de/index.php/topic,111315.0.html

# In[1]:


import math
from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D
import random
import numpy as np
import matplotlib.pyplot as plt


# In[2]:


# Wichtige Daten
# Manuelle Erstellung der Fensterflächen möglich, in diesem Beispiel wird dies aber durch automatische Erstellung überschrieben
window_surfaces= np.array(
    [[(0,0,1),(0,2,1),(0,2,2),(0,0,2)],
     [(0.2,0,1),(0.2,2,1),(0.2,2,2),(0.2,0,2)]])

sonne_azimut = 0
sonne_hoehe = 20

fenster_hoehe = 1
fenster_breite = 0.5
fenster_dicke = 0.1
fenster_richtung_azimut = 45
fenster_richtung_hoehe = 45
fenster_hoehe_ueber_boden = 0.5


# In[3]:


def sphere_to_cart(azimuth, height, radius=1):
    return np.array([
        radius * math.sin(height) * math.cos(azimuth),
        radius * math.sin(height) * math.sin(azimuth),
        radius * math.cos(height)
    ])


def cart_to_sphere(x, y, z):
    radius = np.linalg.norm(np.array([x, y, z]))
    return np.array([
        math.asin(z / radius),  # height
        math.atan2(y, x)  # azimuth
    ])


class Spherical:
    def __init__(self, azimuth, height, radius = 1):
        self.azimuth = azimuth
        self.height = height
        self.radius = radius

    def get_spherical(self):
        return np.array([self.azimuth, self.height, self.radius])

    def get_cartesian(self):
        return sphere_to_cart(self.azimuth, self.height, self.radius)


class Cartesian:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def get_cartesian(self):
        return np.array([self.x, self.y, self.z])

    def get_spherical(self):
        return cart_to_sphere(self.x, self.y, self.z)


class Coordinates:
    def __init__(self, coordinates):
        self.x = coordinates.get_cartesian()[0]
        self.y = coordinates.get_cartesian()[1]
        self.z = coordinates.get_cartesian()[2]
        self.azimuth = coordinates.get_spherical()[0]
        self.height = coordinates.get_spherical()[1]
        self.radius = coordinates.get_spherical()[2]


class Window:
    def __init__(self, hoehe, breite, dicke, hoehe_ueber_boden, richtung: Coordinates):
        # Window without rotation
        self.window_surfaces = np.array([
            [0, 0, 0],
            [breite, 0, 0],
            [breite, 0, hoehe],
            [0, 0, hoehe]])

        ca = math.cos(richtung.azimuth)
        sa = math.sin(richtung.azimuth)
        rotation_z = np.array([
            [ca, -sa, 0],
            [sa, ca, 0],
            [0, 0, 1]
        ])

        ch = math.cos(-richtung.height)
        sh = math.sin(-richtung.height)
        rotation_x = np.array([
            [1, 0, 0],
            [0, ch, -sh],
            [0, sh, ch]
        ])

        # Rotate
        rotation = rotation_x.dot(rotation_z)
        self.window_surfaces = self.window_surfaces.dot(rotation)

        # Apply thickness
        self.window_surfaces = np.array(
            [self.window_surfaces, self.window_surfaces + dicke * np.array([richtung.x, richtung.y, richtung.z])])

        # Move over the ground
        lift_vec = np.array([0, 0, hoehe_ueber_boden])
        self.window_surfaces = self.window_surfaces + lift_vec

    def get_window_surfaces(self):
        return self.window_surfaces


window = Window(
    fenster_hoehe, fenster_breite, fenster_dicke, fenster_hoehe_ueber_boden, Coordinates(
        Spherical(fenster_richtung_azimut, fenster_richtung_hoehe)))

window_surfaces = window.get_window_surfaces()
print(window_surfaces)


# In[4]:


# Sonnenvektor berechnen (Kugelkoordinaten zu kartesischen Koordinaten)
sun_vector = sphere_to_cart(sonne_azimut, 90 - sonne_hoehe)

### Nur zur Ansicht ###

print(sun_vector)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.quiver(0, 0, 0, sun_vector[0], sun_vector[1], sun_vector[2])
plt.show()


# In[5]:


# Berechne Durchstoßpunkte mit X-Y Ebene (z immer 0)
# Methode hier erklärt: https://www.youtube.com/watch?v=STwIlYF21D0
shadow_points = []

for surface in window_surfaces:
    shadow_points_tmp = []
    for point in surface:
        r = point[2] / -sun_vector[2]
        shadow_points_tmp.append(np.round(point + r * sun_vector, 3))   
    shadow_points.append(shadow_points_tmp)
    
# TODO: clipping (praktisch gesehen wird der Schnitt des 'Schattens' von allen Flächen gebildet)

###
        
shadow_points = np.array(shadow_points)
print("x\ty\tz\t\n", shadow_points)


# In[6]:


### Nur zur grafischen Anzeige, keine weitere Relevanz ###

# Plotte Fenster (in Punkten)
dots = []

for surface in window_surfaces:
    for point in surface:
        dots.append(point)
        
for shadow_point_surface in shadow_points:
    for shadow_point in shadow_point_surface: 
        dots.append(shadow_point)
    
fig = pyplot.figure()
ax = Axes3D(fig)

x_vals = []
y_vals = []
z_vals = []

for dot in dots:
    x_vals.append(dot[0])
    y_vals.append(dot[1])
    z_vals.append(dot[2])
    
ax.scatter(x_vals, y_vals, z_vals)
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')

# Sonnenvektor
ax.quiver(0, 0, 0, sun_vector[0], sun_vector[1], sun_vector[2])

# Fensterkontur
for window_surface in window_surfaces:
    X = []
    Y = []
    Z = []
    for point in window_surface:
        X.append(point[0])
        Y.append(point[1])
        Z.append(point[2])
    # Für geschlossene Kontur
    X.append(X[0])
    Y.append(Y[0])
    Z.append(Z[0])
    
    ax.plot(X,Y,Z)
    
# Schattenkontur
for shadow_point in shadow_points:
    X = []
    Y = []
    Z = []
    for point in shadow_point:
        X.append(point[0])
        Y.append(point[1])
        Z.append(point[2])
    # Für geschlossene Kontur
    X.append(X[0])
    Y.append(Y[0])
    Z.append(Z[0])
    
    ax.plot(X,Y,Z)


pyplot.show()
plt.show()

