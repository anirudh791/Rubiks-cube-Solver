from flask import Flask, render_template, request, jsonify
import copy
import logging
import uuid

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CUBE SIMULATION LOGIC ---

def validate_cube(cube):
    """Validates the cube state to ensure it has correct format and colors."""
    valid_faces = {'U', 'D', 'F', 'B', 'L', 'R'}
    if not isinstance(cube, dict) or set(cube.keys()) != valid_faces:
        raise ValueError("Cube must have exactly U, D, F, B, L, R faces")
    
    colors = set()
    for face in cube:
        if not isinstance(cube[face], list) or len(cube[face]) != 3:
            raise ValueError(f"Face {face} must be a 3x3 matrix")
        for row in cube[face]:
            if not isinstance(row, list) or len(row) != 3:
                raise ValueError(f"Face {face} rows must contain 3 stickers")
            colors.update(row)
    
    if len(colors) > 6:
        raise ValueError("Cube contains more than 6 distinct colors")
    
    return True

def rotate_face(face):
    """Clockwise 90-degree rotation of a 3x3 face."""
    return [list(row) for row in zip(*face[::-1])]

def apply_move(cube, move):
    """Applies a single move to the cube state."""
    if not move or move[0] not in 'UDFBLR':
        raise ValueError(f"Invalid move: {move}")
    
    face_char = move[0]
    suffix = move[1:] if len(move) > 1 else ''
    if suffix not in ['', "'", '2']:
        raise ValueError(f"Invalid move suffix: {suffix}")
    
    turns = 3 if "'" in suffix else (2 if "2" in suffix else 1)
    cube = copy.deepcopy(cube)
    
    for _ in range(turns):
        cube[face_char] = rotate_face(cube[face_char])
        
        U, D, F, B, L, R = 'U', 'D', 'F', 'B', 'L', 'R'
        
        if face_char == U:
            tmp = cube[F][0][:]
            cube[F][0] = cube[R][0][:]
            cube[R][0] = cube[B][0][:]
            cube[B][0] = cube[L][0][:]
            cube[L][0] = tmp
        elif face_char == D:
            tmp = cube[F][2][:]
            cube[F][2] = cube[L][2][:]
            cube[L][2] = cube[B][2][:]
            cube[B][2] = cube[R][2][:]
            cube[R][2] = tmp
        elif face_char == F:
            tmp = [cube[U][2][i] for i in range(3)]
            for i in range(3):
                cube[U][2][i]   = cube[L][2-i][2]
                cube[L][2-i][2] = cube[D][0][2-i]
                cube[D][0][2-i] = cube[R][i][0]
                cube[R][i][0]   = tmp[i]
        elif face_char == B:
            tmp = [cube[U][0][i] for i in range(3)]
            for i in range(3):
                cube[U][0][i]   = cube[R][i][2]
                cube[R][i][2]   = cube[D][2][2-i]
                cube[D][2][2-i] = cube[L][2-i][0]
                cube[L][2-i][0] = tmp[i]
        elif face_char == L:
            tmp = [cube[U][i][0] for i in range(3)]
            for i in range(3):
                cube[U][i][0]   = cube[B][2-i][2]
                cube[B][2-i][2] = cube[D][i][0]
                cube[D][i][0]   = cube[F][i][0]
                cube[F][i][0]   = tmp[i]
        elif face_char == R:
            tmp = [cube[U][i][2] for i in range(3)]
            for i in range(3):
                cube[U][i][2]   = cube[F][i][2]
                cube[F][i][2]   = cube[D][i][2]
                cube[D][i][2]   = cube[B][2-i][0]
                cube[B][2-i][0] = tmp[i]
    return cube

def is_cube_solved(cube):
    """Checks if the cube is solved."""
    for face in 'UDFBLR':
        center_color = cube[face][1][1]
        for row in cube[face]:
            if any(sticker != center_color for sticker in row):
                return False
    return True

