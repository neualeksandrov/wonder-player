import os
import sys
import random
import pygame
import argparse
import time
import termios
import tty
import fcntl

# Версия плеера
VERSION = "1.5"
PLAYLIST_FILE = "saved_playlist.txt"

def find_audio_files(folder):
    """Рекурсивный поиск аудиофайлов (WAV, FLAC) в указанной папке"""
    audio_files = []
    supported_formats = ('.wav', '.flac')
    
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(supported_formats):
                full_path = os.path.join(root, file)
                audio_files.append(full_path)
    return audio_files

def save_playlist(playlist, filename=PLAYLIST_FILE):
    """Сохранение плейлиста в файл"""
    try:
        with open(filename, 'w') as f:
            for track in playlist:
                f.write(track + "\n")
        print(f"Плейлист сохранен в файл: {filename} ({len(playlist)} треков)")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении плейлиста: {str(e)}")
        return False

def load_playlist(filename=PLAYLIST_FILE):
    """Загрузка плейлиста из файла"""
    try:
        if not os.path.exists(filename):
            print(f"Файл плейлиста не найден: {filename}")
            return []
            
        with open(filename, 'r') as f:
            playlist = [line.strip() for line in f.readlines()]
        
        # Фильтрация несуществующих файлов
        valid_playlist = []
        for track in playlist:
            if os.path.exists(track):
                valid_playlist.append(track)
            else:
                print(f"Файл недоступен: {track}")
        
        print(f"Загружен плейлист из {filename} ({len(valid_playlist)} треков)")
        return valid_playlist
    except Exception as e:
        print(f"Ошибка при загрузке плейлиста: {str(e)}")
        return []

