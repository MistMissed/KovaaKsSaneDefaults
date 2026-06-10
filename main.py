from subprocess import run
import shutil
import json
from configparser import UNNAMED_SECTION, ConfigParser
from pathlib import Path
from string import ascii_uppercase


def clear_terminal():
    run("cls", shell=True)


def detect_install_dir():
    # check default directory
    COMMON_LIBRARY = "Program Files (x86)\\Steam\\steamapps\\common\\FPSAimTrainer"
    STEAM_LIBRARY = "SteamLibrary\\steamapps\\common\\FPSAimTrainer"
    KOVAAKS_EXE = "FPSAimTrainer.exe"

    # check drives for steam libraries
    for letter in ascii_uppercase:
        current_drive = Path(letter + ":\\")

        if (current_drive / COMMON_LIBRARY / KOVAAKS_EXE).exists():
            return current_drive / COMMON_LIBRARY

        if (current_drive / STEAM_LIBRARY / KOVAAKS_EXE).exists():
            return current_drive / STEAM_LIBRARY

    # failed to find, manually enter
    install_dir = Path()
    while not (install_dir / KOVAAKS_EXE).exists():
        clear_terminal()
        print(
            (
                ""
                if install_dir != Path()
                else "\nFailed to automatically detect KovaaKs installation"
            ),
            "" if install_dir == Path() else f"folder '{install_dir}' does not exist\n",
            f"You can check by opening Steam > KovaaKs > Properties > Installed Files > Browse",
            "Copy from File Explorer navigation bar",
            f"eg. D:\\Program Files (x86)\\Steam\\steamapps\\common\\FPSAimTrainer",
            sep="\n",
        )
        install_dir = Path(input("Manually enter KovaaKs install folder: "))
    return install_dir


def backup_folders(install_dir: Path):
    """renames pre-existing theme, crosshair, and sound folders"""
    crosshairs_path = install_dir / "FPSAimTrainer\\crosshairs"
    sounds_path = install_dir / "FPSAimTrainer\\sounds"
    themes_path = install_dir / "FPSAimTrainer\\Saved\\SaveGames\\Themes"

    try:
        for folder in (crosshairs_path, sounds_path, themes_path):
            backup_folder = folder.with_suffix(".old")
            shutil.copytree(folder, backup_folder, dirs_exist_ok=True)
            shutil.rmtree(folder)
            folder.mkdir()
    except Exception as e:
        print(e)
        quit("something blew up")


# TODO: error handling
def import_files(install_dir: Path):
    "add crosshairs, sounds, and themes to folders"
    crosshairs_path = install_dir / "FPSAimTrainer\\crosshairs"
    sounds_path = install_dir / "FPSAimTrainer\\sounds"
    themes_path = install_dir / "FPSAimTrainer\\Saved\\SaveGames\\Themes"

    local_crosshairs = Path("crosshairs")
    local_sounds = Path("sounds")
    local_themes = Path("themes")

    for src in local_crosshairs.iterdir():
        dst = crosshairs_path / src.name
        shutil.copy(src, dst)

    for src in local_sounds.iterdir():
        dst = sounds_path / src.name
        shutil.copy(src, dst)

    for src in local_themes.iterdir():
        dst = themes_path / src.name
        shutil.copy(src, dst)


def read_config(config_file: str):
    config = ConfigParser()
    config.read(config_file)
    return config


