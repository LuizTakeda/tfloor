#!/usr/bin/env python3
"""
Script para extrair e gerar GIFs animados a partir das spritesheets do jogo
desenvolvido com o SGDK (Sega Genesis Development Kit).

Uso:
    python3 scripts/generate_gifs.py [--scale 8] [--output-dir gifs]
"""

import argparse
import os
import sys
from PIL import Image

# Configuração das entidades baseadas no resources.res e no código fonte
# Formato:
#   file: nome do arquivo em res/sprites/
#   tile_w, tile_h: tamanho em tiles (1 tile = 8 pixels)
#   sgdk_speed: parâmetro speed do resources.res (número de frames NTSC a 60Hz por frame de animação)
#   representative_row: índice da linha de animação principal/representativa
#   animations: lista de nomes para cada linha de animação
ENTITIES = {
    "player": {
        "file": "player.png",
        "tile_w": 1,
        "tile_h": 2,
        "sgdk_speed": 5,
        "representative_row": 1,
        "animations": [
            "idle_right",
            "run_right",
            "turn_left",
            "idle_left",
            "run_left",
            "turn_right",
            "climb",
        ],
    },
    "slime": {
        "file": "enemy-01.png",
        "tile_w": 1,
        "tile_h": 1,
        "sgdk_speed": 5,
        "representative_row": 1,
        "animations": [
            "spawn",
            "walk_right",
            "walk_left",
            "spawning_right",
            "dying_left",
            "dying_right",
        ],
    },
    "bat": {
        "file": "enemy-02.png",
        "tile_w": 1,
        "tile_h": 1,
        "sgdk_speed": 5,
        "representative_row": 0,
        "animations": [
            "fly_right",
            "fly_left",
            "hit_left",
            "hit_right",
        ],
    },
    "horizontal_shooter": {
        "file": "enemy-03.png",
        "tile_w": 2,
        "tile_h": 1,
        "sgdk_speed": 8,
        "representative_row": 1,
        "animations": [
            "idle_right",
            "shoot_right",
            "aim_right",
            "dying_right",
            "idle_left",
            "shoot_left",
            "aim_left",
            "dying_left",
        ],
    },
    "vertical_shooter": {
        "file": "enemy-04.png",
        "tile_w": 1,
        "tile_h": 2,
        "sgdk_speed": 8,
        "representative_row": 1,
        "animations": [
            "spawn",
            "shoot_up",
            "idle",
            "dying",
        ],
    },
    "teleporter": {
        "file": "enemy-05.png",
        "tile_w": 1,
        "tile_h": 1,
        "sgdk_speed": 7,
        "representative_row": 2,
        "animations": [
            "spawn_appear",
            "idle",
            "charge_teleport",
            "vanish",
            "dying",
        ],
    },
    "jumper": {
        "file": "enemy-06.png",
        "tile_w": 2,
        "tile_h": 1,
        "sgdk_speed": 6,
        "representative_row": 2,
        "animations": [
            "spawn",
            "idle",
            "jump_cycle",
            "landing",
            "dying",
        ],
    },
    "item_life": {
        "file": "item-01.png",
        "tile_w": 1,
        "tile_h": 1,
        "sgdk_speed": 7,
        "representative_row": 1,
        "animations": [
            "spawn",
            "shine_idle",
        ],
    },
    "projectile": {
        "file": "projectile-01.png",
        "tile_w": 1,
        "tile_h": 1,
        "sgdk_speed": 8,
        "representative_row": 0,
        "animations": [
            "moving",
            "impact_vertical",
            "impact_horizontal",
        ],
    },
}


def extract_frames_from_row(img, row_idx, frame_w, frame_h, cols):
    """Extrai os quadros não-vazios de uma linha da spritesheet."""
    frames = []
    for col_idx in range(cols):
        box = (
            col_idx * frame_w,
            row_idx * frame_h,
            (col_idx + 1) * frame_w,
            (row_idx + 1) * frame_h,
        )
        crop = img.crop(box)

        # Checa se o frame tem pixels visíveis (índice diferente de 0)
        pixel_indices = list(crop.getdata())
        has_content = any(idx != 0 for idx in pixel_indices)

        if has_content:
            frames.append(crop)
        else:
            # No SGDK rescomp, os frames de uma linha são contíguos da esquerda para a direita
            break

    return frames