# --- IMPROVED SOLVER LOGIC (LAYER BY LAYER) ---
class CubeSolver:
    def __init__(self, cube):
        self.cube = copy.deepcopy(cube)
        self.solution = []
        self.face_colors = {
            'U': self.cube['U'][1][1],
            'D': self.cube['D'][1][1],
            'F': self.cube['F'][1][1],
            'B': self.cube['B'][1][1],
            'L': self.cube['L'][1][1],
            'R': self.cube['R'][1][1]
        }
        self.max_moves = 200
        self.white_color = self.face_colors['U']
        self.yellow_color = self.face_colors['D']

    def _apply(self, moves):
        """Applies a sequence of moves and logs them."""
        if len(self.solution) >= self.max_moves:
            raise Exception("Maximum moves reached. Cube might be unsolvable.")
        
        for move in moves:
            self.cube = apply_move(self.cube, move)
            self.solution.append(move)
            app.logger.debug(f"Applied move: {move}")

    def solve(self):
        """Executes the full LBL solving sequence."""
        if is_cube_solved(self.cube):
            return []
        
        try:
            validate_cube(self.cube)
            self._solve_white_cross()
            self._solve_white_corners()
            self._solve_second_layer()
            self._solve_yellow_cross()
            self._solve_yellow_face()
            self._solve_final_layer()
            
            return self._optimize_solution()
        except Exception as e:
            app.logger.error(f"Solver error: {e}")
            return ["Solver failed. Please reset and try again."]

    def _optimize_solution(self):
        """Optimizes the solution by removing redundant moves."""
        optimized = []
        i = 0
        n = len(self.solution)
        
        while i < n:
            if i < n - 1 and self.solution[i][0] == self.solution[i+1][0]:
                move1, move2 = self.solution[i], self.solution[i+1]
                turns1 = 1 if "'" not in move1 and "2" not in move1 else (3 if "'" in move1 else 2)
                turns2 = 1 if "'" not in move2 and "2" not in move2 else (3 if "'" in move2 else 2)
                total_turns = (turns1 + turns2) % 4
                
                if total_turns == 0:
                    i += 2
                else:
                    face = move1[0]
                    if total_turns == 1:
                        optimized.append(face)
                    elif total_turns == 2:
                        optimized.append(face + "2")
                    else:
                        optimized.append(face + "'")
                    i += 2
            else:
                optimized.append(self.solution[i])
                i += 1
                
        return optimized

    def _find_edge(self, color1, color2):
        """Finds the position of an edge piece with the given colors."""
        edges = [
            ('U', 0, 1, 'B', 0, 1), ('U', 1, 0, 'L', 0, 1),
            ('U', 1, 2, 'R', 0, 1), ('U', 2, 1, 'F', 0, 1),
            ('F', 1, 0, 'L', 1, 2), ('F', 1, 2, 'R', 1, 0),
            ('F', 2, 1, 'D', 0, 1), ('B', 1, 0, 'R', 1, 2),
            ('B', 1, 2, 'L', 1, 0), ('B', 2, 1, 'D', 2, 1),
            ('D', 1, 0, 'L', 2, 1), ('D', 1, 2, 'R', 2, 1)
        ]
        
        for edge in edges:
            f1, r1, c1, f2, r2, c2 = edge
            if {self.cube[f1][r1][c1], self.cube[f2][r2][c2]} == {color1, color2}:
                return edge
        return None

    def _solve_white_cross(self):
        """Stage 1: Solves the white cross on the U face."""
        for face in ['F', 'R', 'B', 'L']:
            side_color = self.face_colors[face]
            edge = self._find_edge(self.white_color, side_color)
            
            if not edge:
                app.logger.warning(f"Edge with colors {self.white_color}, {side_color} not found")
                continue
                
            f1, r1, c1, f2, r2, c2 = edge
            
            # Skip if edge is already in correct position and oriented
            if ((f1 == 'U' and 
                 ((face == 'F' and r1 == 2 and c1 == 1) or
                  (face == 'R' and r1 == 1 and c1 == 2) or
                  (face == 'B' and r1 == 0 and c1 == 1) or
                  (face == 'L' and r1 == 1 and c1 == 0))) and
                f2 == face):
                continue
            
            # Bring edge to bottom layer
            if f1 != 'D' and f2 != 'D':
                if f1 == 'U':
                    for _ in range(4):
                        if (f1 == 'U' and r1 == 2 and c1 == 1 and f2 == 'F'):
                            break
                        self._apply(['U'])
                        edge = self._find_edge(self.white_color, side_color)
                        if not edge: break
                        f1, r1, c1, f2, r2, c2 = edge
                    
                    if face == 'F':
                        self._apply(['F'])
                    elif face == 'R':
                        self._apply(['R'])
                    elif face == 'B':
                        self._apply(['B'])
                    else:
                        self._apply(['L'])
                else:
                    if f1 == 'F' and r1 == 1 and c1 == 2:
                        self._apply(['R', 'U', 'R\''])
                    elif f1 == 'F' and r1 == 1 and c1 == 0:
                        self._apply(['L\'', 'U\'', 'L'])
                    elif f1 == 'B' and r1 == 1 and c1 == 2:
                        self._apply(['R\'', 'U\'', 'R'])
                    elif f1 == 'B' and r1 == 1 and c1 == 0:
                        self._apply(['L', 'U', 'L\''])
                
                edge = self._find_edge(self.white_color, side_color)
                if not edge: continue
                f1, r1, c1, f2, r2, c2 = edge
            
            # Edge is in bottom layer
            if f1 == 'D' or f2 == 'D':
                for _ in range(4):
                    if f2 == face:
                        break
                    self._apply(['D'])
                    edge = self._find_edge(self.white_color, side_color)
                    if not edge: break
                    f1, r1, c1, f2, r2, c2 = edge
                
                if f1 == 'D':
                    self._apply([face, face])
                else:
                    self._apply([face + "'", 'U\'', face + "'"])

    def _find_corner(self, color1, color2, color3):
        """Finds the position of a corner piece with the given colors."""
        corners = [
            ('U', 0, 0, 'L', 0, 0, 'B', 0, 2), ('U', 0, 2, 'B', 0, 0, 'R', 0, 2),
            ('U', 2, 0, 'F', 0, 0, 'L', 0, 2), ('U', 2, 2, 'R', 0, 0, 'F', 0, 2),
            ('D', 0, 0, 'L', 2, 2, 'F', 2, 0), ('D', 0, 2, 'F', 2, 2, 'R', 2, 0),
            ('D', 2, 0, 'B', 2, 2, 'L', 2, 0), ('D', 2, 2, 'R', 2, 2, 'B', 2, 0)
        ]
        
        for corner in corners:
            f1, r1, c1, f2, r2, c2, f3, r3, c3 = corner
            if {self.cube[f1][r1][c1], self.cube[f2][r2][c2], self.cube[f3][r3][c3]} == {color1, color2, color3}:
                return corner
        return None

    def _solve_white_corners(self):
        """Stage 2: Solves the four white corners."""
        for face in ['F', 'R', 'B', 'L']:
            side_color1 = self.face_colors[face]
            side_color2 = self.face_colors['L' if face == 'F' else 'F' if face == 'R' else 'R' if face == 'B' else 'B']
            
            corner = self._find_corner(self.white_color, side_color1, side_color2)
            
            if not corner:
                app.logger.warning(f"Corner with colors {self.white_color}, {side_color1}, {side_color2} not found")
                continue
                
            f1, r1, c1, f2, r2, c2, f3, r3, c3 = corner
            
            # Bring corner to bottom layer
            if f1 != 'D' and f2 != 'D' and f3 != 'D':
                for _ in range(4):
                    if (f1 == 'U' and r1 == 2 and c1 == 2 and f2 == 'R' and f3 == 'F'):
                        break
                    self._apply(['U'])
                    corner = self._find_corner(self.white_color, side_color1, side_color2)
                    if not corner: break
                    f1, r1, c1, f2, r2, c2, f3, r3, c3 = corner
                
                self._apply(['R', 'D', 'R\'', 'D\''])
                corner = self._find_corner(self.white_color, side_color1, side_color2)
                if not corner: continue
                f1, r1, c1, f2, r2, c2, f3, r3, c3 = corner
            
            # Corner is in bottom layer
            if f1 == 'D' or f2 == 'D' or f3 == 'D':
                for _ in range(4):
                    if (f2 == face and f3 == ('L' if face == 'F' else 'F' if face == 'R' else 'R' if face == 'B' else 'B')):
                        break
                    self._apply(['D'])
                    corner = self._find_corner(self.white_color, side_color1, side_color2)
                    if not edge: break
                    f1, r1, c1, f2, r2, c2, f3, r3, c3 = corner
                
                if f1 == 'D':
                    if face == 'F':
                        self._apply(['F', 'D\'', 'F\''])
                    elif face == 'R':
                        self._apply(['R\'', 'D', 'R'])
                    elif face == 'B':
                        self._apply(['B', 'D2', 'B\'', 'D2'])
                    else:
                        self._apply(['L', 'D\'', 'L\''])
                else:
                    if face == 'F':
                        self._apply(['F\'', 'D\'', 'F'])
                    elif face == 'R':
                        self._apply(['R', 'D', 'R\''])
                    elif face == 'B':
                        self._apply(['B\'', 'D2', 'B'])
                    else:
                        self._apply(['L', 'D\'', 'L\''])

    def _solve_second_layer(self):
        """Stage 3: Solves the four middle layer edges."""
        for _ in range(4):
            edge = None
            for f in ['F', 'R', 'B', 'L']:
                adj_face = 'R' if f == 'F' else 'B' if f == 'R' else 'L' if f == 'B' else 'F'
                e = self._find_edge(self.face_colors[f], self.face_colors[adj_face])
                if e and 'U' not in e[0] and 'D' not in e[0] and 'U' not in e[3] and 'D' not in e[3]:
                    continue
                edge = e
                if edge:
                    break
            
            if not edge:
                continue
                
            f1, r1, c1, f2, r2, c2 = edge
            
            if 'U' not in f1 and 'D' not in f1 and 'U' not in f2 and 'D' not in f2:
                if f1 == 'F' and r1 == 1 and c1 == 2:
                    self._apply(['U', 'R', 'U\'', 'R\'', 'U\'', 'F\'', 'U', 'F'])
                elif f1 == 'F' and r1 == 1 and c1 == 0:
                    self._apply(['U\'', 'L\'', 'U', 'L', 'U', 'F', 'U\'', 'F\''])
                edge = self._find_edge(self.face_colors[f], self.face_colors[adj_face])
                if not edge: continue
                f1, r1, c1, f2, r2, c2 = edge
            
            if 'U' in f1 or 'U' in f2 or 'D' in f1 or 'D' in f2:
                if 'U' in f1 or 'U' in f2:
                    face = f2 if f1 == 'U' else f1
                    for _ in range(4):
                        if self.cube[face][0][1 if face in ['L','R'] else 1] == self.face_colors[face]:
                            break
                        self._apply(['U'])
                        edge = self._find_edge(self.face_colors[f], self.face_colors[adj_face])
                        if not edge: break
                        f1, r1, c1, f2, r2, c2 = edge
                    
                    other_color = self.cube[f1][r1][c1] if f1 != 'U' else self.cube[f2][r2][c2]
                    target_face = [k for k, v in self.face_colors.items() if v == other_color][0]
                    
                    if target_face == 'R':
                        self._apply(['U', 'R', 'U\'', 'R\'', 'U\'', 'F\'', 'U', 'F'])
                    else:
                        self._apply(['U\'', 'L\'', 'U', 'L', 'U', 'F', 'U\'', 'F\''])
                else:
                    for _ in range(4):
                        if (f1 == 'F' and r1 == 2 and c1 == 1):
                            break
                        self._apply(['D'])
                        edge = self._find_edge(self.face_colors[f], self.face_colors[adj_face])
                        if not edge: break
                        f1, r1, c1, f2, r2, c2 = edge
                    self._apply(['F', 'U', 'F\''])

    def _solve_yellow_cross(self):
        """Stage 4: Creates a yellow cross on the D face."""
        edges = [
            self.cube['D'][0][1] == self.yellow_color,
            self.cube['D'][1][0] == self.yellow_color,
            self.cube['D'][1][2] == self.yellow_color,
            self.cube['D'][2][1] == self.yellow_color
        ]
        count = sum(edges)
        
        if count == 4:
            return
        
        if count == 0:
            self._apply(['F', 'R', 'U', 'R\'', 'U\'', 'F\''])
            edges = [
                self.cube['D'][0][1] == self.yellow_color,
                self.cube['D'][1][0] == self.yellow_color,
                self.cube['D'][1][2] == self.yellow_color,
                self.cube['D'][2][1] == self.yellow_color
            ]
            count = sum(edges)
        
        if count == 2:
            if edges[0] and edges[2]:
                self._apply(['D'])
            elif not (edges[1] and edges[3]):
                for _ in range(4):
                    if (edges[1] and edges[2]):
                        break
                    self._apply(['D'])
                    edges = [
                        self.cube['D'][0][1] == self.yellow_color,
                        self.cube['D'][1][0] == self.yellow_color,
                        self.cube['D'][1][2] == self.yellow_color,
                        self.cube['D'][2][1] == self.yellow_color
                    ]
            
            self._apply(['F', 'U', 'R', 'U\'', 'R\'', 'F\''])

    def _solve_yellow_face(self):
        """Stage 5: Solves the entire yellow face."""
        for _ in range(4):
            corners = [
                self.cube['D'][0][0] == self.yellow_color,
                self.cube['D'][0][2] == self.yellow_color,
                self.cube['D'][2][0] == self.yellow_color,
                self.cube['D'][2][2] == self.yellow_color
            ]
            
            if all(corners):
                return
            
            for _ in range(4):
                if self.cube['D'][2][2] == self.yellow_color:
                    break
                self._apply(['D'])
            
            self._apply(['R', 'U', 'R\'', 'U', 'R', 'U2', 'R\''])

    def _solve_final_layer(self):
        """Stage 6: Solves the final layer by positioning edges and corners."""
        self._position_final_corners()
        self._position_final_edges()

    def _position_final_corners(self):
        """Positions the final layer corners correctly."""
        alg = ['R\'', 'F', 'R\'', 'B2', 'R', 'F\'', 'R\'', 'B2', 'R2']
        
        for _ in range(4):
            solved = True
            for i in range(4):
                face = ['F', 'R', 'B', 'L'][i]
                next_face = ['R', 'B', 'L', 'F'][i]
                corner_colors = {
                    self.cube['U'][2 if face in ['F','R'] else 0][2 if face in ['R','B'] else 0],
                    self.cube[face][0][2 if face in ['F','B'] else 0],
                    self.cube[next_face][0][0 if next_face in ['F','B'] else 2]
                }
                expected_colors = {self.face_colors['U'], self.face_colors[face], self.face_colors[next_face]}
                if corner_colors != expected_colors:
                    solved = False
                    break
            
            if solved:
                return
            
            self._apply(alg)
            self._apply(['U'])

    def _position_final_edges(self):
        """Positions the final layer edges correctly."""
        alg = ['R2', 'U', 'R', 'U', 'R\'', 'U\'', 'R\'', 'U\'', 'R\'', 'U', 'R\'']
        
        for _ in range(4):
            solved = True
            for face in ['F', 'R', 'B', 'L']:
                if self.cube[face][0][1] != self.face_colors[face]:
                    solved = False
                    break
            
            if solved:
                return
            
            self._apply(alg)
            self._apply(['U'])

# --- FLASK ENDPOINTS ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve_route():
    data = request.get_json()
    if not data or 'cube' not in data:
        return jsonify({'error': 'Invalid request, no cube data provided.'}), 400
    
    cube_state = data['cube']
    app.logger.info("Received cube state for solving.")
    
    try:
        validate_cube(cube_state)
        if is_cube_solved(cube_state):
            return jsonify({'solution': [], 'sequence': "Cube is already solved!"})
        
        solver = CubeSolver(cube_state)
        solution_moves = solver.solve()
        
        sequence = ' '.join(solution_moves) if solution_moves else "Cube is already solved!"
        return jsonify({'solution': solution_moves, 'sequence': sequence})
    except Exception as e:
        app.logger.error(f"Solver error: {e}", exc_info=True)
        return jsonify({'error': f"An error occurred: {str(e)}"}), 400

if __name__ == '__main__':
    app.run(debug=True)