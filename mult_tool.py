import pygame
import math
pygame.init()
GRAPH_MARKS = pygame.font.SysFont('arial', 12)

FLT_EPSILON = 0.01

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
GRAY = (192, 192, 192)

SCREEN_HEIGHT = 800
SCREEN_WIDTH = 1000
SCREEN = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
SCREEN_MID = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
SCREEN_POS = ((0, 0), (SCREEN_WIDTH, 0), (0, SCREEN_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT))


def vec_add(vec1, vec2):
    if len(vec1) == len(vec2):
        return [a + b for a, b in zip(vec1, vec2)]
    else:
        raise ValueError("Vectors have different lengths.")


def vec_mul(coeff, vec): return [coeff * elem for elem in vec]


class Button:
    def __init__(self, size, pos, text, color, action):
        self.position = pos
        self.action = action
        self.Rect = pygame.Rect(pos, size)

        self.Surface = pygame.Surface(size)
        self.Surface.fill(color)
        text_surface = GRAPH_MARKS.render(text, False, BLACK)
        text_size = text_surface.get_size()
        text_pos = vec_add(vec_mul(0.5, size), vec_mul(-0.5, text_size))
        self.Surface.blit(text_surface, text_pos)

    def point_in(self, point):
        return self.Rect.collidepoint(point)

    def __call__(self):
        if self.point_in(mouse_pos):
            if mouse_let_go:
                return self.action()

    def draw(self):
        SCREEN.blit(self.Surface, self.position)


def frange(start, stop, step):
    curr = start
    while curr < stop:
        yield curr
        curr += step


def coords_to_complex(coords):
    return coords[0] + coords[1] * 1j


def complex_to_coords(complex):
    return [complex.real, complex.imag]


class Grid:
    grid_factor = 5
    sub_grid_factor = 4

    def __init__(self, mul_complex=1, add_complex=0, alpha=255):
        self.mul_complex = mul_complex
        self.add_complex = add_complex
        self._Surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._Surface.set_colorkey(WHITE)
        self._Surface.set_alpha(alpha)

    @property
    def alpha(self):
        return self._Surface.get_alpha()

    @alpha.setter
    def alpha(self, value):
        self._Surface.set_alpha(value)

    @property
    def Surface(self):
        self._Surface.fill(WHITE)
        self._draw()
        return self._Surface

    def to_pixel_pos(self, coordinates):
        coord_num = coords_to_complex(coordinates)
        global_num = coord_num * self.mul_complex + self.add_complex
        global_coords = complex_to_coords(global_num)
        return vec_add(vec_mul(screen_dilation, vec_add(global_coords, vec_mul(-1, coord_shift))), SCREEN_MID)

    def to_coordinate(self, pixel_pos):
        global_coords = vec_add(vec_mul((1 / screen_dilation), vec_add(pixel_pos, vec_mul(-1, SCREEN_MID))), coord_shift)
        global_num = coords_to_complex(global_coords)
        coord_num = (global_num - self.add_complex) / self.mul_complex
        return complex_to_coords(coord_num)

    def _draw_lines(self, lines):
        for line in lines:
            pygame.draw.line(self._Surface, *line)

    @staticmethod
    def _colorfunc(line_coord, color1, color2):
        if line_coord:
            return color1
        else:
            return color2

    def _draw_grid(self, bot_left, top_right):
        left_border, top_border = bot_left
        right_border, bottom_border = top_right

        grid_size = 2 ** (self.grid_factor + int(-math.log2(screen_dilation)))
        sub_grid_size = grid_size / self.sub_grid_factor

        line_coords = []

        left_start = int(left_border / sub_grid_size) * sub_grid_size
        line_coords.extend((GRAY, (line_coord, bottom_border), (line_coord, top_border))
                           for line_coord in frange(left_start, right_border, sub_grid_size))

        top_start = int(top_border / sub_grid_size) * sub_grid_size
        line_coords.extend((GRAY, (left_border, line_coord), (right_border, line_coord))
                           for line_coord in frange(top_start, bottom_border, sub_grid_size))

        left_start = int(left_border / grid_size) * grid_size
        x_coords = list(frange(left_start, right_border, grid_size))
        line_coords.extend((self._colorfunc(line_coord, BLACK, RED), (line_coord, bottom_border), (line_coord, top_border))
                           for line_coord in x_coords)

        top_start = int(top_border / grid_size) * grid_size
        y_coords = list(frange(top_start, bottom_border, grid_size))
        line_coords.extend((self._colorfunc(line_coord, BLACK, RED), (left_border, line_coord), (right_border, line_coord))
                           for line_coord in y_coords)

        lines = [(color, self.to_pixel_pos(coord1), self.to_pixel_pos(coord2)) for color, coord1, coord2 in line_coords]
        self._draw_lines(lines)

        marks = []
        for x_coord in x_coords:
            for y_coord in y_coords:
                coord = int(x_coord), int(y_coord)
                if abs(x_coord - coord[0]) < FLT_EPSILON and abs(y_coord) < FLT_EPSILON:
                    marks.append((str(coord[0]), coord))
                elif abs(y_coord - coord[1]) < FLT_EPSILON and abs(x_coord) < FLT_EPSILON:
                    marks.append((str(-coord[1]) + 'i', coord))

        for mark in marks:
            text, coord = mark
            text_surface = GRAPH_MARKS.render(text, False, BLACK)
            self._Surface.blit(text_surface, self.to_pixel_pos(coord))

    def _draw(self):
        screen_coords = [self.to_coordinate(pos) for pos in SCREEN_POS]
        x_s, y_s = zip(*screen_coords)
        bot_left = (min(x_s), min(y_s))
        top_right = (max(x_s), max(y_s))

        self._draw_grid(bot_left, top_right)

    def draw(self):
        SCREEN.blit(self.Surface, (0, 0))


