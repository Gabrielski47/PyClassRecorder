import pyautogui
import keyboard

print('Posicione o mouse sobre o link desejado e aperte ENTER para registrar.')
print('Aperte S para printar "Scroll" e rolar a tela.')
print('Aperte B para sair.\n')

posicoes = []
contador = 1

try:
    while True:
        if keyboard.is_pressed('b'):
            print('\nTecla B pressionada. Encerrando...')
            break

        if keyboard.is_pressed('enter'):

            x, y = pyautogui.position()
            posicoes.append(((x, y), 1800))
            print(f'{contador} - ({x}, {y})')
            contador += 1

            while keyboard.is_pressed('enter'):
                pass

        if keyboard.is_pressed('s'):
            print('Scroll')
            pyautogui.scroll(-500)  # Scrolla para baixo (positivo sobe, negativo desce)
            while keyboard.is_pressed('s'):
                pass

except KeyboardInterrupt:
    print('\nEncerrado pelo teclado.')
