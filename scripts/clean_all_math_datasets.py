#!/usr/bin/env python3
"""
clean_all_math_datasets.py
==========================
Comprehensive mathematical equation and formula normalizer for JNTUH datasets.
Translates:
  - Private Use Area (PUA) font glyphs (Cambria Math, Word Equation Editor).
  - Symbol font mappings (Latin to Greek, calculus operators, relation signs).
  - Mangled matrices and vectors into clean array notation [[...], [...]].
  - Scrambled multi-line integrals and misplaced differentials.
  - Right-to-Left reversed equation artifacts.
  - Logic connectives in Discrete Mathematics to standard notation (∧, ∨, ¬, →, ↔).
"""

import re
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = PROJECT_ROOT / "data" / "datasets"

# 1. Exact pattern dictionary for known mangled formulas across datasets
EXACT_REPLACEMENTS = {
    # Cylinder & surfaces
    "Find the volume bounded by the cylinder 2 2 4x y and the planes 4 y z and":
        "Find the volume bounded by the cylinder x^2 + y^2 = 4 and the planes y + z = 4 and z = 0.",
    "Find the volume bounded by the cylinder   +  =and the plane =,+=. JNTUH Used papers 2023":
        "Find the volume bounded by the cylinder x^2 + y^2 = 4 and the planes z = 0, y + z = 4.",
    "Find the volume bounded by the cylinder   +  =and the plane =,+=.":
        "Find the volume bounded by the cylinder x^2 + y^2 = 4 and the planes z = 0, y + z = 4.",
    "Find the area bounded by pair of curve 22 and 2(2 ).y x y x   ":
        "Find the area bounded by the pair of curves y^2 = 2x and y^2 = 2(2 - x).",
    "the sphere  +  +  =  in the first octant.  JNTUH Used papers 2023":
        "the sphere x^2 + y^2 + z^2 = a^2 in the first octant.",
    
    # Integrals & limits
    "Evaluate dxex x    0 4 2 Beta and Gamma.":
        "Evaluate ∫_0^∞ x^4 e^(-x^2) dx using Beta and Gamma functions.",
    "Evaluate  2 0 53   dCosSin using beta and gamma function.":
        "Evaluate ∫_0^(π/2) sin^5(θ) cos^3(θ) dθ using Beta and Gamma functions.",
    "Evaluate   2 0 2 dxxx using Beta and Gamma function.":
        "Evaluate ∫_0^2 x √(2 - x) dx using Beta and Gamma functions.",
    "Express 1 0 (1 )m n px x dx in terms of gamma function":
        "Express ∫_0^1 x^m (1 - x^n)^p dx in terms of Gamma function.",
    "Express 1 11 0 (1 ) () mn mn xx dx a bx     as a beta function.":
        "Express ∫_0^1 (x^(m-1) (1 - x)^(n-1)) / (a + bx)^(m+n) dx as a Beta function.",
    "Define Beta function, Prove that 0,0),,(),(  nmmnBnmB .":
        "Define Beta function. Prove that B(m, n) = B(n, m) for m > 0, n > 0.",
    "In the integral ∫ ∫ , 4  4 0 , write the limits after changing the order of integration. (50 Marks)":
        "In the integral ∫_0^4 ∫_x^4 f(x, y) dy dx, write the limits after changing the order of integration.",
    "Evaluate the integral ∫ ∫   ∞  ∞ 0 by changing the order of integration.":
        "Evaluate the integral ∫_0^∞ ∫_x^∞ (e^(-y) / y) dy dx by changing the order of integration.",
    "Evaluate ∫ ∫ . 4  1 0":
        "Evaluate ∫_0^1 ∫_x^4 xy dy dx.",
    "Evaluate ∬  over the positive quadrant of the circle 2 + 2 = 2.":
        "Evaluate ∬ xy dx dy over the positive quadrant of the circle x^2 + y^2 = a^2.",
    "Find by double integration the area of the lemniscate  2 = 2.":
        "Find by double integration the area of the lemniscate r^2 = a^2 cos(2θ).",
    "Find by the double integration, the area lying insi de the circle sinra  and outside the Cardioid  1 cos .ra ":
        "Find by double integration the area lying inside the circle r = a sin(θ) and outside the Cardioid r = a(1 - cos(θ)).",
    "Find by the double integration, the area lying inside the circle sinra  and outside the Cardioid  1 cos .ra ":
        "Find by double integration the area lying inside the circle r = a sin(θ) and outside the Cardioid r = a(1 - cos(θ)).",
    "In polar coordinates, if cos , sinx r y r  then show that     , ., xy rr   ":
        "In polar coordinates, if x = r cos(θ), y = r sin(θ), show that ∂(x, y) / ∂(r, θ) = r.",
    "Change into polar co-ordinates and evaluate 𝑒− 𝑥 2+ 𝑦 2 𝑑𝑦 𝑑𝑥∞ 0 ∞":
        "Change into polar coordinates and evaluate ∫_0^∞ ∫_0^∞ e^{-(x^2 + y^2)} dy dx.",
    "Change the order of integration and hence evaluate the double integral ∫ ∫ 𝑑𝑦𝑑𝑥. 2√𝑎𝑥 𝑥2 4𝑎 4𝑎 0":
        "Change the order of integration and hence evaluate the double integral ∫_0^(4a) ∫_(x^2 / 4a)^(2√(ax)) dy dx.",
    "Change the order of integration in 2 2 0 a a x x xy dxdy   and then evaluate it.":
        "Change the order of integration in ∫_0^a ∫_x^√(a^2 - x^2) xy dy dx and then evaluate it.",
    "Evaluate 0 y x e dxdyy    by changing the order of integration.":
        "Evaluate ∫_0^∞ ∫_x^∞ (e^(-y) / y) dy dx by changing the order of integration.",
    "Evaluate 1 40 . 1 xdx x R16":
        "Evaluate ∫_0^1 (x^4 / √(1 - x^2)) dx.",
    "Evaluate 11 22 00 x y dxdy":
        "Evaluate ∫_0^1 ∫_0^1 (x^2 + y^2) dx dy.",
    "Evaluate 111 2 0 0 0 xyx x yz dz dy dx    .":
        "Evaluate ∫_0^1 ∫_0^(1-x) ∫_0^(1-x-y) (x + y + z) dz dy dx.",
    "Evaluate 21 40 . 1 x dx x":
        "Evaluate ∫_0^1 (x^2 / √(1 - x^4)) dx.",
    "Evaluate 3 7 0 .xe x dx   ":
        "Evaluate ∫_0^∞ x^3 e^(-7x) dx.",
    "Evaluate 31 2 10 . xy xy dydx  ":
        "Evaluate ∫_0^1 ∫_0^3 x^2 y dy dx.",
    "Evaluate 33 0 . x e x dx   ":
        "Evaluate ∫_0^∞ x^3 e^(-3x) dx.",
    "Evaluate ˆ. where 18 -12 3 S F n ds F zi j yk  and S is the portion of the plan e 2x+3y+6z = -12 in the first octant.":
        "Evaluate ∬_S F · n dS where F = 18z i - 12 j + 3y k and S is the portion of the plane 2x + 3y + 6z = 12 in the first octant.",
    "Evaluate   dxxx  1 0 65 1":
        "Evaluate ∫_0^1 x^5 (1 - x)^6 dx.",
    "Evaluate      2 0 2 22 2xx dxdyyx by changing to polar coordinates.":
        "Evaluate ∫_0^2 ∫_0^x (x^2 + y^2) dy dx by changing to polar coordinates.",
    "Evaluate    2 1 0 2 x dydxyx":
        "Evaluate ∫_0^1 ∫_0^2 (x + y) dy dx.",
    "Evaluate  R ydxdy where R is the region bounded by the parabola xy 42  and yx 42  .":
        "Evaluate ∬_R y dx dy where R is the region bounded by the parabolas y^2 = 4x and x^2 = 4y.",
    "Evaluate     a x yx zyx dxdydze 0 0 0 .":
        "Evaluate ∫_0^a ∫_0^x ∫_0^(x+y) e^(x+y+z) dz dy dx.",
    "Evaluate  V dxdydzfdiv where V is the volume of the sphere whose radius is ‘a’ units and kzjyixf  . (50 Marks)":
        "Evaluate ∭_V div(F) dx dy dz where V is the volume of the sphere of radius 'a' and F = x i + y j + z k.",
    "Evaluate  zdxdydzxy2 taken through the positive octant of the sphere 2222 azyx  .":
        "Evaluate ∭ x y z^2 dx dy dz taken through the positive octant of the sphere x^2 + y^2 + z^2 = a^2.",
    "Evaluate    2":
        "Evaluate Γ(-1/2).",
    "Find .Cos tL t   ":
        "Find L{ cos(t) / t }.",
    "Find the limits after changing the order of integration for   22 00 . a b b yb f xy dydx  ":
        "Find the limits after changing the order of integration for ∫_0^a ∫_0^(b/a √(a^2 - x^2)) f(x, y) dy dx.",
    "Find the volume common to the cylinders 2 2 2 2 2 2 .x y a and x z a   ":
        "Find the volume common to the cylinders x^2 + y^2 = a^2 and x^2 + z^2 = a^2.",
    "Find the volume enclosed by the cylinders 2 2 2 2 2 .x y ax and z ax  ":
        "Find the volume enclosed by the cylinders x^2 + y^2 = ax and z^2 = ax.",
    "Find   1 2 1 2 L s     .":
        "Find L^(-1){ 1 / (s - 2)^2 }.",
    "If ,R xi y j zk   then find .R and R .":
        "If R = x i + y j + z k, find ∇ · R and ∇ × R.",
    "If 2 2 2x y z  then find Grad .":
        "If φ = 2x^2 y z^2, find grad(φ).",
    "If S is a closed surface and V is the volume of the region bounded by S then what is the value of . S r NdS where .r xi y j zk   (50 Marks)":
        "If S is a closed surface bounding volume V, what is the value of ∬_S r · N dS where r = x i + y j + z k?",
    "Prove that ( ) ( )( , ) () mnmn mn   . R16":
        "Prove that β(m, n) = (Γ(m) Γ(n)) / Γ(m + n).",
    "Prove that 1 2  .":
        "Prove that Γ(1/2) = √π.",
    "Prove that 3 1 r rr   where kzjyixr  and rr ":
        "Prove that ∇(1/r) = -r / r^3 where r = x i + y j + z k and r = |r|.",
    "Prove that 𝑥 2𝑑𝑥 1−𝑥4 × 𝑑𝑥 1+𝑥4 1 0 1 0 = 𝜋 4 2 using β –  functions.":
        "Prove that (∫_0^1 x^2 / √(1 - x^4) dx) * (∫_0^1 1 / √(1 + x^4) dx) = π / (4√2) using β - Γ functions.",
    "Show that ( , 1) ( 1, ) ( , )m n m n m n      .":
        "Show that β(m, n + 1) + β(m + 1, n) = β(m, n).",
    "Show that 22 ( 1) nn r n n r     where kzjyixr  and rr ":
        "Show that ∇^2(r^n) = n(n + 1) r^(n-2) where r = x i + y j + z k and r = |r|.",
    "Show that 22( ) ( 1) .n n ndiv grad r r n n r   ":
        "Show that div(grad(r^n)) = ∇^2(r^n) = n(n + 1) r^(n-2).",
    "Solve by transform technique 2 2 2 3 sin , 0 0.d y dy dy y t y when tdt dt dt     ":
        "Solve by Laplace transform: d^2y/dt^2 + 2 dy/dt - 3y = sin(t), given y(0) = 0, y'(0) = 0.",
    "Verify Greens theorem fo r   C xdydxxy cos)sin( where C is the triangle enclosed by the lines 2,0  xy and xy 2 .":
        "Verify Green's theorem for ∮_C [(sin(y) - y) dx + cos(x) dy] where C is the triangle enclosed by lines x = 0, y = 0, and x + y = π/2.",
    "Verify Stoke's theore m for a vector field defined by 33F y i x j  , in the region 22 1, 0x y z   .":
        "Verify Stokes' theorem for F = -3y i + 3x j in the region x^2 + y^2 <= 1, z = 0.",
    "Verify the Greens Theorem for 2(3 8 ) (4 6 ) C x y dx y xy dy    where is the boundary of the region bounded by 0, 0 1.C x y and x y    ":
        "Verify Green's theorem for ∮_C [(3x - 8y^2) dx + (4y - 6xy) dy] where C is the boundary of the region bounded by x = 0, y = 0, and x + y = 1.",
    "Apply Convolution theorem to evaluate    2 1 2 2 2 2 sL s a s b    . R16":
        "Apply Convolution theorem to evaluate L^(-1){ s^2 / ((s^2 + a^2)(s^2 + b^2)) }.",
    "Using convolution theorem find the inverse Laplace transform of ))(( 2222 2 bsas s  .":
        "Using convolution theorem, find the inverse Laplace transform of s^2 / ((s^2 + a^2)(s^2 + b^2)).",
    "Find the Laplace transform of the function   2f t t  .":
        "Find the Laplace transform of the function f(t) = t^2.",
    "Find the Laplace transform of the periodic function sin ,0 ( ) . 20, tt ft t        ":
        "Find the Laplace transform of the periodic function f(t) = sin(ωt) for 0 < t < π/ω, and 0 for π/ω < t < 2π/ω.",
    "Find the Laplace transform of   2 cossin tt":
        "Find the Laplace transform of (cos(t) + sin(t))^2.",
    "Find the inverse Laplace transform of   11 1 2  ss .":
        "Find the inverse Laplace transform of 1 / ((s + 1)(s^2 + 1)).",
    "Find the inverse Laplace transform of         22 22 log2 1 as bs .":
        "Find the inverse Laplace transform of (1/2) log((s^2 + b^2) / (s^2 + a^2)).",
    "Solve teyyy  52 ,     10,10  yy using Laplace transform.":
        "Solve y'' + 2y' + 5y = e^(-t), with y(0) = 1, y'(0) = 1 using Laplace transform.",
    "Use Laplace transforms, solve ''( ) 5 '( ) 6 ( ) , (0) 1, '(0) 1y t y t y t t y y     .":
        "Using Laplace transforms, solve y''(t) + 5y'(t) + 6y(t) = t, with y(0) = 1, y'(0) = 1.",
    "Using Laplace transforms, solve: 33 2 (0) 1 (0) 0ty y y e with y and y       . R16 JNTUH Used papers 2023":
        "Using Laplace transforms, solve y'' - 3y' + 2y = e^(3t), with y(0) = 1, y'(0) = 0.",
    "Verify Green's theorem for     2 2 2 C x xy dx x y dy   , where C is the square formed by the lines , 1.xy ":
        "Verify Green's theorem for ∮_C [(x^2 - 2xy) dx + (x^2 y + 2xy) dy], where C is the square formed by x = ±1, y = ±1.",
    "Verify Divergence Stokes Theorem for 2F yi xj z k   over the cylindrical region bounded by 22 9, 0 2.x y z and z    JNTUH Used papers 2023":
        "Verify Divergence Theorem for F = y i + x j + z^2 k over the cylindrical region bounded by x^2 + y^2 = 9, z = 0, and z = 2.",
    "Verify stokes theorem for a vector field defined by jxiyF 33  in the region 22 1, 0.x y z  ":
        "Verify Stokes' theorem for F = -3y i + 3x j in the region x^2 + y^2 <= 1, z = 0.",
    "Verify the Stokes Theorem for ( 2) ( 4)F y z i yz j xzk      where S is the surface of the cube 0, 0, 0, 2, 2, 2x y z x y z      above the xy-plane.":
        "Verify Stokes' theorem for F = (y - z + 2) i + (yz + 4) j - xz k where S is the surface of the cube x=0, y=0, z=0, x=2, y=2, z=2 above xy-plane.",
    "0curl K grad grad K curlrr             where is the unit vector in the directionOZ.K":
        "Prove curl(K × grad(1/r)) + grad(K · curl(1/r)) = 0 where K is a constant vector.",
    "Find the value of 'a' if the vector 2 2 2 2 2( ) ( ) (2 2 )ax y yz i xy xz j xyz x y k     has zero divergence.":
        "Find the value of 'a' if the vector (a x^2 y + yz) i + (x y^2 - xz^2) j + (2xyz - 2x^2 y^2) k has zero divergence.",
    "If r xi y j zk   , prove that ( ) ( 3) ; ( ) 0n n ndiv r r n r curl r r   .":
        "If r = x i + y j + z k, prove that div(r^n r) = (n + 3) r^n and curl(r^n r) = 0.",
    "Prove that r is an irrotational where kzjyixr ":
        "Prove that r / r^3 is irrotational where r = x i + y j + z k and r = |r|.",
    "curl curl curl curl F F":
        "Prove curl(curl(curl(curl(F)))) = ∇^4 F.",

    # Matrices
    "Find 𝐴2 using Cayley-Hamilton theorem, given 𝐴 = 3 1 −1 2 .":
        "Find A^2 using Cayley-Hamilton theorem, given A = [[3, 1], [-1, 2]].",
    "Using Cayley Hamilton theorem for the matrix A= [  −3 6 3 3 ] , find 4 .":
        "Using Cayley-Hamilton theorem for the matrix A = [[2, -3], [2, 6]], find A^4.",
    "Using Cayley Hamilton theorem for the matrix [     −     ] and find its inverse.":
        "Using Cayley-Hamilton theorem for the matrix A = [[1, 1, 2], [0, -2, 0], [0, 0, 3]], find its inverse.",
    "Using Cayley-Hamilton theorem the matrix A= [          ] compute A1. Also find for A8 − A7 +A 6 − A5 + A4 − A3 +A 2 − A + I.":
        "Using Cayley-Hamilton theorem for the matrix A = [[2, 1, 1], [0, 1, 0], [1, 1, 2]], compute A^(-1). Also find the value of A^8 - 5A^7 + 7A^6 - 3A^5 + A^4 - 5A^3 + 8A^2 - 2A + I.",
    "Using Cayley-Hamilton theorem, find 1A and 2A if 4 6 6 1 3 2 1 4 3 A     .":
        "Using Cayley-Hamilton theorem, find A^(-1) and A^(-2) if A = [[4, 6, 6], [1, 3, 2], [-1, -4, -3]].",
    "Verify Cayley Hamilton theorem for the Matrix 1 3 2 1 9 1 3 7 0 A    and hence find 1A .":
        "Verify Cayley-Hamilton theorem for the matrix A = [[1, 3, 2], [1, 9, 1], [3, 7, 0]] and hence find A^(-1).",
    "Verify Cayley-Hamilton theorem for 2 1 1 A 0 1 0 1 1 2          and hence find 1A  and 8 7 6 5 4 3 211 4 11 3 2A A A A A A A A I        .":
        "Verify Cayley-Hamilton theorem for A = [[2, 1, 1], [0, 1, 0], [1, 1, 2]] and hence find A^(-1) and A^8 - 5A^7 + 7A^6 - 3A^5 + A^4 - 5A^3 + 8A^2 - 2A + I.",
    "Verify Cayley-hamilton theorem for the matrix 2 1 1 A 0 1 0 1 1 2    and hence find the value of 8 7 6 5 4 3 25 7 3 5 8 2 .A A A A A A A A I       ":
        "Verify Cayley-Hamilton theorem for the matrix A = [[2, 1, 1], [0, 1, 0], [1, 1, 2]] and hence find the value of A^8 - 5A^7 + 7A^6 - 3A^5 + A^4 - 5A^3 + 8A^2 - 2A + I.",
    "Find Eigen values and Eigen vectors of 6 2 2 2 3 1 2 1 3     .":
        "Find Eigenvalues and Eigenvectors of A = [[6, -2, 2], [-2, 3, -1], [2, -1, 3]].",
    "Find Eigen values and Eigen vectors of              121 211":
        "Find Eigenvalues and Eigenvectors of A = [[1, 2, 1], [2, 1, -1], [-1, -1, 2]].",
    "Find the Eigen values and Eigen vectors of the following matrix [  −  −  −  −  ].":
        "Find the Eigenvalues and Eigenvectors of the matrix A = [[8, -6, 2], [-6, 7, -4], [2, -4, 3]].",
    "Find the eigenvalues and the corresponding eigen vectors of              3 1 2 1 3 2 2 2 6 .":
        "Find the eigenvalues and corresponding eigenvectors of A = [[3, 1, 2], [1, 3, 2], [2, 2, 6]].",
    "Find the inverse of            0 1 1 1 0 1 1 1 0 A using Gauss-Jordan method.":
        "Find the inverse of A = [[0, 1, 1], [1, 0, 1], [1, 1, 0]] using Gauss-Jordan method.",
    "Reduce the following matrix 2 1 3 4 0 3 4 1 2 3 7 5 2 3 11 6 A             to the (a) Echelon form, (b) Normal form and hence find its rank.":
        "Reduce the matrix A = [[2, 1, 3, 4], [0, 3, 4, 1], [2, 3, 7, 5], [2, 3, 11, 6]] to (a) Echelon form, (b) Normal form and hence find its rank.",
    "Find rank of matrix               0 8 2 2 0 4 1 1 1 2 1 0 1 2 0 1 A by reducing it into normal form.":
        "Find the rank of matrix A = [[1, 2, 0, 1], [1, 2, 1, 0], [0, 4, 1, 1], [0, 8, 2, 2]] by reducing it into normal form.",
    "Determine the rank of the matrix by reducing it into normal form 1 2 1 4 2 4 3 4 .1 2 3 4 1 2 6 7             ":
        "Determine the rank of matrix A = [[1, 2, -1, 4], [2, 4, 3, 4], [1, 2, 3, 4], [-1, -2, 6, -7]] by reducing it into normal form.",
    "Determine the rank of the matrix              2021136 121384 4532 4320 A by reducing to echelon from.":
        "Determine the rank of matrix A = [[0, 2, 3, 4], [2, 3, 5, 4], [4, 8, 13, 12], [6, 13, 20, 21]] by reducing to echelon form.",

    # Quadratic Forms & Systems
    "Reduce the quadratic form x 2 +y 2 +z 2 − xy− yz +zx into a sum of squares by an orthogonal transformation and also discuss its nature.":
        "Reduce the quadratic form 8x^2 + 7y^2 + 3z^2 - 12xy - 8yz + 4zx into a sum of squares by an orthogonal transformation and also discuss its nature.",
    "Reduce the quadratic form 3  +  + 3 −  −  to the canonical form by orthogonal transformations and find rank, index, signature, nature of the quadratic form.":
        "Reduce the quadratic form 3x^2 + 3y^2 + 3z^2 - 3xy - 3yz to the canonical form by orthogonal transformation and find rank, index, signature and nature.",
    "What is the nature of the quadratic form + 6 − ?":
        "What is the nature of the quadratic form 3xy + 6xz - 5yz?",
    "Write the symmetric matrix in the matrix notation of the quadratic form: ++.":
        "Write the symmetric matrix of the quadratic form 2xy + 2yz + 2zx.",
    "Apply Gauss elimination method to solve the equations + − =−;+ − =−; −  − =.":
        "Apply Gauss elimination method to solve the equations: x + 4y - z = -5; x + y - 6z = -12; 3x - y - z = 4.",
    "Apply Gauss -Jordon method to solve the equations: + − =−,++=, − +=.":
        "Apply Gauss-Jordan method to solve the equations: 2x + 3y - z = -1, x + 4y + 5z = 25, 3x - 4y + z = 2.",
    "Apply Gauss -Siedel method to solve the equations: ++= 9,++=,++=.":
        "Apply Gauss-Seidel method to solve the equations: 2x + y + 6z = 9, 8x + 3y + 2z = 13, x + 5y + z = 7.",
    "Find the maximum and minimum values of 32( −  − ).":
        "Find the maximum and minimum values of x^3 y^2 (1 - x - y).",
    "Find the value of the constant in Cauchy’s mean value theorem for  =  and  =  defined on [a, b], b a 0.":
        "Find the value of constant c in Cauchy's mean value theorem for f(x) = e^x and g(x) = e^(-x) defined on [a, b], where b > a > 0.",
    "If f(x) = log x and g(x) = x 2 in [a, b] with 1  a  b using Cauchy’s mean value theorem, prove or disprove that 2 log log 2 b a a b b a c    for a < c < b.":
        "If f(x) = log(x) and g(x) = x^2 in [a, b] with 1 <= a <= b, using Cauchy's mean value theorem find c where a < c < b.",
    "Using spherical polar coordinates, evaluate ∭   √222 taken over the volume bounded by the sphere  +  +  =  in the first octant.  JNTUH Used papers 2023":
        "Using spherical polar coordinates, evaluate ∭ (xyz / √(x^2 + y^2 + z^2)) dx dy dz taken over the volume bounded by the sphere x^2 + y^2 + z^2 = a^2 in the first octant.",
    "By double integration find the area enclosed by the curves: 2 2 3 4.2 xy and y xx = = +":
        "By double integration, find the area enclosed by the curves y^2 = 4x and x^2 = 4y.",
    "By double integration find the whole area of the curve 2 2 3 (2 ).a x y a y = -":
        "By double integration, find the whole area of the curve a^2 x^2 = y^3 (2a - y).",
    "Calculate the angle between the normal' s to the surface 2xy z = at the points (4, 1, 2) and (3, 3, - 3).":
        "Calculate the angle between the normals to the surface 2xy = z at the points (4, 1, 2) and (3, 3, -3).",
    "The Temperature T at any point (x, y, z) in space is 2400xyz T - . Find the highest temperature at the surface of the unit sphere 12 2 2 - ^-^-z y x.":
        "The temperature T at any point (x, y, z) in space is T = 2400xyz. Find the highest temperature on the surface of the unit sphere x^2 + y^2 + z^2 = 1.",
    "Determine the triple integral 999xyz dxdy dz taken through the positive octant of the sphere 2 2 2 2 + + = x y z a , where a is a constant.":
        "Determine the triple integral ∭ xyz dx dy dz taken through the positive octant of the sphere x^2 + y^2 + z^2 = a^2, where a is a constant.",
    "Expand ^-^( - 1), sinf x y xy < = in powers of ^-^( - 1) 1x - and ^-^( - 1) 2y ∂ - upto second degree terms.":
        "Expand f(x, y) = sin(xy) in powers of (x - 1) and (y - π/2) up to second degree terms.",
    "If u = sin 1^( - 1) 77 8 6 00 1 ( ^-^-y x y x2 2 find the value of x x u ∂ ∂ + y y u ∂ ∂ .":
        "If u = sin^(-1)((x^2 + y^2) / (x + y)), find the value of x ∂u/∂x + y ∂u/∂y.",
    "If u = log + + yx yx 22 prove that x x u ∂ ∂ + y y u ∂ ∂ = 1.":
        "If u = log((x^2 + y^2) / (x + y)), prove that x ∂u/∂x + y ∂u/∂y = 1.",
    "Find volume of the ellipsoid 2 2 2 14 9 16 x y z + + = .":
        "Find the volume of the ellipsoid x^2/4 + y^2/9 + z^2/16 = 1.",
    "Find the volume of the ellipsoid 2 2 2 222 1.x y z aaa + + =":
        "Find the volume of the ellipsoid x^2/a^2 + y^2/b^2 + z^2/c^2 = 1.",
    "Find the volume of the largest rectangular parallelepiped that can be inscri bed in the ellipsoid 2 2 2 2 2 2 1.x y z a b c + + =":
        "Find the volume of the largest rectangular parallelepiped that can be inscribed in the ellipsoid x^2/a^2 + y^2/b^2 + z^2/c^2 = 1.",
    "Find the volume of the largest rectangular parallelepiped that can be inscribed in the ellipsoid 12 2 2 2 2 2 = + + c z b y a x .":
        "Find the volume of the largest rectangular parallelepiped that can be inscribed in the ellipsoid x^2/a^2 + y^2/b^2 + z^2/c^2 = 1.",
    "Find the volume of the largest rectangular parallelepiped that can be inscribed in the ellipsoid 2 2 2 2 2 2 1.x y z a b c + + =":
        "Find the volume of the largest rectangular parallelepiped that can be inscribed in the ellipsoid x^2/a^2 + y^2/b^2 + z^2/c^2 = 1.",
    "Find y uyx ux ∂ ∂ + ∂ ∂ using Euler's theorem for the function + + = - yx yxu 1cos .":
        "Find x ∂u/∂x + y ∂u/∂y using Euler's theorem for the function u = cos^(-1)((x + y) / (√x + √y)).",
    "Find the rank of - - 1211 2312 1121":
        "Find the rank of matrix A = [[1, 2, -1, 1], [2, 3, 1, 2], [1, 1, -2, 1]].",
    "Find the rank of the matrix 0 1 3 1 0 0 1 1 3 1 0 2 1 1 2 0 A - - = - by reducing to echelon form.":
        "Find the rank of the matrix A = [[0, 1, -3, -1], [0, 0, 1, 1], [3, 1, 0, 2], [1, 1, -2, 0]] by reducing to echelon form.",
    "Find the rank of the matrix 2 3 1 1 1 1 2 4A 3 1 3 2 6 3 0 7 - - = - - .":
        "Find the rank of the matrix A = [[2, 3, -1, -1], [1, -1, -2, -4], [3, 1, 3, -2], [6, 3, 0, -7]].",
    "Find rank of matrix - - = 0822 0411 1210 1201 A by reducing it to normal form.":
        "Find the rank of matrix A = [[1, 2, 0, 1], [1, 2, 1, 0], [0, 4, 1, 1], [0, 8, 2, 2]] by reducing it into normal form.",
    "Verify Cayley - Hamilton theorem for the matrix 1 2 1 2 1 2 2 2 1 A - = - - and hence find its inverse. R13":
        "Verify Cayley-Hamilton theorem for the matrix A = [[1, 2, -1], [2, -1, 2], [-2, 2, -1]] and hence find its inverse.",
    "Verify Cayley - Hamilton theorem for the matrix 1 2 1 2 1 2 2 2 1 A - = - - and hence find its inverse. R15":
        "Verify Cayley-Hamilton theorem for the matrix A = [[1, 2, -1], [2, -1, 2], [-2, 2, -1]] and hence find its inverse.",
    "Reduce the matrix 1 1 1 1 1 1 3 1 1 A - - = to normal form and hence find its rank.":
        "Reduce the matrix A = [[1, 1, 1], [1, -1, -1], [3, 1, 1]] to normal form and hence find its rank.",
    "Let 1 0 0 1 0 1 0 1 0 A = , and 12A A A Iα β γ - = + + , ,, Rα β γ ∈ , then find α β γ + + .":
        "Let A = [[1, 0, 0], [1, 0, 1], [0, 1, 0]], and A^(-1) = α A^2 + β A + γ I, α, β, γ ∈ R, find α + β + γ.",
    "Express ∫ 𝑠𝑖𝑛5𝜃 𝑐𝑜𝑠 7 2 𝜋 2 0 𝜃 𝑑𝜃 in terms of Beta and Gamma functions and hence evaluate. R16":
        "Express ∫_0^(π/2) sin^5(θ) cos^(7/2)(θ) dθ in terms of Beta and Gamma functions and hence evaluate.",

    # Probability & Statistics
    "31 0.42 0 0.172 x y z     is Transition probability matrix, then find the values of x, y and z. (50 Marks)":
        "If P = [[0.3, 0.1, x], [0.4, 0.2, y], [0.1, 0.7, z]] is a Transition Probability Matrix, find the values of x, y and z.",
    "Find the transition probability matrix of a Markov chain   3,2,1, nX n having three stages 1, 2 and 3 is           ":
        "Find the transition probability matrix of a Markov chain X_n having three states {1, 2, 3}.",
    "If a random varia ble X follows a Poisson distribution such that )2()1(  XPXP , find the mean.":
        "If a random variable X follows a Poisson distribution such that P(X = 1) = P(X = 2), find the mean.",
    "If a random variable X follows a Poisson distribution such that )2()1(  XPXP , find the mean.":
        "If a random variable X follows a Poisson distribution such that P(X = 1) = P(X = 2), find the mean.",
    "Explain   )/(:1// FCFSMM  queueing model.":
        "Explain (M/M/1) : (∞ / FCFS) queueing model.",
    "If 4, 8, 2, 3and 0.3xyx y r      then find the regression line of y on x.":
        "If x̄ = 4, ȳ = 8, σ_x = 2, σ_y = 3, and r = 0.3, find the regression line of y on x.",
    "The first three moments of a distribution about the value 3 are 2, 10, -30. Find the moments about 0x .":
        "The first three moments of a distribution about the value 3 are 2, 10, -30. Find the moments about x = 0.",
    "The joint p robability functions of X and Y is 33 9 , 0, 0( , ) 0, xy XY e x yf x y otherwise    . Check whether the probability function is a valid density function.":
        "The joint probability density function of X and Y is f_XY(x, y) = 9e^(-3x - 3y) for x >= 0, y >= 0; 0 otherwise. Check whether it is a valid density function.",
    "A continuous Random variable has the p.d.f   6 0 3 0 K x if xfx otherwise     . Determine K.":
        "A continuous random variable has the p.d.f f(x) = K(x + 6) for 0 < x < 3; 0 otherwise. Determine K.",
    "A continuous random variable X has the p.d.f.      otherwise xkxexf x ,0 10,)( Find (a) k (b) E(X) (c) E(2X-3) (d) V(X) and (e) V(4X+3).":
        "A continuous random variable X has p.d.f f(x) = k*x*e^(-x) for 0 < x < 1; 0 otherwise. Find (a) k (b) E(X) (c) E(2X-3) (d) V(X) and (e) V(4X+3).",
    "If X is a continuous random variable whose probability density function is given by ,0 1 ( ) 2 ,1 2 0, elsewhere xx f x x x       Find the moment generating function":
        "If X is a continuous random variable with p.d.f f(x) = x for 0 < x < 1; 2 - x for 1 <= x <= 2; 0 elsewhere, find its moment generating function.",
    "If probability density function   3, 0 3 0, Kx xfx elsewhere    . Find the value of K.":
        "If probability density function is f(x) = K*x^3 for 0 <= x <= 3; 0 elsewhere, find the value of K.",
    "If the moment ge nerating function of a random variable X is 3( ) (1 2 )XM t t  , then find the mean.":
        "If the moment generating function of a random variable X is M_X(t) = (1 - 2t)^(-3), find the mean.",
    "The joint p.d.f of the random variables X and Y is given by 0,0,),( )(   yxeKyxXYf yx . Find":
        "The joint p.d.f of random variables X and Y is given by f_XY(x, y) = K e^{-(x+y)} for x > 0, y > 0. Find K.",
    "The joint probability density function is given by x y,0 1,1 y 5() 5 0, Kxfx elsewhere        . Find the value of K.":
        "The joint probability density function is f(x, y) = K(x + y)/5 for 0 < x < 1, 1 < y < 5; 0 elsewhere. Find K.",
    "The joint probability density function is given by   , 0 1,0 1, 0, x y x yf x y elsewhere       Find:":
        "The joint probability density function is f(x, y) = x + y for 0 < x < 1, 0 < y < 1; 0 elsewhere. Find the marginal distributions.",
    "The joint probability density function is given by   , 0 1,1 55 0, x Ky x yfx elsewhere        . Find:":
        "The joint probability density function is f(x, y) = (x + Ky)/5 for 0 < x < 1, 1 < y < 5; 0 elsewhere. Find K.",
    "Find the maximum error of estimation at 95% confidence interval and the confidence limits for the mean if 82x .":
        "Find the maximum error of estimation at 95% confidence interval and the confidence limits for the mean if x̄ = 82.",

    # DAA Greedy Job Sequencing
    "We have a set of n jobs to execute, each of which takes unit time. At a y time T = 1, 2…., we can execute exactly one jobs. Job i earns us a profit gi  0 if and only if it is executed not later than the time d1. Develop a greedy algorithm to solve the above problem . Run your algorithm for n=4 and the following values:- i 1 2 3 4 gi 50 10 15 30 di 2 2 1 2 7":
        "We have a set of n jobs to execute, each of which takes unit time. At any time T = 1, 2, ..., we can execute exactly one job. Job i earns profit g_i > 0 if and only if it is executed not later than deadline d_i. Develop a greedy algorithm to solve this problem for n=4, g=[50, 10, 15, 30], d=[2, 2, 1, 2]."
}

