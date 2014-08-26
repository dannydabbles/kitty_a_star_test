#!/bin/python
##########################Import Statements########################################
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from sympy import *
import sys
import random

##########################Global Variables#########################################
G = None
name = "KittyAiProto"
viewW = 1024
viewH = 512
zoom = 2
depth = 5
depnum = pow(2, depth)
depflag = True
depwidth = 0
depheight = 0
ctype = 'p'
cbutton = False
gravC = 10.0
jvelRange = [10.0,0.0,100.0]
maxJump = 4

##########################Data Structures##########################################
class grid:

    class box:

        connect = []
        jumpMap = {}
        jumpCalced = False

        platform = []
        edge = False

        parent = None
        g_score = 0
        h_score = 0
        f_score = 0

        corner = None
        dim = None
        colorc = [0,0,0]

        vis = False
        walkable = False
        apath = False

        def __init__(self, corner, dim, colorc):
            self.corner = corner[:]
            self.dim = dim[:]
            if colorc is not None:
                self.colorc = colorc[:]
            self.connect = []
            for i in range(8):
                self.connect.append(None)
            if len(self.connect) != 8:
                print "Error: initial number of box connections exceeds 8."
            return 
    
    boxes = []  #2D array of all boxes in grid
    start = None  #Start box
    goal = None   #End box

    def __init__(self):
        return

    def colorList(self, L):
        for B in L:
            if B is self.start or B is self.goal:
                continue
            B.apath = True
        return

    def recPath_rec(self, L, curr):
        if curr is None: return L
        L.insert(0, curr)
        return self.recPath_rec(L, curr.parent)

    def recPath(self,curr):
        L = []
        return self.recPath_rec(L, curr)

    def distance(self,A, B):
        temp = sqrt(abs(pow(float(B.corner[0] - A.corner[0]), 2) + pow(float(B.corner[1] - A.corner[1]), 2)))
        return temp

    def heuristic_est_dist(self,A, B):
        temp = sqrt(abs(pow(float(B.corner[0] - A.corner[0]), 2) + pow(float(B.corner[1] - A.corner[1]), 2)))
        return temp

    def resetBoxes(self, depwidth, depheight):
        self.boxes = []
        temp = int(pow(2,depth))
        for i in range(temp):
            self.boxes.append([])
            for j in range(temp): 
                self.boxes[i].append(None)
        for i in range(temp):
            for j in range(temp):
                cornertemp = [i*depwidth, j*depheight]
                dimtemp = [depwidth, depheight]
                self.boxes[i][j] = self.box(cornertemp, dimtemp, None)
        for j in range(len(self.boxes)):
            for i in range(len(self.boxes[j])):
                if i-1 >= 0 and j-1 >= 0:
                    self.boxes[i][j].connect[0] = self.boxes[i-1][j-1]
                if j-1 >= 0:
                    self.boxes[i][j].connect[1] = self.boxes[i][j-1]
                if i+1 < len(self.boxes[j]) and j-1 >= 0:
                    self.boxes[i][j].connect[2] = self.boxes[i+1][j-1]
                if i+1 < len(self.boxes[j]):
                    self.boxes[i][j].connect[3] = self.boxes[i+1][j]   
                if i+1 < len(self.boxes[j]) and j+1 < len(self.boxes):
                    self.boxes[i][j].connect[4] = self.boxes[i+1][j+1]
                if j+1 < len(self.boxes):
                    self.boxes[i][j].connect[5] = self.boxes[i][j+1]
                if i-1 >= 0 and j+1 < len(self.boxes):
                    self.boxes[i][j].connect[6] = self.boxes[i-1][j+1] 
                if i-1 >= 0:
                    self.boxes[i][j].connect[7] = self.boxes[i-1][j]
        return
          
    def drawboxes(self):
        if self.boxes is None:
            return
        for Y in self.boxes:
            for B in Y:
                if B.apath:
                    glBegin(GL_POLYGON)
                    glColor(0,255,0)
                    rect(B.corner[0],B.corner[1], B.dim[0], B.dim[1])
                    glEnd()
                elif B.vis:
                    glBegin(GL_POLYGON)
                    glColor(B.colorc[0],B.colorc[1],B.colorc[2])
                    rect(B.corner[0],B.corner[1], B.dim[0], B.dim[1])
                    glEnd()
        return                    

    def findPath(self, start, goal):
        self.start = start
        self.goal = goal
        for Y in self.boxes:
            for B in Y:
                B.parent = None
                B.apath = False
                B.g_score = viewW * 100
                B.h_score = viewW * 100
                B.f_score = viewW * 100
        cset = []
        oset = []
        start.g_score = 0
        start.h_score = self.heuristic_est_dist(start, goal)
        start.f_score = start.h_score
        oset.append(start)
        while len(oset) != 0:
            X = oset.pop(0)
            if X is goal:
                return self.recPath(goal)
            cset.append(X)
            if len(X.platform) == 0:
                self.calcPlatform(X)
            self.calcJumps(X)
            for Y in X.connect:
                if Y is None: 
                    continue
                if not Y.walkable: 
                    continue
                if Y in cset: 
                    continue
                if Y in X.connect[:8]:
                    tent_g_score = X.g_score + self.distance(X,Y)
                else:
                    tent_g_score = X.g_score + 5 * self.distance(X,Y)

                tent_better = False
                if not Y in oset:
                    oset.append(Y)
                    tent_better = True
                elif tent_g_score < Y.g_score:
                    tent_better = True
                else:
                    tent_better = False
                if tent_better is True:
                    Y.parent = X
                    Y.g_score = tent_g_score
                    Y.f_score = Y.g_score + Y.h_score
        print "No path found!"
        return None

    def calcPlatform(self, X):
        if len(X.platform) != 0:
            return
        platform = []
        curr = X
        platform.append(X)
        while True:
            prev = curr
            curr = curr.connect[3]
            if curr is None:
                break
            if not curr.walkable:
                prev.edge = True
                break
            platform.append(curr)
        curr = X
        while True:
            prev = curr
            curr = curr.connect[7]
            if curr is None:
                break
            if not curr.walkable:
                prev.edge = True
                break
            platform.append(curr)
        X.platform = platform
        return

    def calcJumps(self, X):
        global gravC
        global jvelRange
        global maxJump
        if X.jumpCalced:
            return
        o = Symbol('o')
        v = Symbol('v')
        g = Symbol('g')
        x = Symbol('x')
        y = Symbol('y')
        checklist = []
        for i in range(maxJump):
            if i == 0:
                checklist.extend(X.connect[1:8:1])
