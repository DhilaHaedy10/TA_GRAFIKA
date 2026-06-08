"""transforms.py — transformasi 2D berbasis matriks homogen 3×3."""
import math


def mat_mul(A, B):
    return [[sum(A[r][k]*B[k][c] for k in range(3)) for c in range(3)] for r in range(3)]

def identity():
    return [[1,0,0],[0,1,0],[0,0,1]]

def apply_matrix(pts, M):
    return [(M[0][0]*x + M[0][1]*y + M[0][2],
             M[1][0]*x + M[1][1]*y + M[1][2]) for (x,y) in pts]

def translate_matrix(tx, ty):
    M = identity(); M[0][2]=tx; M[1][2]=ty; return M

def rotate_matrix(deg, cx=0, cy=0):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    T1=translate_matrix(-cx,-cy)
    R=[[c,-s,0],[s,c,0],[0,0,1]]
    T2=translate_matrix(cx,cy)
    return mat_mul(T2, mat_mul(R,T1))

def scale_matrix(sx, sy, cx=0, cy=0):
    T1=translate_matrix(-cx,-cy)
    S=[[sx,0,0],[0,sy,0],[0,0,1]]
    T2=translate_matrix(cx,cy)
    return mat_mul(T2, mat_mul(S,T1))

def skew_matrix(shx, shy, cx=0, cy=0):
    T1=translate_matrix(-cx,-cy)
    tx, ty = math.tan(math.radians(shx)), math.tan(math.radians(shy))
    SK=[[1,tx,0],[ty,1,0],[0,0,1]]
    T2=translate_matrix(cx,cy)
    return mat_mul(T2, mat_mul(SK,T1))

def reflect_matrix(axis, m=1.0, b=0.0, canvas_w=1000, canvas_h=700):
    cw, ch = canvas_w, canvas_h
    cx, cy = cw/2, ch/2
    if axis == "Sumbu X":
        T1=translate_matrix(0,-cy); R=[[1,0,0],[0,-1,0],[0,0,1]]; T2=translate_matrix(0,cy)
        return mat_mul(T2, mat_mul(R,T1))
    elif axis == "Sumbu Y":
        T1=translate_matrix(-cx,0); R=[[-1,0,0],[0,1,0],[0,0,1]]; T2=translate_matrix(cx,0)
        return mat_mul(T2, mat_mul(R,T1))
    elif axis == "y = x":
        T1=translate_matrix(-cx,-cy); R=[[0,1,0],[1,0,0],[0,0,1]]; T2=translate_matrix(cx,cy)
        return mat_mul(T2, mat_mul(R,T1))
    elif axis == "y = -x":
        T1=translate_matrix(-cx,-cy); R=[[0,-1,0],[-1,0,0],[0,0,1]]; T2=translate_matrix(cx,cy)
        return mat_mul(T2, mat_mul(R,T1))
    else:
        d = m*m+1
        T1=translate_matrix(0,-b)
        R=[[(1-m*m)/d, 2*m/d, 0],[2*m/d,(m*m-1)/d,0],[0,0,1]]
        T2=translate_matrix(0,b)
        return mat_mul(T2, mat_mul(R,T1))