# TODO: apply_primary_user_settings() incomplete
def apply_primary_user_settings(install_dir: Path, config: ConfigParser):
    primary_user_settings_path = (
        install_dir
        / "FPSAimTrainer"
        / "Saved"
        / "SaveGames"
        / "PrimaryUserSettings.json"
    )
    if not primary_user_settings_path.exists():
        quit("run kovaaks prior to running this script")
    with open(primary_user_settings_path, "r") as f:
        primary_user_settings = json.load(f)

    # type_name = boolean, float, integer, string, vector
    def set_setting(type_name: str, key_name: str, value):
        # stupid setting name format
        # eg. ["integerSettings"] ["EIntegerSettingId::Anisotropy"] = 0
        section_name = f"{type_name}Settings"
        key = f"E{type_name.capitalize()}SettingID::{key_name}"
        primary_user_settings[section_name][key] = value

    # Examples:
    # set_setting("boolean", "balls", "true")
    # set_setting("float", "floatingballs", 1.91)
    # set_setting("integer", "Anisotropy", 0)
    # set_setting("string", "ballstring", "this is ballstring")
    # set_setting("vector", "ballvector", (1, 2, 3))

    # graphics
    set_setting("integer", "Anisotropy", 0)
    set_setting("integer", "AntiAliasing", 0)
    set_setting("integer", "AntiAliasingQuality", 0)
    set_setting("integer", "SceneColorFormat", 3)
    set_setting("integer", "Shadows", 0)
    set_setting("float", "MaxFPS", 999)
    set_setting("float", "MenuMaxFPS", 120)

    # visuals
    set_setting("boolean", "OverrideAllNewMapMaterials", "true")
    set_setting("boolean", "HideGun", "true")
    set_setting("float", "DecalTime", 0)
    set_setting("string", "CurrentThemeName", config["Main"]["visual_theme"])

    # fov
    set_setting("string", "FOVScaleString", "Overwatch")
    set_setting("float", "FOV", config["Main"]["fov"])

    # sens
    set_setting("string", "SensScaleString", "cm/360")
    set_setting("float", "XSens", config["Main"]["sensitivity"])
    set_setting("float", "YSens", config["Main"]["sensitivity"])
    set_setting("integer", "DPI", config["Main"]["dpi"])

    # set_setting("string", "SpawnSound", PLACEHOLDER)

    # write file
    with open(primary_user_settings_path, "w") as f:
        json.dump(primary_user_settings, f)


def create_weapon_settings(path: Path, config: ConfigParser):
    # TODO: use config
    settings = {
        "WeaponHidden": "true",
        "Hitmarkers": "false",
        "HeadHitmarkers": "false",
        "CrosshairColor": "X=0.000 Y=1.000 Z=0.402",
        "CrosshairFile": "lmbSmolPlus.png",
        "BodyHitSound": "wood-tap-click",
        "HeadHitSound": "wood-tap-click",
        "ShootSound": "",
        "HitSoundCooldown": "0.06",
        "CrosshairFile": "lmbSmolPlus.png",
    }

    with open(path, "w") as f:
        for key, value in settings.items():
            f.write(f"{key}={value}\n")

    pass


def apply_weapon_settings(install_dir: Path, config: ConfigParser):
    # TODO: move this outside of the func
    weapon_settings_path = (
        install_dir / "FPSAimTrainer" / "Saved" / "SaveGames" / "weaponsettings.ini"
    )
    weapon_settings = ConfigParser(allow_unnamed_section=True)

    if not weapon_settings_path.exists():
        create_weapon_settings(weapon_settings_path, config)
        return

    weapon_settings.read(weapon_settings_path)




    # TODO: use config
    weapon_settings.set(UNNAMED_SECTION, "WeaponHidden", "true")
    weapon_settings.set(UNNAMED_SECTION, "Hitmarkers", "false")
    weapon_settings.set(UNNAMED_SECTION, "HeadHitmarkers", "false")

    weapon_settings.set(UNNAMED_SECTION, "CrosshairColor", "X=0.000 Y=1.000 Z=0.402")
    weapon_settings.set(UNNAMED_SECTION, "CrosshairFile", "lmbSmolPlus.png")

    # Sound
    weapon_settings.set(UNNAMED_SECTION, "BodyHitSound", "wood-tap-click")
    weapon_settings.set(UNNAMED_SECTION, "HeadHitSound", "wood-tap-click")
    weapon_settings.set(UNNAMED_SECTION, "ShootSound", "")
    weapon_settings.set(UNNAMED_SECTION, "HitSoundCooldown", "0.06")

    weapon_settings.set(UNNAMED_SECTION, "CrosshairFile", "lmbSmolPlus.png")

    with open(weapon_settings_path, "w") as f:
        weapon_settings.write(f, space_around_delimiters=False)


def main():
    config = read_config("config.ini")
    install_dir = detect_install_dir()

    backup_folders(install_dir)
    import_files(install_dir)
    apply_primary_user_settings(install_dir, config)
    apply_weapon_settings(install_dir, config)

    # TODO: find where resolution is stored
    # TODO: make restore backups script


if __name__ == "__main__":
    main()