GLOBAL_GRID = Grid()
screen_dilation = 100
DILATION_RATE = 1.1
coord_shift = [0, 0]
OVERLAY_GRID_ALPHA = 128


class Dot:
    dots = []

    def __init__(self, complex, color=BLUE):
        self.coords = [1, 0]
        self.radius = 5
        self.color = color
        self.complex = complex
        self.dots.append(self)

    @property
    def complex(self):
        return self.coords[0] + self.coords[1] * 1j

    @complex.setter
    def complex(self, val):
        self.coords[0] = val.real
        self.coords[1] = val.imag

    def draw(self):
        pygame.draw.circle(SCREEN, self.color, GLOBAL_GRID.to_pixel_pos(self.coords), self.radius)

    def __contains__(self, coords):
        return (self.coords[0] - coords[0]) ** 2 + (self.coords[1] - coords[1]) ** 2 < (self.radius / screen_dilation) ** 2


result = Dot(0, GREEN)
mouse_clicked = False
mouse_held = False
mouse_right_clicked = False
mouse_let_go = False
mouse_pos = (0, 0)
mouse_scrolled_up = False
mouse_scrolled_down = False
mouse_coords = (0, 0)


def update_mouse_vars():
    global mouse_clicked
    global mouse_held
    global mouse_right_clicked
    global mouse_let_go
    global mouse_pos
    global mouse_coords
    global mouse_scrolled_up
    global mouse_scrolled_down

    mouse_clicked = False
    mouse_right_clicked = False
    mouse_scrolled_up = False
    mouse_scrolled_down = False
    mouse_let_go = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_held = True
                mouse_clicked = True
            elif event.button == 3:
                mouse_right_clicked = True
            elif event.button == 4:
                mouse_scrolled_up = True
            elif event.button == 5:
                mouse_scrolled_down = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_held = False
                mouse_let_go = True
    mouse_pos = pygame.mouse.get_pos()
    mouse_coords = GLOBAL_GRID.to_coordinate(mouse_pos)
    return False


MENU_BUTTON_SIZE = (100, 100)
MENU_BUTTON_POS = (100, 100)
MENU_BUTTON = Button(MENU_BUTTON_SIZE, MENU_BUTTON_POS, "Menu", GRAY, lambda: True)


def main_mul():
    global screen_dilation
    global coord_shift
    global mouse_clicked
    global mouse_held
    global mouse_right_clicked
    global mouse_let_go
    global mouse_scrolled_down
    global mouse_scrolled_up
    global mouse_coords
    global mouse_pos
    global result

    current_factor = Dot(1)
    previous_product = result.complex
    curr_grid = Grid(alpha=OVERLAY_GRID_ALPHA)

    dragging = []

    while True:
        if update_mouse_vars():
            break

        if MENU_BUTTON():
            return False

        if mouse_scrolled_up:
            screen_dilation *= DILATION_RATE
        elif mouse_scrolled_down:
            screen_dilation /= DILATION_RATE
        if mouse_clicked:
            dragging = [dot for dot in Dot.dots if mouse_coords in dot]
            if len(dragging) == 0:
                start_mouse = mouse_pos
                start_coord = coord_shift.copy()
        if mouse_held:
            if len(dragging):
                for dot in dragging:
                    dot.coords = list(mouse_coords)
            else:
                coord_diff = vec_mul((1/screen_dilation), vec_add(start_mouse, vec_mul(-1, mouse_pos)))
                coord_shift = vec_add(start_coord, coord_diff)
        if mouse_right_clicked:
            if mouse_coords in current_factor:
                previous_product *= current_factor.complex
                current_factor.complex = 1
            elif mouse_coords in result:
                previous_product = 1
                current_factor.complex = 1
            else:
                if curr_grid.alpha:
                    curr_grid.alpha = 0
                else:
                    curr_grid.alpha = OVERLAY_GRID_ALPHA
        result.complex = previous_product * current_factor.complex
        curr_grid.mul_complex = current_factor.complex

        SCREEN.fill(WHITE)
        GLOBAL_GRID.draw()
        curr_grid.draw()
        result.draw()
        current_factor.draw()
        MENU_BUTTON.draw()
        pygame.display.update()

    mouse_clicked = False
    mouse_held = False
    mouse_right_clicked = False
    mouse_let_go = False
    mouse_scrolled_up = False
    mouse_scrolled_down = False
    return True


