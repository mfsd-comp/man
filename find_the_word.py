import argparse
import random
import sys

import pygame


WIDTH, HEIGHT = 1000, 600

# Colors
WHITE = (245, 248, 255)
BLACK = (20, 24, 30)
MINT = (73, 214, 173)
RED = (225, 80, 95)
GOLD = (252, 201, 76)
BLUE = (86, 152, 255)

WORD_BANK = [
    {"clue": "I automate tasks between apps. Who am I?", "answer": "n8n", "category": "Automation"},
    {"clue": "Version control platform for team collaboration.", "answer": "github", "category": "Dev Tools"},
    {"clue": "Language known for indentation and readability.", "answer": "python", "category": "Programming"},
    {"clue": "JavaScript runtime used on servers.", "answer": "node", "category": "Backend"},
    {"clue": "A containerization platform with whale logo.", "answer": "docker", "category": "Cloud"},
]


class GameState:
    def __init__(self):
        random.shuffle(WORD_BANK)
        self.input_text = ""
        self.message = "Type the answer and press Enter!"
        self.message_color = BLUE
        self.message_timer = 0
        self.current_idx = 0
        self.score = 0
        self.streak = 0
        self.lives = 3
        self.max_time = 20.0
        self.round_time = self.max_time
        self.game_over = False
        self.hint_used = False
        self.bubbles = [
            [random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(12, 40), random.uniform(0.4, 1.4)]
            for _ in range(30)
        ]
        self.confetti = []

    def start_round(self):
        self.round_time = self.max_time
        self.hint_used = False
        self.input_text = ""

    def current_entry(self):
        return WORD_BANK[self.current_idx % len(WORD_BANK)]

    def set_message(self, text, color, duration=2.2):
        self.message = text
        self.message_color = color
        self.message_timer = duration

    def reveal_hint(self, answer):
        visible = max(1, len(answer) // 3)
        indexes = set(random.sample(range(len(answer)), visible))
        return "".join(ch if i in indexes else "_" for i, ch in enumerate(answer))

    def spawn_confetti(self):
        for _ in range(55):
            self.confetti.append(
                {
                    "x": WIDTH // 2 + random.randint(-100, 100),
                    "y": HEIGHT // 2,
                    "vx": random.uniform(-4.0, 4.0),
                    "vy": random.uniform(-7.0, -1.0),
                    "life": random.randint(35, 75),
                    "color": random.choice([MINT, GOLD, BLUE, RED, WHITE]),
                    "size": random.randint(3, 7),
                }
            )

    def submit_answer(self):
        if self.game_over:
            return

        answer = self.current_entry()["answer"]
        if self.input_text.strip().lower() == answer:
            bonus = 10 + min(10, self.streak * 2)
            time_bonus = int(self.round_time)
            self.score += bonus + time_bonus
            self.streak += 1
            self.current_idx += 1
            self.spawn_confetti()
            self.set_message(f"Perfect! +{bonus + time_bonus} points", MINT)
            self.start_round()
            return

        self.lives -= 1
        self.streak = 0
        self.input_text = ""
        self.set_message("Oops! Wrong answer.", RED)
        if self.lives <= 0:
            self.game_over = True
            self.set_message("Game Over! Press R to restart.", RED, duration=999)

    def use_hint(self):
        if self.game_over or self.hint_used:
            return

        answer = self.current_entry()["answer"]
        hint = self.reveal_hint(answer)
        self.score = max(0, self.score - 5)
        self.hint_used = True
        self.set_message(f"Hint: {hint}  (-5 points)", GOLD, duration=3)

    def restart_game(self):
        random.shuffle(WORD_BANK)
        self.current_idx = 0
        self.score = 0
        self.streak = 0
        self.lives = 3
        self.game_over = False
        self.set_message("New game started. Let's go!", BLUE)
        self.start_round()


def draw_background(screen, bubbles, ticks):
    for y in range(HEIGHT):
        wave = int(20 * pygame.math.Vector2(1, 0).rotate((y + ticks * 0.02) % 360).x)
        color = (30 + y // 8 + wave // 6, 45 + y // 7, 72 + y // 6)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

    for bubble in bubbles:
        bubble[1] -= bubble[3]
        if bubble[1] < -bubble[2]:
            bubble[0] = random.randint(0, WIDTH)
            bubble[1] = HEIGHT + bubble[2]
        pygame.draw.circle(screen, (255, 255, 255, 40), (int(bubble[0]), int(bubble[1])), bubble[2], width=1)


def draw_ui(screen, state, fonts, caret_on):
    title_font, font, small_font, tiny_font = fonts
    entry = state.current_entry()

    pygame.draw.rect(screen, (10, 14, 20), (40, 28, WIDTH - 80, HEIGHT - 56), border_radius=18)
    pygame.draw.rect(screen, (74, 134, 238), (40, 28, WIDTH - 80, HEIGHT - 56), 2, border_radius=18)

    title = title_font.render("Find the Word • Pro Edition", True, WHITE)
    screen.blit(title, (62, 44))

    pygame.draw.rect(screen, (20, 27, 39), (62, 130, WIDTH - 124, 130), border_radius=12)
    clue_text = font.render(f"Clue: {entry['clue']}", True, WHITE)
    category_text = small_font.render(f"Category: {entry['category']}", True, (179, 209, 255))
    screen.blit(clue_text, (82, 162))
    screen.blit(category_text, (82, 208))

    input_rect = pygame.Rect(62, 286, WIDTH - 124, 62)
    pygame.draw.rect(screen, (7, 10, 15), input_rect, border_radius=10)
    pygame.draw.rect(screen, BLUE, input_rect, 2, border_radius=10)
    display_text = state.input_text + ("|" if caret_on and not state.game_over else "")
    typed = font.render(display_text, True, WHITE)
    screen.blit(typed, (82, 300))

    bar_bg = pygame.Rect(62, 370, WIDTH - 124, 18)
    pygame.draw.rect(screen, (40, 45, 56), bar_bg, border_radius=9)
    ratio = max(0, state.round_time / state.max_time)
    fill_w = int((WIDTH - 124) * ratio)
    bar_color = MINT if ratio > 0.5 else GOLD if ratio > 0.2 else RED
    pygame.draw.rect(screen, bar_color, (62, 370, fill_w, 18), border_radius=9)

    stats = small_font.render(
        f"Score: {state.score}    Streak: {state.streak}    Lives: {state.lives}    Round: {state.current_idx + 1}",
        True,
        WHITE,
    )
    screen.blit(stats, (62, 404))

    msg = small_font.render(state.message, True, state.message_color)
    screen.blit(msg, (62, 446))

    controls = tiny_font.render("Enter: Submit    Tab: Hint (-5)    Esc: Clear    R: Restart", True, (189, 201, 226))
    screen.blit(controls, (62, HEIGHT - 54))

    if state.game_over:
        overlay = pygame.Surface((WIDTH - 124, 150), pygame.SRCALPHA)
        overlay.fill((8, 11, 18, 220))
        screen.blit(overlay, (62, 220))
        go_title = font.render("Game Over", True, RED)
        go_score = small_font.render(f"Final Score: {state.score}", True, WHITE)
        go_hint = small_font.render("Press R to play again.", True, (179, 209, 255))
        screen.blit(go_title, (WIDTH // 2 - go_title.get_width() // 2, 246))
        screen.blit(go_score, (WIDTH // 2 - go_score.get_width() // 2, 293))
        screen.blit(go_hint, (WIDTH // 2 - go_hint.get_width() // 2, 326))


def update_confetti(screen, confetti):
    alive = []
    for piece in confetti:
        piece["x"] += piece["vx"]
        piece["y"] += piece["vy"]
        piece["vy"] += 0.24
        piece["life"] -= 1
        if piece["life"] > 0:
            alive.append(piece)
            pygame.draw.circle(screen, piece["color"], (int(piece["x"]), int(piece["y"])), piece["size"])
    confetti[:] = alive


def parse_args():
    parser = argparse.ArgumentParser(description="Find the Word: Pro Edition")
    parser.add_argument(
        "--auto-exit-seconds",
        type=float,
        default=0,
        help="Automatically close after N seconds (useful for quick execution checks).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Find the Word: Pro Edition")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", 54, bold=True)
    font = pygame.font.SysFont("arial", 34)
    small_font = pygame.font.SysFont("arial", 24)
    tiny_font = pygame.font.SysFont("arial", 18)
    fonts = (title_font, font, small_font, tiny_font)

    state = GameState()
    state.start_round()

    elapsed = 0.0
    while True:
        dt = clock.tick(60) / 1000
        elapsed += dt
        ticks = pygame.time.get_ticks()
        caret_on = (ticks // 450) % 2 == 0

        if args.auto_exit_seconds > 0 and elapsed >= args.auto_exit_seconds:
            pygame.quit()
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    state.submit_answer()
                elif event.key == pygame.K_TAB:
                    state.use_hint()
                elif event.key == pygame.K_ESCAPE:
                    state.input_text = ""
                elif event.key == pygame.K_r:
                    state.restart_game()
                elif event.key == pygame.K_BACKSPACE:
                    state.input_text = state.input_text[:-1]
                elif not state.game_over and event.unicode.isprintable() and len(state.input_text) < 24:
                    state.input_text += event.unicode

        if not state.game_over:
            state.round_time -= dt
            if state.round_time <= 0:
                state.round_time = 0
                state.input_text = ""
                state.set_message("Time's up! Life lost.", RED)
                state.lives -= 1
                state.streak = 0
                if state.lives <= 0:
                    state.game_over = True
                    state.set_message("Game Over! Press R to restart.", RED, duration=999)
                else:
                    state.start_round()

        if state.message_timer > 0 and state.message_timer != 999:
            state.message_timer -= dt
            if state.message_timer <= 0:
                state.set_message("Keep going!", (194, 219, 255), duration=0)

        draw_background(screen, state.bubbles, ticks)
        draw_ui(screen, state, fonts, caret_on)
        update_confetti(screen, state.confetti)
        pygame.display.flip()


if __name__ == "__main__":
    main()
