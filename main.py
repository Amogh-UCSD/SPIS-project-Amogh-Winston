# $ pip install pygame
# Imports
import sys
import pygame
import ctypes

# Increas Dots Per inch so it looks sharper
ctypes.windll.shcore.SetProcessDpiAwareness(True)

# Pygame Configuration
pygame.init()
fps = 800
fpsClock = pygame.time.Clock()
width, height = 1280, 800
screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
font = pygame.font.SysFont('Serif', 15)

# Variables
objects = []
animFrames = []
# Initial color
drawColor = [0, 0, 0]
# Initial brush size
brushSize = 30
brushSizeSteps = 1
# Canvas size
canvasSize = [600, 600]

# Button Class
class Button():
    def __init__(self, x, y, width, height, buttonText='Button', onclickFunction=None, onePress=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclickFunction = onclickFunction
        self.onePress = onePress

        self.fillColors = {
            'normal': '#ffffff',
            'hover': '#666666',
            'pressed': '#333333',
        }

        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.buttonSurf = font.render(buttonText, True, (20, 20, 20))

        self.alreadyPressed = False

        objects.append(self)

    def process(self):

        mousePos = pygame.mouse.get_pos()

        self.buttonSurface.fill(self.fillColors['normal'])
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.fillColors['hover'])

            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self.fillColors['pressed'])

                if self.onePress:
                    self.onclickFunction()

                elif not self.alreadyPressed:
                    self.onclickFunction()
                    self.alreadyPressed = True

            else:
                self.alreadyPressed = False

        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width/2 - self.buttonSurf.get_rect().width/2,
            self.buttonRect.height/2 - self.buttonSurf.get_rect().height/2
        ])
        screen.blit(self.buttonSurface, self.buttonRect)

# Slider class if time permits
#class Slider():
#    def __init__(self, pos: tuple, size: tuple, startVal: float, min: int, max: int, color) -> None:
#        self.size = size
#        self.pos = pos
#
#        self.leftEdge = self.pos[0] - (size[0]//2)
#        self.rightEdge = self.pos[0] + (size[0]//2)
#        self.top = self.pos[1] + (size[1]//2)
#        self.bottom = self.pos[1] - (size[1]//2)
#
#        self.min = min
#        self.max = max
#
#        self.startVal = startVal
#        self.color = color
#
#        self.container = pygame.Rect(self.leftEdge, self.top, self.size[0], self.size[1])
#        self.knob = pygame.Rect(self.leftEdge + self.startVal -5, self.top, 10, self.size[1])
#
#        def moveKnob(self):
#            (placeholder)
#
#        def render(self, app):
#            pygame.draw.rect(app.screen, color, self.container)
#            pygame.draw.rect(app.screen, "white", self.knob)
# Helper functions
# Changing color
def changeColor(color):
    global drawColor
    drawColor = color

# Changing brush size
def changebrushSize(dir):
    global brushSize
    if dir == 'greater':
        brushSize += brushSizeSteps
    else:
        brushSize -= brushSizeSteps

# Save the surface to the Disk
def save():
    pygame.image.save(canvas, "canvas.png")
def addFrame():
    frame = pygame.image.save(canvas, "frame.png")
    animFrames.append(frame)

# Button Variables.
buttonWidth = 80
buttonHeight = 35

# Buttons and their respective functions.
buttons = [
    ['Black', lambda: changeColor([0, 0, 0])],
    ['White', lambda: changeColor([255, 255, 255])],
    ['Red', lambda: changeColor([200, 0, 0])],
    ['Blue', lambda: changeColor([0, 0, 200])],
    ['Green', lambda: changeColor([0, 200, 0])],
    ['Yellow', lambda: changeColor([225, 225, 0])],
    ['Orange', lambda: changeColor([225, 128, 0])],
    ['Cyan', lambda: changeColor([0, 225, 225])],
    ['Violet', lambda: changeColor([225, 0, 225])],
    ['Brush Larger', lambda: changebrushSize('greater')],
    ['Brush Smaller', lambda: changebrushSize('smaller')],
    ['Save', save],
    ['Add Frame', addFrame]
    #['Run Animation', Code to change display to an animated video]
]

# Making the buttons
for index, buttonName in enumerate(buttons):
    Button(index * (buttonWidth + 10) + 10, 10, buttonWidth,
           buttonHeight, buttonName[0], buttonName[1])

# Filling the canvas
canvas = pygame.Surface(canvasSize)
canvas.fill((255, 255, 255))

# Main draw loop.
while True:
    screen.fill((30, 30, 30))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    # Drawing the Buttons
    for object in objects:
        object.process()

     # Draw the Canvas at the center of the screen
    x, y = screen.get_size()
    screen.blit(canvas, [x/2 - canvasSize[0]/2, y/2 - canvasSize[1]/2])

    # Drawing with the mouse
    if pygame.mouse.get_pressed()[0]:
        mx, my = pygame.mouse.get_pos()
        # Calculate Position on the Canvas
        dx = mx - x/2 + canvasSize[0]/2
        dy = my - y/2 + canvasSize[1]/2
        pygame.draw.circle(canvas, drawColor, [dx, dy], brushSize,)

    # Reference Dot
    pygame.draw.circle(screen, drawColor, [100, 100], brushSize,)

    pygame.display.flip()
    print("testing")
    fpsClock.tick(fps)