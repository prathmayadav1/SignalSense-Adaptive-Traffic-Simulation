import pygame
import random

# SignalSense: Adaptive Traffic Signal Simulation
pygame.init()

WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SignalSense - Adaptive Traffic Signal Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)
small = pygame.font.SysFont("consolas", 14)

BG = (15, 18, 30)
ROAD = (45, 48, 60)
WHITE = (240, 240, 245)
GREEN = (40, 220, 110)
RED = (240, 65, 75)
YELLOW = (255, 195, 45)
CYAN = (70, 220, 255)
CAR_COLORS = [(60, 170, 255), (255, 100, 170), (255, 170, 60), (90, 230, 170)]

cx, cy = WIDTH // 2, HEIGHT // 2
ROAD_W = 170
directions = ["N", "S", "E", "W"]


class Vehicle:
    def __init__(self, direction):
        self.direction = direction
        self.color = random.choice(CAR_COLORS)
        self.speed = random.randint(2, 4)
        self.passed = False

        if direction == "N":
            self.x, self.y = cx - 35, -30
        elif direction == "S":
            self.x, self.y = cx + 35, HEIGHT + 30
        elif direction == "W":
            self.x, self.y = -30, cy + 35
        else:
            self.x, self.y = WIDTH + 30, cy - 35

    def update(self, green_axis, vehicles):
        dx, dy = {"N": (0, 1), "S": (0, -1), "W": (1, 0), "E": (-1, 0)}[self.direction]
        is_green = ((self.direction in ("N", "S") and green_axis == "NS") or
                    (self.direction in ("E", "W") and green_axis == "EW"))
        stop = {"N": cy - ROAD_W // 2 - 15, "S": cy + ROAD_W // 2 + 15,
                "W": cx - ROAD_W // 2 - 15, "E": cx + ROAD_W // 2 + 15}[self.direction]
        dist = ((stop - self.y) * dy if dy else (stop - self.x) * dx)

        blocked = False
        for v in vehicles:
            if v is self or v.direction != self.direction:
                continue
            ahead = ((v.y - self.y) * dy if dy else (v.x - self.x) * dx)
            if 0 < ahead < 42:
                blocked = True
                break

        if (is_green or dist > 0) and not blocked:
            self.x += dx * self.speed
            self.y += dy * self.speed

        if ((self.direction == "N" and self.y > cy + ROAD_W // 2 + 30) or
            (self.direction == "S" and self.y < cy - ROAD_W // 2 - 30) or
            (self.direction == "W" and self.x > cx + ROAD_W // 2 + 30) or
            (self.direction == "E" and self.x < cx - ROAD_W // 2 - 30)):
            self.passed = True

    def draw(self):
        size = (14, 27) if self.direction in ("N", "S") else (27, 14)
        rect = pygame.Rect(0, 0, *size)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(screen, self.color, rect, border_radius=4)
        pygame.draw.rect(screen, WHITE, rect, 1, border_radius=4)


class Controller:
    def __init__(self):
        self.axis = "NS"
        self.state = "GREEN"
        self.timer = 0.0
        self.green_time = 8.0
        self.yellow_time = 2.0
        self.all_red_time = 1.0

    def update(self, dt, queues):
        self.timer += dt

        if self.state == "GREEN":
            if self.timer >= self.green_time:
                self.state = "YELLOW"
                self.timer = 0.0
        elif self.state == "YELLOW":
            if self.timer >= self.yellow_time:
                self.state = "ALL_RED"
                self.timer = 0.0
        elif self.state == "ALL_RED":
            if self.timer >= self.all_red_time:
                ns = queues["N"] + queues["S"]
                ew = queues["E"] + queues["W"]
                if self.axis == "NS":
                    self.axis = "EW" if ew > ns else "NS"
                else:
                    self.axis = "NS" if ns > ew else "EW"
                self.state = "GREEN"
                self.timer = 0.0

    def active_green_axis(self):
        if self.state == "ALL_RED":
            return None
        return self.axis

    def draw(self):
        # North/South light group
        if self.axis == "NS":
            ns_color = GREEN if self.state == "GREEN" else YELLOW if self.state == "YELLOW" else RED
            ew_color = RED if self.state != "ALL_RED" else RED
        else:
            ns_color = RED
            ew_color = GREEN if self.state == "GREEN" else YELLOW if self.state == "YELLOW" else RED

        if self.state == "ALL_RED":
            ns_color = RED
            ew_color = RED

        self.draw_light(cx - 90, cy - 90, ns_color)
        self.draw_light(cx + 90, cy + 90, ns_color)
        self.draw_light(cx - 90, cy + 90, ew_color)
        self.draw_light(cx + 90, cy - 90, ew_color)

        if self.state == "YELLOW":
            active = self.axis
            if active == "NS":
                self.draw_light(cx - 90, cy - 90, YELLOW)
                self.draw_light(cx + 90, cy + 90, YELLOW)
            else:
                self.draw_light(cx - 90, cy + 90, YELLOW)
                self.draw_light(cx + 90, cy - 90, YELLOW)

    def draw_light(self, x, y, color):
        pygame.draw.circle(screen, color, (int(x), int(y)), 10)
        pygame.draw.circle(screen, WHITE, (int(x), int(y)), 10, 1)


class Simulation:
    def __init__(self):
        self.controller = Controller()
        self.vehicles = []
        self.spawn_timer = 0.0
        self.spawn_interval = 0.75
        self.score = 0

    def queue_counts(self):
        counts = {direction: 0 for direction in directions}
        for vehicle in self.vehicles:
            if not vehicle.passed:
                counts[vehicle.direction] += 1
        return counts

    def spawn_vehicle(self):
        direction = random.choice(directions)
        if any(vehicle.direction == direction and vehicle.x in range(-10, 10) for vehicle in self.vehicles):
            return
        self.vehicles.append(Vehicle(direction))

    def update(self, dt):
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            if len(self.vehicles) < 18:
                self.spawn_vehicle()

        queues = self.queue_counts()
        self.controller.update(dt, queues)
        green_axis = self.controller.active_green_axis()

        for vehicle in list(self.vehicles):
            vehicle.update(green_axis, self.vehicles)
            if vehicle.passed:
                self.vehicles.remove(vehicle)
                self.score += 1

    def draw(self):
        screen.fill(BG)

        road_rect = pygame.Rect(cx - ROAD_W // 2, 0, ROAD_W, HEIGHT)
        pygame.draw.rect(screen, ROAD, road_rect)
        pygame.draw.rect(screen, ROAD, pygame.Rect(0, cy - ROAD_W // 2, WIDTH, ROAD_W))

        pygame.draw.rect(screen, BG, pygame.Rect(cx - 15, 0, 30, HEIGHT))
        pygame.draw.rect(screen, BG, pygame.Rect(0, cy - 15, WIDTH, 30))

        for x in range(0, WIDTH, 40):
            pygame.draw.rect(screen, WHITE, (x, cy - 2, 22, 4))
        for y in range(0, HEIGHT, 40):
            pygame.draw.rect(screen, WHITE, (cx - 2, y, 4, 22))

        for vehicle in self.vehicles:
            vehicle.draw()

        self.controller.draw()

        hud = [
            f"State: {self.controller.state}",
            f"Axis: {self.controller.axis}",
            f"Vehicles: {len(self.vehicles)}",
            f"Cleared: {self.score}",
        ]
        for idx, text in enumerate(hud):
            label = font.render(text, True, WHITE)
            screen.blit(label, (20, 24 + idx * 24))

        pygame.display.flip()


simulation = Simulation()

running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    simulation.update(dt)
    simulation.draw()

pygame.quit()