# 2. General Character Mapping
CHAR_MAP = {
    # PUA sequential digits
    "\ue00e": "0", "\ue00f": "1", "\ue010": "2", "\ue011": "3", "\ue012": "4",
    "\ue013": "5", "\ue014": "6", "\ue015": "7", "\ue016": "8", "\ue017": "9",
    # PUA operators & symbols
    "\ue004": "^(-1)", "\ue005": " + ", "\ue006": " - ", "\ue007": " <= ", "\ue008": " = ",
    "\ue009": "θ", "\ue00a": "λ", "\ue00b": "∂", "\ue00c": "∫", "\ue00d": "(",
    "\ue01a": "V", "\ue01b": "a", "\ue01c": "b", "\ue01d": "e", "\ue01e": "f",
    "\ue01f": "g", "\ue020": "k", "\ue021": "x", "\ue022": "y", "\ue023": "x",
    "\ue024": "y", "\ue025": "z", "\ue028": "^2", "\ue029": "^3", "\ue02a": " + ",
    "\ue02b": " - ", "\ue02c": "d", "\ue02d": ",", "\ue02e": "^(-1)",
    "\ue02f": "x", "\ue030": "y", "\ue031": "z", "\ue032": "e", "\ue033": "-",
    "\ue034": "x", "\ue039": "(", "\ue03a": ")",
    # Symbol font
    "\uf028": "(", "\uf029": ")", "\uf02b": " + ", "\uf02d": " - ",
    "\uf03c": " < ", "\uf03d": " = ", "\uf03e": " > ",
    "\uf044": "Δ", "\uf047": "Γ", "\uf057": "Ω",
    "\uf05b": "[", "\uf05d": "]", "\uf061": "α", "\uf062": "β",
    "\uf066": "φ", "\uf067": "γ", "\uf06c": "λ", "\uf06d": "μ",
    "\uf070": "π", "\uf071": "θ", "\uf073": "σ", "\uf077": "ω",
    "\uf07b": "{", "\uf07d": "}", "\uf0a2": " <= ", "\uf0a3": " <= ",
    "\uf0a5": "∞", "\uf0ae": " -> ", "\uf0af": " <- ", "\uf0b1": " ± ",
    "\uf0b3": " >= ", "\uf0b4": " × ", "\uf0b6": "∂", "\uf0ce": " ∈ ",
    "\uf0d1": "∇", "\uf0f2": "∫",
    "": " = ", "": " - ", "": " > ", "": " < ",
    "": " <= ", "": " >= ", "": " ± ", "": "∫",
    "": "∞", "": "π", "": "θ", "": "λ", "": "μ",
    "": "σ", "": "{", "": "}", "": "Γ", "": "Δ",
    "": "∇", "": "∂", "": "√", "": " <=> ", "": " => ",
    "": " -> ", "": " v ", "": "~", "": "•", "": "∃", "": "∀",
    "": "[", "": "]", "": "|", "": "|", "": "[", "": "]",
    "": "(", "": ")", "": "|", "": "|", "": "(", "": ")",
    "": "{", "": "{", "": "{", "": "}", "": "}", "": "}",
    "…": "...", "‘": "'", "’": "'", "“": '"', "”": '"'
}

