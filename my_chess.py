# === Imports and Initialization ===
import os, sys, pygame, chess, chess.engine
from collections import deque

pygame.init()
WIDTH, HEIGHT, SQUARE_SIZE = 600, 600, 75
WHITE, BROWN = (240, 217, 181), (181, 136, 99)
BUTTON_WIDTH, SIDE_PANEL_WIDTH = 180, 200

# === Load Piece Images ===
PIECE_IMAGES = {}
for p in 'prnbqkPRNBQK':
    color = 'b' if p.islower() else 'w'
    fname = os.path.join("pieces", f"{color}{p.lower()}.png")
    if os.path.exists(fname):
        img = pygame.transform.scale(pygame.image.load(fname), (SQUARE_SIZE, SQUARE_SIZE))
    else:
        img = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
    PIECE_IMAGES[p] = img

# === Engine Setup ===
STOCKFISH_PATH = r"C:\\Code arena\\chess\\stockfish-windows-x86-64-avx2\\stockfish\\stockfish-windows-x86-64-avx2.exe"
engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
board = chess.Board()

# === Pygame Display Setup ===
screen = pygame.display.set_mode((WIDTH + SIDE_PANEL_WIDTH, HEIGHT))
pygame.display.set_caption("Chess")
font, small_font = pygame.font.Font(None, 36), pygame.font.Font(None, 24)

# === Game State ===
game_message = ""
show_knight_path = show_attack_pattern = False
selected_square = selected_for_pattern = knight_start = knight_end = None
knight_path = []

# === UI Buttons ===
button_rects = {
    k: pygame.Rect(WIDTH + 10, 400 + i * 40, BUTTON_WIDTH, 30)
    for i, k in enumerate(["knight_path", "attack_pattern", "minimax_tree", "show_all"])
}

def draw_buttons():
    for k, r in button_rects.items():
        pygame.draw.rect(screen, (100, 100, 100), r)
        pygame.draw.rect(screen, (255, 255, 255), r, 2)
        screen.blit(small_font.render(k.replace("_", " ").title(), True, (255, 255, 255)), (r.x + 10, r.y + 5))

def handle_button_click(pos):
    global show_knight_path, show_attack_pattern, knight_path, knight_start, knight_end, selected_for_pattern
    if button_rects["knight_path"].collidepoint(pos):
        show_knight_path, knight_path, knight_start, knight_end = not show_knight_path, [], None, None
    elif button_rects["attack_pattern"].collidepoint(pos):
        show_attack_pattern, selected_for_pattern = not show_attack_pattern, None
    elif button_rects["minimax_tree"].collidepoint(pos):
        open_minimax_window()
    elif button_rects["show_all"].collidepoint(pos):
        show_knight_path = show_attack_pattern = True

# === Evaluation and Moves ===
def get_evaluation():
    return engine.analyse(board, chess.engine.Limit(time=0.1))["score"].white().score(mate_score=10000)

def draw_eval_bar():
    bar_x, bar_w = WIDTH + 100, 20
    pygame.draw.rect(screen, (0, 0, 0), (bar_x, 0, bar_w, HEIGHT))
    score = max(min(get_evaluation(), 1000), -1000) / 1000
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, 0, bar_w, int((1 - ((score + 1) / 2)) * HEIGHT)))

def get_top_moves(n=5):
    moves, seen = [], set()
    with engine.analysis(board, chess.engine.Limit(time=1.0), multipv=n) as analysis:
        for info in analysis:
            if "pv" in info and "score" in info:
                move = info["pv"][0]
                san = board.san(move)
                if san not in seen:
                    moves.append((san, info["score"].white().score(mate_score=10000)))
                    seen.add(san)
                if len(moves) == n: break
    return moves

def draw_top_moves():
    pygame.draw.rect(screen, (30, 30, 30), (WIDTH, 0, 100, HEIGHT))
    screen.blit(font.render("Moves", True, (255, 255, 255)), (WIDTH + 10, 10))
    for i, (n, s) in enumerate(get_top_moves()):
        y = 50 + 60 * i
        screen.blit(font.render(f"{i+1}. {n}", True, (200, 200, 100)), (WIDTH + 10, y))
        screen.blit(small_font.render(f"Eval: {s}", True, (200, 200, 100)), (WIDTH + 10, y + 25))

# === Visualization Helpers ===
def knight_shortest_path(start, end):
    dirs = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
    queue, visited = deque([[start]]), set()
    while queue:
        path = queue.popleft()
        curr = path[-1]
        if curr == end: return path
        if curr in visited: continue
        visited.add(curr)
        r, c = divmod(curr, 8)
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                next_sq = nr * 8 + nc
                if next_sq not in visited:
                    queue.append(path + [next_sq])
    return []