#                print len(checklist)
                continue
            tlist = []
            for Y in checklist:
                if Y is None:
                    continue
                for Z in Y.connect[1:8:1]:
                    if Z is None:
                        continue
                    elif Z is X: 
                        continue
                    elif Z in checklist:
                        continue
                    elif Z in tlist:
                        continue
                    else:
                        tlist.append(Z)
            checklist.extend(tlist)
#            print len(tlist)
#        print len(checklist)
        if len(checklist) > 80: 
            print "Jump calculation error!"
            exit(1)
        for Y in checklist:
            if Y is None:
                continue
            if not Y.walkable:
                continue
            if Y in X.platform:
                continue
            if len(Y.platform) == 0:
                self.calcPlatform(Y)
            if not Y.edge:
                continue
#            print "Testing..."
            angles = []
            xVal = float(Y.corner[0] - X.corner[0])
            yVal = float(Y.corner[1] - X.corner[1])
            eqnp = atan(((v**2 + sqrt(v**4 - g*(g*x**2 + 2*y*v**2)))/(g*x)))
            eqnp = eqnp.subs(g, float(gravC))
            eqnp = eqnp.subs(x, xVal)
            eqnp = eqnp.subs(y, yVal)
            eqnm = atan(((v**2 - sqrt(v**4 - g*(g*x**2 + 2*y*v**2)))/(g*x)))
            eqnm = eqnm.subs(g, float(gravC))
            eqnm = eqnm.subs(x, xVal)
            eqnm = eqnm.subs(y, yVal)
            for i in range(int(jvelRange[0])):
                vel = (jvelRange[2]-jvelRange[1])*(1/jvelRange[0])*i + jvelRange[1]
                fcnp = Eq(eqnp.subs(v, vel) , o)
                fcnm = Eq(eqnm.subs(v, vel) , o)
                nump = (solve(fcnp, o )[0]*180/pi).evalf()
                numm = (solve(fcnm , o )[0]*180/pi).evalf()
                if(isinstance(nump, (int, float, core.numbers.Real))): 
                    angles.append(float(nump))
                if(isinstance(numm, (int, float, core.numbers.Real))): 
                    angles.append(float(numm))
            if len(angles) == 0: 
#                print "No angles"
                continue
#            print anglesg
            X.connect.append(Y)
            X.jumpMap[Y] = angles
#            print "..."
        X.jumpCalced = True
        return

##########################Functions################################################
def rect(A,B,W,H):
    global viewH
    global depheight
    A = int(A)
    B = viewH - depheight - int(B)
    W = int(W)
    H = int(H)
    glVertex2d(A,B)
    glVertex2d(A+W,B)
    glVertex2d(A+W,B+H)
    glVertex2d(A,B+H)
    return

def update():
    global depflag
    global depwidth, depheight
    global G
    if depflag:
        G.resetBoxes(depwidth, depheight)
        depflag = False
    if G.start != None and G.goal != None:
        path = G.findPath(G.start, G.goal)
        if path != None and len(path) != 0:
            G.colorList(path) 
    glutPostRedisplay()
    return