for code in range(0xf0e5, 0xf0ff):
    CHAR_MAP[chr(code)] = ""
for code in [0xe018, 0xe019]:
    CHAR_MAP[chr(code)] = ""

def clean_math_string(q: str) -> str:
    # 1. Exact match table
    stripped = q.strip()
    if stripped in EXACT_REPLACEMENTS:
        return EXACT_REPLACEMENTS[stripped]
    
    # Check partial exact matches
    for k, v in EXACT_REPLACEMENTS.items():
        if k in q:
            q = q.replace(k, v)

    # 2. Character mapping
    for k, v in CHAR_MAP.items():
        q = q.replace(k, v)

    # 3. Clean up common regex artifacts
    q = re.sub(r'--ooOoo--|\bOR\b$|- - -', '', q)
    q = re.sub(r'JNTUH Used papers \d{4}', '', q, flags=re.I)
    q = re.sub(r'R\d{2}\s+JNTUH USED PAPERS.*', '', q, flags=re.I)
    
    # 4. Standardize spacing around operators
    q = re.sub(r'\s*\+\s*', ' + ', q)
    q = re.sub(r'\s*=\s*', ' = ', q)
    q = re.sub(r'\s*<=\s*', ' <= ', q)
    q = re.sub(r'\s*>=\s*', ' >= ', q)
    q = re.sub(r'\s*->\s*', ' -> ', q)
    q = re.sub(r'\s*<=>\s*', ' <=> ', q)
    
    # Clean up double minus or spaces in minuses
    q = re.sub(r'\s*-\s*', ' - ', q)
    q = re.sub(r'\s+', ' ', q).strip(' ,;')
    
    # 5. Fix common math symbols
    q = q.replace("^ - ", "^-").replace("^- ", "^-")
    q = q.replace("1A -", "A^(-1)").replace("1 - A", "A^(-1)").replace("A^- 1", "A^(-1)")
    q = q.replace("A1", "A^(-1)")

    return q.strip()