def setup_non_blocking_input():
    """Настройка неблокирующего ввода с клавиатуры"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
    return fd, old_settings

def restore_input_settings(fd, old_settings):
    """Восстановление настроек терминала"""
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

class PlayerInterface:
    """Класс для управления интерфейсом плеера"""
    def __init__(self, initial_track="", index=0, playlist_length=0):
        self.bindings = {}
        self.available_keys = [
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'
        ]
        self.commands = {
            'pause_toggle': "пауза/продолжение",
            'next_track': "следующий трек",
            'prev_track': "предыдущий трек",
            'quit': "выход",
            'delete': "удалить текущий трек"
        }
        self.last_remap_time = time.time()
        self.next_remap_interval = random.uniform(5, 10)
        self.delete_mode = False
        self.paused = False
        self.current_index = index
        self.playlist_length = playlist_length
        self.set_current_track(initial_track)
        self.remap_keys()
    
    def remap_keys(self):
        """Случайное переназначение клавиш"""
        # Выбираем случайные клавиши для каждой команды
        keys = random.sample(self.available_keys, len(self.commands))
        self.bindings = dict(zip(self.commands.keys(), keys))
        
        # Обновляем время следующего переназначения
        self.last_remap_time = time.time()
        self.next_remap_interval = random.uniform(5, 10)
        
        # Выводим новую справку
        self.print_help()

    def set_paused(self, paused):
        self.paused = paused
        self.print_help()

    def set_current_track(self, track):
        """Обновление текущего трека"""
        if track:
            self.current_track_filename = track
            self.current_track = f"Воспроизведение ({self.current_index+1}/{self.playlist_length}): {track}"
        else:
            self.current_track_filename = track
            self.current_track = "Трек неизвестен"
    
    def update_track_info(self, index, playlist_length):
        """Обновление информации о позиции трека и длине плейлиста"""
        self.current_index = index
        self.playlist_length = playlist_length
    
    def print_help(self):
        """Вывод справки по текущим назначениям клавиш"""
        os.system('cls' if os.name == 'nt' else 'clear')
        if self.delete_mode:
            print(f"\n=== РЕЖИМ УДАЛЕНИЯ ===")
            print(f"{self.current_track}")
            print("ЛЮБАЯ КНОПКА УДАЛИТ ТЕКУЩИЙ ТРЕК!")
        else:
            print(f"\n{self.current_track}")
            print("Назначения клавиш:")
            for command, key in self.bindings.items():
                print(f"  {key.upper()} - {self.commands[command]}")
            # print(f"Следующее переназначение через: {self.next_remap_interval:.1f} сек")
        if self.paused:
            print("⏸  Пауза")
    
    def should_remap(self):
        """Проверка, нужно ли выполнять переназначение"""
        return time.time() - self.last_remap_time >= self.next_remap_interval
    
    def get_key(self, command):
        """Получение клавиши для команды"""
        return self.bindings.get(command, None)
    
    def handle_key(self, key):
        """Обработка нажатия клавиши"""
        if self.delete_mode:
            return 'delete'  # В режиме удаления все клавиши работают как удаление
        
        if key == self.bindings['pause_toggle']:
            return 'pause_toggle'
        elif key == self.bindings['next_track']:
            return 'next_track'
        elif key == self.bindings['prev_track']:
            return 'prev_track'
        elif key == self.bindings['quit']:
            return 'quit'
        elif key == self.bindings['delete']:
            return 'delete'
        return None
    
    def enter_delete_mode(self):
        """Активация режима удаления"""
        self.delete_mode = True
        print(f"\n{self.current_track}")
        print("=== РЕЖИМ УДАЛЕНИЯ АКТИВИРОВАН ===")
        print("ЛЮБАЯ КНОПКА УДАЛИТ ТЕКУЩИЙ ТРЕК!")
    
    def exit_delete_mode(self):
        """Выход из режима удаления"""
        self.delete_mode = False
        print("\n=== РЕЖИМ УДАЛЕНИЯ ДЕАКТИВИРОВАН ===")

def play_music(playlist):
    """Воспроизведение плейлиста с возможностью управления"""
    if not playlist:
        print("Ошибка: Плейлист пуст!")
        return
    
    pygame.mixer.init()
    current_index = 0
    backward = 0
    paused = False
    
    # Настройка неблокирующего ввода
    fd, old_settings = setup_non_blocking_input()

    history = {}

    # Инициализация интерфейса плеера с первым треком
    player_interface = PlayerInterface(
        initial_track=playlist[current_index] if playlist else "",
        index=current_index,
        playlist_length=len(playlist)
    )

    while not player_interface.should_remap():
        time.sleep(0.1)

    random.shuffle(playlist)
    player_interface.remap_keys()

    # Функция для воспроизведения трека
    def play_track(index):
        nonlocal current_index
        nonlocal backward
        
        if index < 0 or index >= len(playlist):
            return False

        if (index < current_index):
            backward += 1
            track = list(history.keys()).pop(-1 - backward)
            history[track] = False
        else:
            backward = 0
            track = playlist[index]

        if history.get(track, False):
            random.shuffle(playlist)
            return play_track(index)
                
        try:
            if not os.path.exists(track):
                print(f"Файл не найден: {track}")
                return False
                
            pygame.mixer.music.load(track)
            pygame.mixer.music.play()
            current_index = index
            
            # Обновляем информацию о треке в интерфейсе
            player_interface.update_track_info(current_index, len(playlist))
            player_interface.set_current_track(track)

            history[track] = True
            return True

        except pygame.error as e:
            print(f"Ошибка при чтении файла {track}: {str(e)}")
            return False
    
    # Запускаем первый трек
    if not play_track(0):
        restore_input_settings(fd, old_settings)
        return
        
    # Основной цикл воспроизведения
    try:
        while True:
            # Проверка ввода с клавиатуры
            try:
                key = sys.stdin.read(1).lower()
                if key:
                    command = player_interface.handle_key(key)
                    
                    # Режим удаления
                    if command == 'delete' and player_interface.delete_mode:
                        # Удаление текущего файла
                        #current_track = playlist[current_index]
                        current_track = player_interface.current_track_filename
                        try:
                            # Останавливаем воспроизведение
                            pygame.mixer.music.stop()
                            
                            # Удаляем файл
                            os.remove(current_track)
                            print(f"\n>>> ФАЙЛ УДАЛЕН: {current_track}")
                            
                            # Удаляем трек из плейлиста
                            playlist.pop(playlist.index(current_track))
                            
                            # Сохраняем обновленный плейлист
                            save_playlist(playlist)
                            print("Плейлист сохранен!")
                            
                            # Если плейлист пуст, выходим
                            if not playlist:
                                print("Плейлист пуст. Выход.")
                                break
                                
                            # Корректируем индекс
                            if current_index >= len(playlist):
                                current_index = len(playlist) - 1
                            
                            # Выходим из режима удаления
                            player_interface.exit_delete_mode()
                            
                            # Воспроизводим следующий трек
                            if not play_track(current_index):
                                break
                            
                        except Exception as e:
                            print(f"Ошибка при удалении файла: {str(e)}")
                            player_interface.exit_delete_mode()
                    
                    # Обычные команды
                    elif command == 'pause_toggle':
                        if paused:
                            pygame.mixer.music.unpause()
                            paused = False
                            player_interface.set_paused(paused) 
                            #print("▶ Продолжение воспроизведения")
                        else:
                            pygame.mixer.music.pause()
                            paused = True
                            player_interface.set_paused(paused)
                    
                    elif command == 'next_track':
                        if play_track(current_index + 1):
                            paused = False
                            player_interface.set_paused(paused)

                    elif command == 'prev_track':
                        if current_index > 0 and play_track(current_index - 1):
                            paused = False
                            player_interface.set_paused(paused)
                    
                    elif command == 'quit':
                        pygame.mixer.music.stop()
                        print("\nВыход из программы")
                        break
                    
                    elif command == 'delete':
                        # Активируем режим удаления
                        player_interface.enter_delete_mode()
            
            except IOError:
                pass  # Нет ввода

            # Проверка завершения трека
            if not paused and not pygame.mixer.music.get_busy():
                next_index = current_index + 1
                if next_index < len(playlist):
                    if play_track(next_index):
                        paused = False
                        player_interface.set_paused(paused)
                else:
                    print("\nКонец плейлиста!")
                    break

            # Проверка необходимости переназначения клавиш
            if player_interface.should_remap():
                random.shuffle(playlist)
                player_interface.remap_keys()

            time.sleep(0.1)

    except KeyboardInterrupt:
        pygame.mixer.music.stop()
        print("\nВоспроизведение прервано")
    finally:
        restore_input_settings(fd, old_settings)
        pygame.mixer.quit()

def main():
    parser = argparse.ArgumentParser(
        description=f'Аудиоплеер с перемешиванием и случайным переназначением клавиш (версия {VERSION})',
        epilog='Пример: python player.py /путь/к/музыкальной/папке'
    )
    parser.add_argument('folder', type=str, help='Папка с аудиофайлами')
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    
    args = parser.parse_args()

    # Вывод информации о версии
    print(f"\n===  Wonder player (версия {VERSION}) ===")
    
    # Сначала пытаемся загрузить сохраненный плейлист
    playlist = load_playlist()
    
    # Если не удалось загрузить плейлист, создаем новый из указанной папки
    if not playlist:
        if not os.path.isdir(args.folder):
            print(f"Ошибка: '{args.folder}' не является папкой или не существует")
            return
            
        print(f"Поиск аудиофайлов (WAV, FLAC) в: {args.folder}...")
        playlist = find_audio_files(args.folder)
        
        if not playlist:
            print("Аудиофайлы не найдены!")
            print("Убедитесь, что в папке есть файлы с расширениями .wav или .flac")
            return
            
        print(f"Найдено треков: {len(playlist)}")
        
        # Сохраняем новый плейлист
        save_playlist(playlist)
    
    # Воспроизведение плейлиста
    print("Треков в плейлисте:", len(playlist))
    play_music(playlist)

if __name__ == "__main__":
    main()