def main_add():
    global screen_dilation
    global coord_shift
    global mouse_clicked
    global mouse_held
    global mouse_right_clicked
    global mouse_let_go
    global mouse_scrolled_down
    global mouse_scrolled_up
    global mouse_coords
    global result

    current_term = Dot(0)
    previous_sum = result.complex
    curr_grid = Grid(alpha=OVERLAY_GRID_ALPHA)

    dragging = []

    while True:
        if update_mouse_vars():
            break

        if MENU_BUTTON():
            return False

        if mouse_scrolled_up:
            screen_dilation *= DILATION_RATE
        elif mouse_scrolled_down:
            screen_dilation /= DILATION_RATE
        if mouse_clicked:
            dragging = [dot for dot in Dot.dots if mouse_coords in dot]
            if len(dragging) == 0:
                start_mouse = mouse_pos
                start_coord = coord_shift.copy()
        if mouse_held:
            if len(dragging):
                for dot in dragging:
                    dot.coords = list(mouse_coords)
            else:
                coord_diff = vec_mul((1/screen_dilation), vec_add(start_mouse, vec_mul(-1, mouse_pos)))
                coord_shift = vec_add(start_coord, coord_diff)
        if mouse_right_clicked:
            if mouse_coords in current_term:
                previous_sum += current_term.complex
                current_term.complex = 0
            elif mouse_coords in result:
                previous_sum = 0
                current_term.complex = 0
            else:
                if curr_grid.alpha:
                    curr_grid.alpha = 0
                else:
                    curr_grid.alpha = OVERLAY_GRID_ALPHA
        result.complex = previous_sum + current_term.complex
        curr_grid.add_complex = current_term.complex

        SCREEN.fill(WHITE)
        GLOBAL_GRID.draw()
        curr_grid.draw()
        result.draw()
        current_term.draw()
        MENU_BUTTON.draw()
        pygame.display.update()

    mouse_clicked = False
    mouse_held = False
    mouse_right_clicked = False
    mouse_let_go = False
    mouse_scrolled_up = False
    mouse_scrolled_down = False
    return True


def main():
    global screen_dilation
    global coord_shift

    BUTTON_SIZE = (100, 100)
    ADD_BUTTON_POS = (100, 100)
    MUL_BUTTON_POS = (100, 300)
    add_button = Button(BUTTON_SIZE, ADD_BUTTON_POS, "Add", GRAY, main_add)
    mul_button = Button(BUTTON_SIZE, MUL_BUTTON_POS, "Multiply", GRAY, main_mul)

    dragging = []
    while True:
        if update_mouse_vars():
            break

        if add_button():
            return True
        if mul_button():
            return True

        if mouse_scrolled_up:
            screen_dilation *= DILATION_RATE
        elif mouse_scrolled_down:
            screen_dilation /= DILATION_RATE
        if mouse_clicked:
            dragging = [dot for dot in Dot.dots if mouse_coords in dot]
            if len(dragging) == 0:
                start_mouse = mouse_pos
                start_coord = coord_shift.copy()
        if mouse_held:
            if len(dragging):
                result.coords = list(mouse_coords)
            else:
                coord_diff = vec_mul((1 / screen_dilation), vec_add(start_mouse, vec_mul(-1, mouse_pos)))
                coord_shift = vec_add(start_coord, coord_diff)
        if mouse_right_clicked and mouse_coords in result:
            result.complex = 0

        SCREEN.fill(WHITE)
        GLOBAL_GRID.draw()
        result.draw()
        add_button.draw()
        mul_button.draw()
        pygame.display.update()


main()