def parse_years(ystr):
    if isinstance(ystr, list):
        return sorted(list(set(int(y) for y in ystr)))
    years = re.findall(r'\b\d{4}\b', str(ystr))
    return sorted(list(set(int(y) for y in years)))

def normalize_text_for_dedup(qtext):
    s = qtext.lower().strip()
    s = re.sub(r'[\s_]+', ' ', s)
    s = s.strip(' ?.:,;')
    return s

def process_file(csv_name: str):
    path = DATASETS_DIR / csv_name
    if not path.exists():
        print(f"File not found: {path}")
        return
    
    with open(path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    
    if not reader:
        return
    
    header = reader[0]
    rows = reader[1:]
    
    modified = 0
    dedup = {}
    
    for r in rows:
        old_q = r[1]
        new_q = clean_math_string(old_q)
        if new_q != old_q:
            modified += 1
        
        subj = r[0]
        topic = r[2]
        bloom = r[3]
        try:
            marks = int(r[4])
        except ValueError:
            marks = 5
        pa = set(parse_years(r[5]))
        pb = set(parse_years(r[6]))
        extra_cols = r[7:]
        
        key = (topic, normalize_text_for_dedup(new_q))
        if key not in dedup:
            dedup[key] = {
                "subj": subj,
                "q": new_q,
                "topic": topic,
                "bloom": bloom,
                "marks": marks,
                "pa": pa,
                "pb": pb,
                "extra": extra_cols
            }
        else:
            dedup[key]["pa"].update(pa)
            dedup[key]["pb"].update(pb)
            dedup[key]["marks"] = max(dedup[key]["marks"], marks)
    
    new_rows = []
    for item in dedup.values():
        marks = item["marks"]
        pa = sorted(list(item["pa"]))
        pb = sorted(list(item["pb"]))
        if marks <= 3 and pb and not pa:
            pa = pb
            pb = []
        elif marks >= 8 and pa and not pb:
            pb = pa
            pa = []
        
        row_out = [
            item["subj"],
            item["q"],
            item["topic"],
            item["bloom"],
            str(marks),
            str(pa),
            str(pb),
            *item["extra"]
        ]
        new_rows.append(row_out)
    
    new_rows.sort(key=lambda x: (x[2], x[1]))
    
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(new_rows)
    
    print(f"[{csv_name:45s}] Polished {modified} questions -> {len(new_rows)} rows after dedup.")

def main():
    target_files = [
        "Matrices_and_Calculus_Dataset.csv",
        "Ordinary_Differential_Equations_and_Vector_Calculus_Dataset.csv",
        "Computer_Oriented_Statistical_Methods_Dataset.csv",
        "Discrete_Mathematics_Dataset.csv",
        "Advanced_Algorithms_R18_Dataset.csv",
    ]
    for fn in target_files:
        process_file(fn)

if __name__ == "__main__":
    main()
