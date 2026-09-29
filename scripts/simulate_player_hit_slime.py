#!/usr/bin/env python3
"""
Simulador em Python da mecânica do jogo T-Floor:
Player correndo e atingindo o Slime, com cálculo de colisão,
knockback, animação de morte e atualização de HUD.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def load_frames(sprite_path, tile_w, tile_h):
    img = Image.open(sprite_path)
    fw = tile_w * 8
    fh = tile_h * 8
    cols = img.width // fw
    rows = img.height // fh
    animations = []
    for r in range(rows):
        row_frames = []
        for c in range(cols):
            box = (c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)
            crop = img.crop(box)
            if any(p != 0 for p in crop.getdata()):
                row_frames.append(crop)
            else:
                break
        animations.append(row_frames)
    return img, animations

def main():
    bg = Image.open("res/backgrounds/cenario.png").convert("RGBA")
    _, player_anims = load_frames("res/sprites/player.png", 1, 2)
    _, slime_anims = load_frames("res/sprites/enemy-01.png", 1, 1)

    # Animações:
    # Player: row 1 = running right, row 4 = running left
    # Slime: row 1 = walk right, row 2 = walk left, row 4 = dying left, row 5 = dying right

    frames = []

    # Configuração da simulação no 1º andar (FN_ONE: y=160 para player, y=168 para slime)
    player_x = 100.0
    player_y = 160.0
    player_vx = 1.2

    slime_x = 200.0
    slime_y = 168.0
    slime_vx = -0.75
    slime_state = "WALK_LEFT"
    slime_dead = False
    slime_dying_frame = 0

    kills = 0
    total_steps = 70

    for step in range(total_steps):
        canvas = bg.copy()
        draw = ImageDraw.Draw(canvas)

        # Atualiza física
        if not slime_dead:
            slime_x += slime_vx
            # Checa colisão (did_player_hit_enemy)
            # Player correndo para direita atinge slime pela esquerda
            player_right = player_x + 7
            slime_hit_left = slime_x + 1
            slime_hit_right = slime_x + 6

            if player_right >= slime_hit_left and player_x <= slime_hit_right:
                # HIT!
                slime_state = "DYING"
                slime_vx = 2.0  # knockback para direita
                slime_vy = -0.75
                kills = 1

        if slime_state == "DYING":
            slime_x += slime_vx
            slime_y += slime_vy
            slime_dying_frame += 0.25
            if slime_dying_frame >= len(slime_anims[5]):
                slime_dead = True

        player_x += player_vx

        # HUD Textual no padrão do jogo
        draw.text((8, 48), "KILLS", fill=(255, 255, 255))
        draw.text((8, 56), f" {kills:2d}/ 15", fill=(255, 255, 255))
        draw.text((248, 48), "LIFE 3", fill=(255, 255, 255))
        draw.text((248, 168), "LEVEL 1", fill=(255, 255, 255))

        # Renderiza Slime se vivo ou morrendo
        if not slime_dead:
            if slime_state == "WALK_LEFT":
                s_frame_idx = int((step // 5) % len(slime_anims[2]))
                s_img = slime_anims[2][s_frame_idx].convert("RGBA")
            else:
                s_frame_idx = min(int(slime_dying_frame), len(slime_anims[5]) - 1)
                s_img = slime_anims[5][s_frame_idx].convert("RGBA")

            canvas.paste(s_img, (int(slime_x), int(slime_y)), s_img)

        # Renderiza Player
        p_frame_idx = int((step // 5) % len(player_anims[1]))
        p_img = player_anims[1][p_frame_idx].convert("RGBA")
        canvas.paste(p_img, (int(player_x), int(player_y)), p_img)

        # Escala 2x para 640x448 nítido
        scaled = canvas.resize((640, 448), Image.Resampling.NEAREST)
        frames.append(scaled.convert("P", palette=Image.Palette.ADAPTIVE))

    out_path = "gifs/simulated_player_hit_slime.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=40,
        loop=0,
    )
    print(f"GIF simulado gerado com sucesso: {out_path} ({len(frames)} frames)")

if __name__ == "__main__":
    main()