def draw():
    global viewH, viewW
    global depth, depwidth, depheight
    global G
    depheight = viewH / pow(2, depth)
    depwidth = viewW / pow(2, depth)
    for i in range(int(pow(2, depth))):
        temp = int(i*depwidth)
        glBegin(GL_LINES)
        glColor(0,255,0)
        glVertex2d(temp,0)
        glVertex2d(temp,viewH)     
        glEnd()
    for j in range(int(pow(2, depth))):
        temp = int(j*depheight)
        glBegin(GL_LINES)
        glColor(0,255,0)
        glVertex2d(0,temp)
        glVertex2d(viewW, temp)     
        glEnd()
    G.drawboxes()

def display():
    glLoadIdentity()
    down = 2
    left = -1
#    gluLookAt(left + viewW, down + viewH,10*zoom,
#              left + viewW, down + viewH,0,
#              0,1,0)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glPushMatrix()
    glPointSize(1)
    draw()
    glPopMatrix()
    glutSwapBuffers()
    glFlush()
    return

def Key(key, x, y):
    global viewW
    global viewH
    global zoom
    global depth, depflag
    global ctype
    global G
    if key == 'q':
        sys.exit(0)
    if key == '[':
        zoom += .1
    if key == ']':
        zoom -= .1
    if key == '+': #'+' increases fineness of grid
        depflag = True
        depth += 1
    if key == '-': #'-' decreases fineness of grid
        if depth > 0:
            depflag = True
            depth -= 1
    if key == "\r" or key == "\n": #'return' clears the colord boxes on the screen
        for Y in G.boxes:
            for B in Y:
                G.start = None
                G.goal = None
                B.vis = False
                B.walkable = False
                B.apath = False
    if key == 'p':
        ctype = 'p'
    if key == 'l':
        ctype = 'l' 
    if key == 'o':
        ctype = 'o'
    if key == 's':
        ctype = 's'
    if key == 'f':
        ctype = 'f'
    return

def Mouse(button, state, mouseX, mouseY):
    global cbutton
    global ctype
    global G
    cbutton = button
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        colorc =  [0,0,0]
        redc =    [255,0,0]
        yellowc = [255,255,0]
        whitec =  [255,255,255]
        bluec =   [0,0,255]
        blackc =  [0,0,0]
        for Y in G.boxes:
            for B in Y:
                if mouseX >= B.corner[0] and mouseX < (B.corner[0] + B.dim[0]) and mouseY >= B.corner[1] and mouseY < (B.corner[1] + B.dim[1]):
                    if ctype == 'p':
                        colorc = whitec[:]
                        if B.connect[1] != None: B.connect[1].walkable = True
                    if ctype == 'l':
                        colorc = yellowc[:]
                        if B != None: B.walkable = True
                    if ctype == 's':
                        colorc = bluec[:]
                        G.start = B
                        G.start.walkable = True
                    if ctype == 'f':
                        colorc = redc[:]
                        G.goal = B
                        G.goal.walkable = True
                    B.vis = True
                    if ctype == 'o':
                        B.colorc = blackc[:]
                        B.vis = False
                        B.walkable = False
                        if B.connect[1] != None: B.connect[1].walkable = False
                    B.colorc = colorc[:]
    return

def Motion(mouseX, mouseY):
    global cbutton
    global ctype
    global G
    if cbutton == GLUT_LEFT_BUTTON:
        colorc =  [0,0,0]
        redc =    [255,0,0]
        yellowc = [255,255,0]
        whitec =  [255,255,255]
        bluec =   [0,0,255]
        blackc =  [0,0,0]
        for Y in G.boxes:
            for B in Y:
                if mouseX >= B.corner[0] and mouseX < B.corner[0] + B.dim[0] and mouseY >= B.corner[1] and mouseY < B.corner[1] + B.dim[1]:
                    colorc = B.colorc
                    if B is G.start or B is G.goal:
                        continue
                    if ctype == 'p':
                        colorc = whitec
                        if B.connect[1] != None: B.connect[1].walkable = True
                    if ctype == 'l':
                        colorc = yellowc
                        if B != None: B.walkable = True
                    B.vis = True
                    if ctype == 'o':
#                        print "Test"
                        B.colorc = blackc
                        B.vis = False
                        B.walkable = False
                        if B.connect[1] != None: B.connect[1].walkable = False
                    B.colorc = colorc[:]
    return

def main():
    global viewW
    global viewH
    global G
    G = grid()
    #G.calcJumps(None)
    random.seed(random.seed())
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE)
    glutInitWindowSize(viewW, viewH)
    glutCreateWindow(name)
    glutIdleFunc(update)
    glutKeyboardFunc(Key)
    glutMouseFunc(Mouse)
    glutMotionFunc(Motion)
    glClearColor(0.,0.,0.,1.)
    glEnable(GL_POINT_SMOOTH)
    glutDisplayFunc(display)
    glMatrixMode(GL_PROJECTION)
#    gluPerspective(40.,1.,1.,1000.)
    gluOrtho2D(0, viewW, 0, viewH)
    glPushMatrix()
    glMatrixMode(GL_MODELVIEW)
    glutMainLoop()
    return

if __name__ == '__main__': main()