def draw_graph_path(path, color):
    pts = [(chess.square_file(sq) * SQUARE_SIZE + SQUARE_SIZE // 2, (7 - chess.square_rank(sq)) * SQUARE_SIZE + SQUARE_SIZE // 2) for sq in path]
    for p in pts: pygame.draw.circle(screen, color, p, 6)
    for a, b in zip(pts, pts[1:]): pygame.draw.line(screen, color, a, b, 2)

def draw_attack_pattern(square):
    piece = board.piece_at(square)
    if not piece: return
    sx, sy = chess.square_file(square) * SQUARE_SIZE + SQUARE_SIZE // 2, (7 - chess.square_rank(square)) * SQUARE_SIZE + SQUARE_SIZE // 2
    for t in board.attacks(square):
        x, y = chess.square_file(t) * SQUARE_SIZE + SQUARE_SIZE // 2, (7 - chess.square_rank(t)) * SQUARE_SIZE + SQUARE_SIZE // 2
        pygame.draw.circle(screen, (255, 0, 0), (x, y), 6)
        pygame.draw.line(screen, (255, 0, 0), (sx, sy), (x, y), 2)

# === Drawing Board and Pieces ===
def draw_board():
    for r in range(8):
        for c in range(8):
            sq = chess.square(c, 7 - r)
            rect = pygame.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            color = WHITE if (r + c) % 2 == 0 else BROWN
            pygame.draw.rect(screen, color, rect)
            if selected_square == sq:
                pygame.draw.rect(screen, (0, 255, 0), rect, 3)
            elif selected_square and chess.Move(selected_square, sq) in board.legal_moves:
                pygame.draw.circle(screen, (0, 0, 255), tuple(map(int, rect.center)), 10)
    for i in range(8):
        screen.blit(small_font.render(str(8 - i), True, (0, 0, 0)), (5, i * SQUARE_SIZE + 5))
        screen.blit(small_font.render(chr(97 + i), True, (0, 0, 0)), (i * SQUARE_SIZE + SQUARE_SIZE - 15, HEIGHT - 10))

def draw_pieces():
    for r in range(8):
        for c in range(8):
            sq = chess.square(c, 7 - r)
            p = board.piece_at(sq)
            if p: screen.blit(PIECE_IMAGES[p.symbol()], (c * SQUARE_SIZE, r * SQUARE_SIZE))

# === Game State and Interactions ===
def draw_message():
    if game_message:
        screen.blit(font.render(game_message, True, (255, 255, 255)), (WIDTH // 4, HEIGHT - 300))

def check_game_status():
    global game_message
    if board.is_checkmate(): game_message = "Checkmate! Game Over."
    elif board.is_stalemate(): game_message = "It's a stalemate!"
    elif board.is_insufficient_material(): game_message = "Draw due to insufficient material."
    elif board.is_seventyfive_moves(): game_message = "Draw due to 75-move rule."
    elif board.is_fivefold_repetition(): game_message = "Draw due to fivefold repetition."

def handle_click(pos):
    global selected_square, game_message, knight_path, selected_for_pattern, knight_start, knight_end
    if board.is_game_over(): return
    col, row = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE
    sq = chess.square(col, 7 - row)

    if show_knight_path:
        if knight_start is None and board.piece_at(sq) and board.piece_at(sq).piece_type == chess.KNIGHT and board.piece_at(sq).color == board.turn:
            knight_start = sq
        elif knight_start is not None:
            knight_end = sq
            knight_path = knight_shortest_path(knight_start, knight_end)
            knight_start = None
        return

    if selected_square is None:
        if board.piece_at(sq) and board.piece_at(sq).color == board.turn:
            selected_square = sq
            if show_attack_pattern: selected_for_pattern = sq
    else:
        move = chess.Move(selected_square, sq)
        if board.piece_at(selected_square).piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
            move = chess.Move(selected_square, sq, promotion=chess.QUEEN)
        if move in board.legal_moves:
            board.push(move)
            check_game_status()
            if not board.is_game_over():
                board.push(engine.play(board, chess.engine.Limit(time=0.1)).move)
                check_game_status()
        selected_square = None

# === Misc Features ===
def difficulty_level():
    try: level = int(input("Enter game difficulty level (0 to 20): "))
    except ValueError: level = 10
    engine.configure({"Skill Level": max(0, min(20, level))})

def open_minimax_window():
    pygame.display.set_caption("Minimax Tree")
    tree_screen = pygame.display.set_mode((800, 600))
    tree_screen.fill((30, 30, 30))
    moves, (rx, ry), r = get_top_moves(3), (400, 60), 20
    pygame.draw.circle(tree_screen, (255, 255, 255), (rx, ry), r)
    tree_screen.blit(small_font.render("Root", True, (255, 255, 255)), (rx - 20, ry + 25))
    for i, (m, s) in enumerate(moves):
        x, y = 200 + i * 200, ry + 150
        pygame.draw.line(tree_screen, (255, 255, 255), (rx, ry + r), (x, y - r), 2)
        pygame.draw.circle(tree_screen, (0, 255, 0), (x, y), r)
        tree_screen.blit(small_font.render(m, True, (255, 255, 255)), (x - 30, y + 25))
        tree_screen.blit(small_font.render(f"Eval: {s}", True, (255, 255, 255)), (x - 40, y + 45))
    pygame.display.flip()
    pygame.time.wait(5000)
    pygame.display.set_mode((WIDTH + SIDE_PANEL_WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")

# === Main Game Loop ===
difficulty_level()
running = True
while running:
    draw_board(), draw_pieces(), draw_message(), draw_eval_bar(), draw_top_moves(), draw_buttons()
    if show_knight_path and knight_path: draw_graph_path(knight_path, (0, 255, 255))
    if show_attack_pattern and selected_for_pattern: draw_attack_pattern(selected_for_pattern)
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            (handle_button_click if event.pos[0] >= WIDTH else handle_click)(event.pos)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_u:
            if board.move_stack: board.pop()
            if board.move_stack: board.pop()
engine.quit()
pygame.quit()