def save_animated_gif(frames, output_path, scale=8, duration_ms=100, transparent=True, bg_color=None):
    """Salva a lista de frames em formato GIF animado com redimensionamento nítido (nearest neighbor)."""
    if not frames:
        return False

    scaled_frames = []
    for f in frames:
        w = f.width * scale
        h = f.height * scale

        if not transparent and bg_color is not None:
            # Converte para RGBA e aplica cor de fundo
            rgba = f.convert("RGBA")
            bg = Image.new("RGBA", (f.width, f.height), bg_color)
            composite = Image.alpha_composite(bg, rgba)
            f_conv = composite.convert("P", palette=Image.Palette.ADAPTIVE)
            scaled = f_conv.resize((w, h), Image.Resampling.NEAREST)
        else:
            # Mantém em modo P com transparência no índice 0
            scaled = f.resize((w, h), Image.Resampling.NEAREST)

        scaled_frames.append(scaled)

    kwargs = {
        "save_all": True,
        "append_images": scaled_frames[1:],
        "duration": duration_ms,
        "loop": 0,
    }

    if transparent:
        kwargs["transparency"] = 0
        kwargs["disposal"] = 2

    scaled_frames[0].save(output_path, **kwargs)
    return True


def main():
    parser = argparse.ArgumentParser(description="Gera GIFs animados a partir das sprites do Mega Drive.")
    parser.add_argument("--scale", type=int, default=8, help="Fator de escala dos pixels (padrão: 8)")
    parser.add_argument("--sprites-dir", default="res/sprites", help="Diretório das sprites de entrada")
    parser.add_argument("--output-dir", default="gifs", help="Diretório de saída para os GIFs")
    parser.add_argument("--no-transparency", action="store_true", help="Desativa transparência e usa fundo sólido")
    parser.add_argument("--bg-color", default="#141419", help="Cor de fundo quando transparência desativada")
    args = parser.parse_args()

    sprites_dir = args.sprites_dir
    output_dir = args.output_dir
    scale = args.scale
    transparent = not args.no_transparency

    if not os.path.isdir(sprites_dir):
        print(f"Erro: diretório de sprites '{sprites_dir}' não encontrado!", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print(" Gerador de GIFs - University T-Floor (SGDK / Sega Mega Drive)")
    print("=" * 70)
    print(f"  Diretório de sprites : {sprites_dir}")
    print(f"  Diretório de saída   : {output_dir}")
    print(f"  Escala de pixel      : {scale}x")
    print(f"  Transparência        : {'Ativada (Fundo transparente)' if transparent else f'Desativada ({args.bg_color})'}")
    print("-" * 70)

    total_gifs = 0

    for entity_name, config in ENTITIES.items():
        sprite_path = os.path.join(sprites_dir, config["file"])
        if not os.path.exists(sprite_path):
            print(f"[!] Aviso: {sprite_path} não encontrado, pulando...")
            continue

        img = Image.open(sprite_path)
        frame_w = config["tile_w"] * 8
        frame_h = config["tile_h"] * 8
        cols = img.width // frame_w
        rows = img.height // frame_h

        # Duração em milissegundos calculada a partir do clock NTSC (60 Hz -> ~16.66ms por frame)
        duration_ms = max(int((config["sgdk_speed"] / 60.0) * 1000), 20)

        entity_out_dir = os.path.join(output_dir, entity_name)
        os.makedirs(entity_out_dir, exist_ok=True)

        print(f"\n▶ Entidade: {entity_name.upper()} ({config['file']})")
        print(f"  Tamanho base: {frame_w}x{frame_h} px -> Saída {frame_w * scale}x{frame_h * scale} px | Speed: {duration_ms}ms/frame")

        rep_frames = None
        rep_duration = duration_ms

        for row_idx, anim_name in enumerate(config["animations"]):
            if row_idx >= rows:
                break

            frames = extract_frames_from_row(img, row_idx, frame_w, frame_h, cols)
            if not frames:
                continue

            gif_name = f"{row_idx:02d}_{anim_name}.gif"
            gif_path = os.path.join(entity_out_dir, gif_name)

            # Para animações de 1 frame único, colocamos duração maior para visualização
            anim_duration = duration_ms if len(frames) > 1 else 500

            save_animated_gif(
                frames,
                gif_path,
                scale=scale,
                duration_ms=anim_duration,
                transparent=transparent,
                bg_color=args.bg_color,
            )
            total_gifs += 1
            print(f"   ✓ [{len(frames):02d} frames] {anim_name:<20} -> {gif_path}")

            if row_idx == config["representative_row"]:
                rep_frames = frames
                rep_duration = anim_duration

        # Salva o GIF principal/representativo da entidade na raiz da pasta de saída
        if rep_frames:
            main_gif_path = os.path.join(output_dir, f"{entity_name}.gif")
            save_animated_gif(
                rep_frames,
                main_gif_path,
                scale=scale,
                duration_ms=rep_duration,
                transparent=transparent,
                bg_color=args.bg_color,
            )
            total_gifs += 1
            print(f"   ★ GIF Principal gerado: {main_gif_path}")

    print("\n" + "=" * 70)
    print(f" Concluído com sucesso! Total de {total_gifs} GIFs gerados em '{output_dir}/'.")
    print("=" * 70)


if __name__ == "__main__":
    main()
