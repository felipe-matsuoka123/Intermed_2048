import streamlit as st
from PIL import Image
import random, os, base64, copy
from io import BytesIO

# ----------------------------
# Page configuration
# ----------------------------
st.set_page_config(page_title="Intermed 2048", page_icon="🐍", layout="wide")
# --- Centered Title & Caption ---
st.markdown("<h1 style='text-align: center;'>🐍 Intermed <del>2048</del> 2025</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic;'>Combine as faculdades para chegar no campeão geral da intermed 2025</p>", unsafe_allow_html=True)

# ----------------------------
# Load and normalize logos
# ----------------------------
LOGO_DIR = "logos"
LOGO_SIZE = (128, 128)

@st.cache_data
def load_images(logo_dir):
    """Loads, resizes, and base64-encodes all images from the logo directory."""
    if not os.path.exists(logo_dir):
        st.error(f"Logo folder '{logo_dir}' not found. Please create it and add your college logos.")
        return None

    logos = [
        os.path.join(logo_dir, f)
        for f in os.listdir(logo_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if not logos:
        st.error("No logos found in the logos folder. Add .png or .jpg images.")
        return None

    # --- FIX: Sort numerically (1, 2, 10) instead of alphabetically (1, 10, 2) ---
    try:
        logos.sort(key=lambda path: int(os.path.splitext(os.path.basename(path))[0]))
    except ValueError:
        st.error("Error: Logo filenames must be numbers (e.g., '1.jpg', '2.png').")
        st.warning("Sorting alphabetically as a fallback: 1.jpg, 10.jpg, 2.jpg...")
        logos.sort() # Fallback to alphabetical if filenames aren't numbers
    # --- End of Fix ---

    def image_to_base64(img):
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    try:
        images = [Image.open(path).resize(LOGO_SIZE) for path in logos]
        return [image_to_base64(img) for img in images]
    except Exception as e:
        st.error(f"Error loading images: {e}")
        return None

images_b64 = load_images(LOGO_DIR)

# --- NEW: Load the 'Win' Image ---
@st.cache_data
def load_win_image():
    """Loads, resizes, and base64-encodes the win image."""
    for ext in ['.png', '.jpg', '.jpeg', '.gif']:
        path = f"win_image{ext}"
        if os.path.exists(path):
            try:
                # Resize to fit nicely in the overlay
                img = Image.open(path).resize((400, 400), Image.LANCZOS)
                buf = BytesIO()
                img.save(buf, format="PNG") # Always save as PNG for base64
                return base64.b64encode(buf.getvalue()).decode("utf-8")
            except Exception as e:
                st.error(f"Error loading win image: {e}")
                return None
    
    # If no file was found
    st.warning("Optional 'win_image.[png/jpg/gif]' not found. Win message will be text-only.")
    return None

# Load it globally
win_image_b64 = load_win_image()
# --- End of New Section ---


if not images_b64:
    st.stop()

# Define the highest possible tile index (the "win" condition)
WIN_INDEX = len(images_b64) - 1

# ----------------------------
# Helper functions
# ----------------------------
def add_new_tile(grid):
    """Adds a new '0' tile to a random empty spot in the grid."""
    empties = [(i, j) for i in range(4) for j in range(4) if grid[i][j] is None]
    if empties:
        i, j = random.choice(empties)
        grid[i][j] = 0
    return grid

def check_game_over(grid):
    """Returns True if no moves are possible, False otherwise."""
    for i in range(4):
        for j in range(4):
            # Check for empty spots
            if grid[i][j] is None:
                return False
            # Check for horizontal merges
            if j < 3 and grid[i][j] == grid[i][j+1]:
                return False
            # Check for vertical merges
            if i < 3 and grid[i][j] == grid[i+1][j]:
                return False
    return True

# ----------------------------
# Initialize session state
# ----------------------------
def init_game():
    """Sets up a new game in session_state."""
    grid = [[None for _ in range(4)] for _ in range(4)]
    grid = add_new_tile(grid)
    grid = add_new_tile(grid) # Start with two tiles
    st.session_state.grid = grid
    st.session_state.game_over = False
    st.session_state.game_won = False

if "grid" not in st.session_state:
    init_game()

# ----------------------------
# Merge & move logic
# ----------------------------
def merge_row(row):
    """Merges tiles in a single row (left). Returns new row and score."""
    new_row = [val for val in row if val is not None]
    merged_row = []
    skip = False
    
    for i in range(len(new_row)):
        if skip:
            skip = False
            continue
        
        if i + 1 < len(new_row) and new_row[i] == new_row[i + 1]:
            merged_val = min(new_row[i] + 1, WIN_INDEX)
            merged_row.append(merged_val)
            skip = True
            if merged_val == WIN_INDEX:
                st.session_state.game_won = True
        else:
            merged_row.append(new_row[i])
            
    while len(merged_row) < 4:
        merged_row.append(None)
    return merged_row

def calculate_move(grid, direction):
    """Takes the current grid and a direction, returns the new grid after move."""
    new_grid = copy.deepcopy(grid)
    if direction == "left":
        for i in range(4):
            new_grid[i] = merge_row(new_grid[i])
    elif direction == "right":
        for i in range(4):
            reversed_row = new_grid[i][::-1]
            new_grid[i] = merge_row(reversed_row)[::-1]
    elif direction == "up":
        transposed = list(map(list, zip(*new_grid)))
        for i in range(4):
            transposed[i] = merge_row(transposed[i])
        new_grid = list(map(list, zip(*transposed)))
    elif direction == "down":
        transposed = list(map(list, zip(*new_grid)))
        for i in range(4):
            reversed_col = transposed[i][::-1]
            transposed[i] = merge_row(reversed_col)[::-1]
        new_grid = list(map(list, zip(*transposed)))
    return new_grid

# ----------------------------
# Main game loop
# ----------------------------

# "New Game" button
if st.button("Novo Jogo"):
    init_game()
    st.rerun()

# ----------------------------
# Grid rendering (CSS & HTML)
# ----------------------------
TILE_SIZE = 140
GAP_SIZE = 12
PADDING_SIZE = 12
BG_COLOR = "#d6d6d6" # Light gray for empty tiles

# --- CSS FIX: Correct container width calculation ---
GRID_WIDTH = (TILE_SIZE * 4) + (GAP_SIZE * 3) + (PADDING_SIZE * 2)

st.markdown(f"""
<style>
/* --- FIX: Wrapper to force centering --- */
.center-div {{
    display: flex;
    justify-content: center;
}}

/* --- NEW: Force Light Theme --- */
body {{
    background-color: #FFFFFF !important; /* Force white background */
    color: #000000 !important; /* Force black text */
}}
/* Target the main app container */
.stApp {{
    background-color: #FFFFFF !important;
}}
/* Ensure all text is dark */
h1, h2, h3, h4, h5, h6, p, .stCaption {{
    color: #000000 !important;
}}

/* --- NEW: Style Streamlit Buttons for Light Theme --- */
.stButton > button {{
    background-color: #f0f2f6 !important; /* Light gray background for buttons */
    color: #000000 !important; /* Black text for buttons */
    border: 1px solid #ced4da !important; /* Light border */
    border-radius: 0.5rem;
}}

.stButton > button:hover {{
    background-color: #e2e6ea !important; /* Slightly darker on hover */
    border-color: #dae0e5 !important;
}}

.stButton > button:active {{
    background-color: #d3d9df !important; /* Even darker when pressed */
    border-color: #cad1d8 !important;
}}
/* --- End of Button Styling --- */

.grid-container {{
    position: relative;
    width: {GRID_WIDTH}px; /* 4 tiles + 3 gaps + 2 padding */
    /* margin: auto; <-- Replaced by center-div */
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    justify-items: center;
    align-items: center;
    gap: {GAP_SIZE}px;
    border-radius: 12px;
    padding: {PADDING_SIZE}px;
    background-color: #bbada0; /* Classic 2048 grid background */
}}
.tile {{
    width: {TILE_SIZE}px;
    height: {TILE_SIZE}px;
    background-color: {BG_COLOR};
    border-radius: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative; /* To position the number */
}}
.tile img {{
    width: {LOGO_SIZE[0]}px;
    height: {LOGO_SIZE[1]}px;
    border-radius: 8px;
    animation: pop 0.2s ease-out;
}}
/* --- REMOVED: Style for the number on the tile --- */

/* --- NEW: Animation Keyframes --- */
@keyframes pop {{
    0% {{
        transform: scale(0.7);
        opacity: 0.5;
    }}
    100% {{
        transform: scale(1);
        opacity: 1;
    }}
}}
/* --- End of New Section --- */

.game-overlay {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    /* --- UPDATED: More opaque white background --- */
    background-color: rgba(255, 255, 255, 0.9); 
    display: flex;
    flex-direction: column; /* To stack image and text */
    justify-content: center;
    align-items: center;
    border-radius: 12px;
    z-index: 10;
    text-align: center;
    /* --- UPDATED: Ensure text is black --- */
    color: #000000 !important; 
}}
.game-overlay h1, .game-overlay h2 {{
    color: #000000 !important;
}}
</style>
""", unsafe_allow_html=True)

# Build the HTML for the grid
html_grid = "<div class='grid'>"
for row in st.session_state.grid:
    for val in row:
        if val is not None:
            # --- MODIFIED: Removed the tile-number div ---
            html_grid += f"<div class='tile'><img src='data:image/png;base64,{images_b64[val]}'></div>"
        else:
            html_grid += "<div class='tile'></div>" # Empty tile
html_grid += "</div>"

# --- UPDATED: Display game state messages *over* the grid ---
game_message = ""
if st.session_state.game_won:
    st.balloons()
    
    if win_image_b64:
        # If 'win_image.png' exists, show it
        game_message = f"<div class='game-overlay'><img src='data:image/png;base64,{win_image_b64}' width='400' height='400' style='border-radius: 12px;'><h1 style='margin-top: 10px;'>🐍 Campeão! 🐍</h1></div>"
    else:
        # Fallback if no win image is found
        game_message = "<div class='game-overlay'><h1>🎓<br/>Campeão!</h1></div>"

elif st.session_state.game_over:
    game_message = "<div class='game-overlay'><h2>Game Over!</h2>Pressione 'New Game' para tentar novamente.</div>"

# Combine grid and overlay
st.markdown(f"<div class='center-div'><div class='grid-container'>{game_message}{html_grid}</div></div>", unsafe_allow_html=True)

# --- On-Screen Button Controls ---
direction = None
st.write("") # Spacer

# Layout for buttons
top_cols = st.columns([1, 1, 1]) # 3 columns for layout
with top_cols[1]: # Center column for Up
    if st.button("Cima ⬆", use_container_width=True, key="up_btn"):
        direction = "up"

mid_cols = st.columns([1, 1, 1]) # New row
with mid_cols[0]: # Left column
    if st.button("Esquerda ⬅", use_container_width=True, key="left_btn"):
        direction = "left"
with mid_cols[1]: # Center column for Down
    if st.button("Baixo ⬇", use_container_width=True, key="down_btn"):
        direction = "down"
with mid_cols[2]: # Right column
    if st.button("Direita ➡", use_container_width=True, key="right_btn"):
        direction = "right"
# --- End of Button Controls ---


# Process the move only if the game is not over AND a button was pressed
if direction and not st.session_state.game_over and not st.session_state.game_won:
    grid_before = copy.deepcopy(st.session_state.grid)
    grid_after = calculate_move(grid_before, direction)
    
    grid_changed = (grid_after != grid_before)
    
    if grid_changed:
        st.session_state.grid = add_new_tile(grid_after)
        if check_game_over(st.session_state.grid):
            st.session_state.game_over = True
    else:
        if check_game_over(st.session_state.grid):
            st.session_state.game_over = True

    st.rerun() 

elif check_game_over(st.session_state.grid) and not st.session_state.game_won:
    st.session_state.game_over = True

st.markdown("<br><br>", unsafe_allow_html=True) # Add some space
st.markdown("<p style='text-align: center; color: #888;'>Feito por Felipe Matsuoka (Pavio)</p>", unsafe_allow_html=True)