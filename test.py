import math
import random

def compute_distance(p1, p2):
    # Calcul de la distance euclidienne entre deux points
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def closest_pair(particles):
    def closest_pair_rec(particles_sorted_by_x, particles_sorted_by_y):
        # Si il y a moins de 4 points, utiliser la méthode de force brute
        if len(particles_sorted_by_x) <= 3:
            min_dist = float('inf')
            pair = []
            for i in range(len(particles_sorted_by_x)):
                for j in range(i + 1, len(particles_sorted_by_x)):
                    dist = compute_distance(particles_sorted_by_x[i], particles_sorted_by_x[j])
                    if dist < min_dist:
                        min_dist = dist
                        pair = [particles_sorted_by_x[i], particles_sorted_by_x[j]]
            return min_dist, pair

        # Diviser les points
        mid = len(particles_sorted_by_x) // 2
        left_particles = particles_sorted_by_x[:mid]
        right_particles = particles_sorted_by_x[mid:]

        # Séparation par l'axe X
        mid_x = particles_sorted_by_x[mid][0]

        # Trouver les paires les plus proches à gauche et à droite
        dist_left, pair_left = closest_pair_rec(left_particles, particles_sorted_by_y)
        dist_right, pair_right = closest_pair_rec(right_particles, particles_sorted_by_y)

        # Trouver la plus petite distance parmi les deux
        min_dist = min(dist_left, dist_right)
        closest_pair = pair_left if dist_left < dist_right else pair_right

        # Vérifier les points proches de la ligne de séparation
        strip = [p for p in particles_sorted_by_y if abs(p[0] - mid_x) < min_dist]

        # Comparer les points dans la bande
        for i in range(len(strip)):
            for j in range(i + 1, min(i + 7, len(strip))):
                dist = compute_distance(strip[i], strip[j])
                if dist < min_dist:
                    min_dist = dist
                    closest_pair = [strip[i], strip[j]]

        return min_dist, closest_pair

    # Trier les points par leurs coordonnées X et Y
    particles_sorted_by_x = sorted(particles, key=lambda x: x[0])
    particles_sorted_by_y = sorted(particles, key=lambda x: x[1])

    # Appeler la fonction récursive
    _, result = closest_pair_rec(particles_sorted_by_x, particles_sorted_by_y)

    # Retourner les indices des deux points les plus proches
    return [particles.index(result[0]), particles.index(result[1])]


# Générer 2000 points aléatoires avec des coordonnées entre -10000 et 10000
particles = [[random.randint(-10000, 10000), random.randint(-10000, 10000)] for _ in range(2000)]

# Trouver les deux points les plus proches
closest_points = closest_pair(particles)

# Afficher les indices et les coordonnées des points les plus proches
print("Les deux points les plus proches sont :")
print(f"Point 1 (index {closest_points[0]}): {particles[closest_points[0]]}")
print(f"Point 2 (index {closest_points[1]}): {particles[closest_points[1]]}")
print(f"Distance: {compute_distance(particles[closest_points[0]], particles[closest_points[1]])}")